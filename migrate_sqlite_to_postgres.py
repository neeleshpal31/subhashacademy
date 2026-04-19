import os
import sqlite3
from typing import Dict

import psycopg2


def get_database_url() -> str:
    database_url = os.getenv("SUPABASE_DB_URL", "").strip()
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("SUPABASE_DB_URL (or DATABASE_URL) is required. Set Supabase PostgreSQL connection string first.")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def detect_sslmode(database_url: str) -> str:
    lowered = database_url.lower()
    if "supabase.co" in lowered or "pooler.supabase.com" in lowered:
        return "require"
    return ""


def get_sqlite_path() -> str:
    source_path = os.getenv("SQLITE_SOURCE_PATH", "college.db").strip()
    if not source_path:
        source_path = "college.db"
    if not os.path.isabs(source_path):
        source_path = os.path.join(os.path.dirname(__file__), source_path)
    return source_path


def table_exists_sqlite(cur: sqlite3.Cursor, table_name: str) -> bool:
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    )
    return cur.fetchone() is not None


def ensure_postgres_schema(pg_cur) -> None:
    pg_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admissions (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            course TEXT NOT NULL,
            message TEXT
        )
        """
    )

    pg_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """
    )

    pg_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS gallery_images (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            filename TEXT NOT NULL,
            category TEXT DEFAULT 'campus_infrastructure',
            image_data BYTEA,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    pg_cur.execute(
        """
        UPDATE gallery_images
        SET category = 'campus_infrastructure'
        WHERE category IS NULL OR TRIM(category) = ''
        """
    )


def truncate_if_requested(pg_cur) -> None:
    should_truncate = os.getenv("MIGRATION_TRUNCATE", "0").strip() == "1"
    if should_truncate:
        pg_cur.execute("TRUNCATE TABLE gallery_images, admissions, admin RESTART IDENTITY CASCADE")


def migrate_admissions(sql_cur: sqlite3.Cursor, pg_cur) -> int:
    if not table_exists_sqlite(sql_cur, "admissions"):
        return 0

    sql_cur.execute("SELECT id, name, email, phone, course, message FROM admissions ORDER BY id")
    rows = sql_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO admissions (id, name, email, phone, course, message)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                course = EXCLUDED.course,
                message = EXCLUDED.message
            """,
            row,
        )
    return len(rows)


def migrate_admin(sql_cur: sqlite3.Cursor, pg_cur) -> int:
    if not table_exists_sqlite(sql_cur, "admin"):
        return 0

    sql_cur.execute("SELECT id, username, password FROM admin ORDER BY id")
    rows = sql_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO admin (id, username, password)
            VALUES (%s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                username = EXCLUDED.username,
                password = EXCLUDED.password
            """,
            row,
        )
    return len(rows)


def migrate_gallery_images(sql_cur: sqlite3.Cursor, pg_cur) -> int:
    if not table_exists_sqlite(sql_cur, "gallery_images"):
        return 0

    sql_cur.execute(
        """
        SELECT
            id,
            title,
            description,
            filename,
            category,
            image_data,
            mime_type,
            created_at
        FROM gallery_images
        ORDER BY id
        """
    )
    rows = sql_cur.fetchall()

    for row in rows:
        image_data = row[5]
        if isinstance(image_data, memoryview):
            image_data = image_data.tobytes()

        pg_cur.execute(
            """
            INSERT INTO gallery_images
            (id, title, description, filename, category, image_data, mime_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                filename = EXCLUDED.filename,
                category = EXCLUDED.category,
                image_data = EXCLUDED.image_data,
                mime_type = EXCLUDED.mime_type,
                created_at = EXCLUDED.created_at
            """,
            (row[0], row[1], row[2], row[3], row[4], image_data, row[6], row[7]),
        )

    return len(rows)


def reset_sequences(pg_cur) -> None:
    pg_cur.execute(
        "SELECT setval(pg_get_serial_sequence('admissions', 'id'), COALESCE((SELECT MAX(id) FROM admissions), 1), true)"
    )
    pg_cur.execute(
        "SELECT setval(pg_get_serial_sequence('admin', 'id'), COALESCE((SELECT MAX(id) FROM admin), 1), true)"
    )
    pg_cur.execute(
        "SELECT setval(pg_get_serial_sequence('gallery_images', 'id'), COALESCE((SELECT MAX(id) FROM gallery_images), 1), true)"
    )


def main() -> None:
    sqlite_path = get_sqlite_path()
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite source database not found: {sqlite_path}")

    database_url = get_database_url()
    connect_kwargs: Dict[str, object] = {"connect_timeout": 15}
    sslmode = os.getenv("PGSSLMODE", "").strip() or detect_sslmode(database_url)
    if sslmode:
        connect_kwargs["sslmode"] = sslmode

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(database_url, **connect_kwargs)
    pg_cur = pg_conn.cursor()

    try:
        ensure_postgres_schema(pg_cur)
        truncate_if_requested(pg_cur)

        migrated_counts = {
            "admissions": migrate_admissions(sqlite_cur, pg_cur),
            "admin": migrate_admin(sqlite_cur, pg_cur),
            "gallery_images": migrate_gallery_images(sqlite_cur, pg_cur),
        }

        reset_sequences(pg_cur)
        pg_conn.commit()

        print("Migration completed successfully.")
        for table, count in migrated_counts.items():
            print(f"  {table}: {count} row(s) migrated")
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
