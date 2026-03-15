import sqlite3
import os

db_path = 'college.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Exporting database to SQL...")

# Get all tables except sqlite_sequence
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

sql_commands = []

for table in tables:
    # Get CREATE TABLE statement
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
    create_stmt = cursor.fetchone()[0]
    sql_commands.append(f"\n-- Table: {table}\n{create_stmt};\n")
    
    # Get all data
    cursor.execute(f"SELECT * FROM {table};")
    rows = cursor.fetchall()
    
    if rows:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]
        
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
            
            insert_stmt = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});"
            sql_commands.append(insert_stmt)

conn.close()

# Write to file
with open('database_init.sql', 'w') as f:
    f.write("-- Database initialization script for Render\n")
    f.write("-- Auto-generated from college.db\n\n")
    f.writelines(sql_commands)

print("✅ Exported to database_init.sql")
print(f"Total SQL commands: {len(sql_commands)}")
