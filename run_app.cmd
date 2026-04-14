@echo off
setlocal

cd /d "%~dp0"

set "DATABASE_URL=postgresql://postgres:998877@localhost:5432/college_db"
set "PGSSLMODE=disable"
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
