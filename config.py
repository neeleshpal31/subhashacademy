import os
import sqlite3

from werkzeug.security import generate_password_hash


def _get_db_path():
    default_path = os.path.join(os.path.dirname(__file__), "college.db")
    return os.getenv("SQLITE_DB_PATH", default_path)


def _connect():
    db_path = _get_db_path()
    connection = sqlite3.connect(db_path, check_same_thread=False)
    return connection


def _ensure_column(raw_cursor, table_name, column_name, column_sql):
    raw_cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in raw_cursor.fetchall()}
    if column_name not in existing_columns:
        raw_cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


db = _connect()
_raw_cursor = db.cursor()

_raw_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """
)

_raw_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS gallery_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        filename TEXT NOT NULL,
        category TEXT DEFAULT 'campus_infrastructure',
        image_data BLOB,
        mime_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)

_ensure_column(_raw_cursor, "gallery_images", "category", "category TEXT DEFAULT 'campus_infrastructure'")
_ensure_column(_raw_cursor, "gallery_images", "image_data", "image_data BLOB")
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
        "INSERT INTO admin (username, password) VALUES (?, ?)",
        ("admin", generate_password_hash("admin123")),
    )

_raw_cursor.execute("SELECT id, password FROM admin")
admin_rows = _raw_cursor.fetchall()

for admin_id, stored_password in admin_rows:
    if "$" not in stored_password:
        _raw_cursor.execute(
            "UPDATE admin SET password=? WHERE id=?",
            (generate_password_hash(stored_password), admin_id),
        )

db.commit()
cursor = db.cursor()

print("SQLite Database Connected Successfully")