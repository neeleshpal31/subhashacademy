# PostgreSQL Complete Setup

Use this checklist to fully switch this project from SQLite to PostgreSQL.

## 1) Install PostgreSQL on Windows (Fresh Laptop)

Your machine has `winget` available, so install PostgreSQL with:

```powershell
winget install -e --id PostgreSQL.PostgreSQL
```

During installation:

1. Set a password for user `postgres` and remember it.
2. Keep default port as `5432`.
3. Complete install and let service start.

After install, open a new PowerShell window and verify:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" --version
```

If version command fails, check this alternate path:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" --version
```

## 2) Create Local Database

Use `psql` and create DB:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5432 -c "CREATE DATABASE college_db;"
```

If DB already exists, you can ignore the error.

## 3) Required Environment Variables

Set these in local terminal (PowerShell):

```powershell
$env:DATABASE_URL="postgresql://postgres:your_password@localhost:5432/college_db"
$env:PGSSLMODE="disable"
$env:SQLITE_SOURCE_PATH="college.db"
$env:FLASK_SECRET_KEY="change-this-in-production"
$env:FLASK_SECURE_COOKIE="0"
```

For Render/Cloud PostgreSQL, use:

```powershell
$env:DATABASE_URL="postgresql://user:password@host:5432/dbname"
$env:PGSSLMODE="require"
$env:SQLITE_SOURCE_PATH="college.db"
$env:FLASK_SECRET_KEY="your-strong-secret"
$env:FLASK_SECURE_COOKIE="1"
```

## 4) Install/Update Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5) Transfer Complete Data from SQLite to PostgreSQL

Run migration script:

```powershell
.\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py
```

If you want a fresh full replace each run (clear PostgreSQL tables first):

```powershell
$env:MIGRATION_TRUNCATE="1"
.\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py
```

## 6) Start Application with PostgreSQL

```powershell
.\.venv\Scripts\python.exe app.py
```

or with gunicorn:

```powershell
gunicorn -c gunicorn.conf.py app:app
```

## 7) Verify Migration Counts

```powershell
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe check_tables.py
```

## 8) Common Errors and Fix

1. Error: `DATABASE_URL is required`
   - Fix: set `$env:DATABASE_URL=...` in same terminal before running script.

2. Error: SSL connection issues
   - Local DB: use `PGSSLMODE=disable`
   - Cloud DB: use `PGSSLMODE=require`

3. Error: authentication failed
   - Recheck username/password/host/port/db name in `DATABASE_URL`.

4. Error: `psql` not recognized
   - Use full path command shown in Step 1 and Step 2.

## 9) Final Status Condition

Migration is complete when:

1. `migrate_sqlite_to_postgres.py` prints "Migration completed successfully".
2. `check_db.py` shows tables and expected row counts.
3. Website opens and admission/admin/gallery work normally.
