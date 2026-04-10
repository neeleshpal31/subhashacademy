import os
import time

import psycopg2
from werkzeug.security import generate_password_hash


class CursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        adapted_query = query.replace("?", "%s")
        if params is None:
            self._cursor.execute(adapted_query)
        else:
            self._cursor.execute(adapted_query, params)
        return self

    def executemany(self, query, param_list):
        self._cursor.executemany(query.replace("?", "%s"), param_list)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        return self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


def _get_database_url():
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _connect():
    database_url = _get_database_url()
    connect_kwargs = {"connect_timeout": 5}

    if database_url:
        connect_kwargs["dsn"] = database_url
        sslmode = os.getenv("POSTGRES_SSLMODE")
        if sslmode:
            connect_kwargs["sslmode"] = sslmode
        elif "localhost" not in database_url and "127.0.0.1" not in database_url:
            connect_kwargs["sslmode"] = "require"
    else:
        if os.getenv("RENDER") == "true":
            raise RuntimeError(
                "DATABASE_URL or POSTGRES_* env vars are missing on Render. "
                "Attach the PostgreSQL database to the web service and redeploy."
            )

        connect_kwargs.update(
            {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "dbname": os.getenv("POSTGRES_DB", "college"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "sslmode": os.getenv("POSTGRES_SSLMODE", "prefer"),
            }
        )

    last_error = None
    for attempt in range(3):
        try:
            return psycopg2.connect(**connect_kwargs)
        except psycopg2.OperationalError as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2)

    raise last_error


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

_raw_cursor.execute(
    """
    ALTER TABLE gallery_images
    ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'campus_infrastructure'
    """
)

_raw_cursor.execute(
    """
    ALTER TABLE gallery_images
    ADD COLUMN IF NOT EXISTS image_data BYTEA
    """
)

_raw_cursor.execute(
    """
    ALTER TABLE gallery_images
    ADD COLUMN IF NOT EXISTS mime_type TEXT
    """
)

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


cursor = CursorAdapter(db.cursor())

print("PostgreSQL Database Connected Successfully")