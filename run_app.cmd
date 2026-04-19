@echo off
setlocal

cd /d "%~dp0"

if "%SUPABASE_DB_URL%"=="" (
    echo ERROR: SUPABASE_DB_URL is not set.
    echo Please set Supabase PostgreSQL connection string before running.
    echo Example:
    echo   set "SUPABASE_DB_URL=postgresql://postgres.xxxxx:[password]@aws-0-xx-xx-xx.pooler.supabase.com:6543/postgres"
    exit /b 1
)

if "%PGSSLMODE%"=="" set "PGSSLMODE=require"

set "SQLITE_SOURCE_PATH=college.db"
set "FLASK_SECRET_KEY=change-this-in-production"
set "FLASK_SECURE_COOKIE=0"

if exist ".venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe app.py
) else (
    echo ERROR: .venv\Scripts\python.exe not found.
    echo Please create virtual environment first.
    exit /b 1
)
