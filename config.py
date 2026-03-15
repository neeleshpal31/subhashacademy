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


# Initialize database with default data if empty on Render
def _initialize_default_data():
    cursor.execute("SELECT COUNT(*) FROM admissions;")
    admission_count = cursor.fetchone()[0]
    
    if admission_count == 0:
        # Check if database initialization file exists
        init_script_path = os.path.join(os.path.dirname(__file__), "database_init.sql")
        if os.path.exists(init_script_path):
            with open(init_script_path, 'r') as f:
                sql_lines = f.readlines()
                sql_statement = ""
                for line in sql_lines:
                    line = line.strip()
                    if line and not line.startswith("--"):
                        sql_statement += line
                        if line.endswith(";"):
                            try:
                                cursor.execute(sql_statement)
                                sql_statement = ""
                            except Exception as e:
                                print(f"Error executing SQL: {e}")
                                sql_statement = ""
            db.commit()
        else:
            # If init file doesn't exist, create sample data
            cursor.execute(
                "INSERT INTO admissions (name, email, phone, course, message) VALUES (?, ?, ?, ?, ?)",
                ('Sample Student', 'sample@example.com', '9999999999', 'BCA', 'Sample admission entry'),
            )
            cursor.execute(
                "INSERT INTO gallery_images (title, description, filename, category) VALUES (?, ?, ?, ?)",
                ('Campus', 'College Campus', 'campus.jpg', 'campus_infrastructure'),
            )
            db.commit()

_initialize_default_data()

print("SQLite Database Connected Successfully")