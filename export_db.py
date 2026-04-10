from config import db

cursor = db.cursor()

print("Exporting database to SQL...")

# Get all tables except sqlite_sequence
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() ORDER BY table_name;")
tables = [row[0] for row in cursor.fetchall()]

sql_commands = []

for table in tables:
    cursor.execute(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    columns = cursor.fetchall()

    column_defs = []
    for column_name, data_type, is_nullable, column_default in columns:
        definition = f'    "{column_name}" {data_type.upper()}'
        if column_default:
            definition += f" DEFAULT {column_default}"
        if is_nullable == 'NO':
            definition += " NOT NULL"
        column_defs.append(definition)

    create_stmt = f"CREATE TABLE IF NOT EXISTS \"{table}\" (\n" + ",\n".join(column_defs) + "\n);"
    sql_commands.append(f"\n-- Table: {table}\n{create_stmt}\n")

    cursor.execute(f'SELECT * FROM "{table}" ORDER BY 1;')
    rows = cursor.fetchall()

    if rows:
        column_names = [col[0] for col in columns]

        quoted_columns = ", ".join(f'"{col}"' for col in column_names)
        for row in rows:
            values = []
            for val in row:
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))

            insert_stmt = f"INSERT INTO \"{table}\" ({quoted_columns}) VALUES ({', '.join(values)});"
            sql_commands.append(insert_stmt)

# Write to file
with open('database_init.sql', 'w') as f:
    f.write("-- PostgreSQL initialization script for the college website\n")
    f.writelines(sql_commands)

print("✅ Exported to database_init.sql")
print(f"Total SQL commands: {len(sql_commands)}")
