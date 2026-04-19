# Supabase Complete Setup

Use this checklist to run the full project database on Supabase (managed PostgreSQL).

## 1) Create Supabase project

1. Create a new Supabase project.
2. In Supabase dashboard open: `Project Settings -> Database`.
3. Copy the PostgreSQL connection URL (pooler URL is recommended).

## 2) Required environment variables

Set these in local PowerShell:

```powershell
$env:SUPABASE_DB_URL="postgresql://postgres.xxxxx:[password]@aws-0-xx-xx-xx.pooler.supabase.com:6543/postgres"
$env:PGSSLMODE="require"
$env:SQLITE_SOURCE_PATH="college.db"
$env:FLASK_SECRET_KEY="change-this-in-production"
$env:FLASK_SECURE_COOKIE="0"
```

For production (Render):

```powershell
SUPABASE_DB_URL=<supabase-postgres-url>
PGSSLMODE=require
FLASK_SECRET_KEY=<strong-secret>
FLASK_SECURE_COOKIE=1
```

Notes:

1. App now prefers `SUPABASE_DB_URL`.
2. `DATABASE_URL` still works as fallback.

## 3) Install/update dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4) Migrate SQLite data to Supabase

Run migration script:

```powershell
.\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py
```

For full replace (truncate target tables first):

```powershell
$env:MIGRATION_TRUNCATE="1"
.\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py
```

## 5) Start app with Supabase DB

```powershell
run_app.cmd
```

or:

```powershell
.\.venv\Scripts\python.exe app.py
```

## 6) Verify application flow

1. Open website and check home/gallery pages.
2. Test admission form submit.
3. Test admin login and gallery upload/delete.
4. Check health endpoints: `/health` and `/healthz`.

## 7) Common errors and fixes

1. Error: `SUPABASE_DB_URL ... is required`
   - Fix: set `SUPABASE_DB_URL` in the same terminal/session.

2. Error: SSL connection failed
   - Fix: ensure `PGSSLMODE=require` for Supabase.

3. Error: authentication failed
   - Fix: verify username/password/host/port from Supabase connection string.

4. Timeout during DB connect
   - Fix: ensure your network allows outbound connection to Supabase and use pooler URL.

## 8) Final success condition

Setup is complete when:

1. `migrate_sqlite_to_postgres.py` prints `Migration completed successfully`.
2. Website opens using Supabase-backed data.
3. Admission/admin/gallery flows work without local PostgreSQL.