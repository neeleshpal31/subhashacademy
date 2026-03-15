import os
import sqlite3
from werkzeug.security import generate_password_hash


def _get_db_path():
    return os.getenv("SQLITE_DB_PATH", "college.db")


db = sqlite3.connect(_get_db_path(), check_same_thread=False)
cursor = db.cursor()

cursor.execute(
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

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS gallery_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        filename TEXT NOT NULL,
        category TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cursor.execute("PRAGMA table_info(gallery_images)")
gallery_columns = [row[1] for row in cursor.fetchall()]

if "category" not in gallery_columns:
    cursor.execute("ALTER TABLE gallery_images ADD COLUMN category TEXT")

cursor.execute(
    """
    UPDATE gallery_images
    SET category = 'campus_infrastructure'
    WHERE category IS NULL OR TRIM(category) = ''
    """
)

cursor.execute("SELECT COUNT(*) FROM admin")
admin_count = cursor.fetchone()[0]

if admin_count == 0:
    cursor.execute(
        "INSERT INTO admin (username, password) VALUES (?, ?)",
        ("admin", generate_password_hash("admin123")),
    )


cursor.execute("SELECT id, password FROM admin")
admin_rows = cursor.fetchall()

for admin_id, stored_password in admin_rows:
    # Migrate any legacy plaintext passwords to hashed values.
    if "$" not in stored_password:
        cursor.execute(
            "UPDATE admin SET password=? WHERE id=?",
            (generate_password_hash(stored_password), admin_id),
        )

db.commit()

print("SQLite Database Connected Successfully")