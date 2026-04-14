from config import db

cursor = db.cursor()

print("Exporting database to SQL...")

# Get all tables except sqlite_sequence
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall()]

sql_commands = []

for table in tables:
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
        (table,),
    )
    create_stmt = cursor.fetchone()[0]
    sql_commands.append(f"\n-- Table: {table}\n{create_stmt}\n")

    cursor.execute(f'SELECT * FROM "{table}" ORDER BY 1;')
    rows = cursor.fetchall()

    if rows:
        cursor.execute(f"PRAGMA table_info({table});")
        column_names = [col[1] for col in cursor.fetchall()]

        quoted_columns = ", ".join(f'"{col}"' for col in column_names)
        for row in rows:
            values = []
            for val in row:
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                elif isinstance(val, bytes):
                    values.append("X'" + val.hex() + "'")
                else:
                    values.append(str(val))

            insert_stmt = f"INSERT OR IGNORE INTO \"{table}\" ({quoted_columns}) VALUES ({', '.join(values)});"
            sql_commands.append(insert_stmt)

# Write to file
with open('database_init.sql', 'w') as f:
    f.write("-- SQLite initialization script for the college website\n")
    f.writelines(sql_commands)

print("✅ Exported to database_init.sql")
print(f"Total SQL commands: {len(sql_commands)}")
