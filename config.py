import os
import psycopg2

from werkzeug.security import generate_password_hash


def _get_database_url():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for PostgreSQL connection.")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _connect():
    connect_kwargs = {"connect_timeout": 15}
    sslmode = os.getenv("PGSSLMODE", "").strip()
    if sslmode:
        connect_kwargs["sslmode"] = sslmode
    connection = psycopg2.connect(_get_database_url(), **connect_kwargs)
    return connection


def _ensure_column(raw_cursor, table_name, column_name, column_sql):
    raw_cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    if raw_cursor.fetchone() is None:
        raw_cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


db = _connect()
_raw_cursor = db.cursor()

_raw_cursor.execute(
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

_raw_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """
)

_raw_cursor.execute(
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

_ensure_column(_raw_cursor, "gallery_images", "category", "category TEXT DEFAULT 'campus_infrastructure'")
_ensure_column(_raw_cursor, "gallery_images", "image_data", "image_data BYTEA")
_ensure_column(_raw_cursor, "gallery_images", "mime_type", "mime_type TEXT")

_raw_cursor.execute(
    """
    UPDATE gallery_images
    SET category = 'campus_infrastructure'
    WHERE category IS NULL OR TRIM(category) = ''
    """
)

_raw_cursor.execute("SELECT COUNT(*) FROM admin")
admin_count = _raw_cursor.fetchone()[0]

if admin_count == 0:
    _raw_cursor.execute(
        "INSERT INTO admin (username, password) VALUES (%s, %s)",
        ("admin", generate_password_hash("admin123")),
    )

_raw_cursor.execute("SELECT id, password FROM admin")
admin_rows = _raw_cursor.fetchall()

for admin_id, stored_password in admin_rows:
    if "$" not in stored_password:
        _raw_cursor.execute(
            "UPDATE admin SET password=%s WHERE id=%s",
            (generate_password_hash(stored_password), admin_id),
        )

db.commit()
cursor = db.cursor()

print("PostgreSQL Database Connected Successfully")