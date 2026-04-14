from config import db

cursor = db.cursor()

print("Exporting database to SQL...")

# Get all public tables
cursor.execute(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
)
tables = [row[0] for row in cursor.fetchall()]

sql_commands = []

for table in tables:
    sql_commands.append(f"\n-- Table: {table}\n")

    cursor.execute(f'SELECT * FROM "{table}" ORDER BY 1;')
    rows = cursor.fetchall()

    if rows:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
            """,
            (table,),
        )
        column_names = [col[0] for col in cursor.fetchall()]

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
                elif isinstance(val, memoryview):
                    values.append("X'" + val.tobytes().hex() + "'")
                else:
                    values.append(str(val))

            insert_stmt = f"INSERT INTO \"{table}\" ({quoted_columns}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;"
            sql_commands.append(insert_stmt)

# Write to file
with open('database_init.sql', 'w') as f:
    f.write("-- PostgreSQL initialization script for the college website\n")
    f.writelines(sql_commands)

print("✅ Exported to database_init.sql")
print(f"Total SQL commands: {len(sql_commands)}")
