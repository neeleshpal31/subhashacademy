# Render Deployment (PostgreSQL)

This project is configured to run with PostgreSQL on Render.

## 1) One-time setup on Render

1. Push this repo to GitHub.
2. In Render, create a new Web Service from this repo.
3. Use `render.yaml` (Blueprint) or set values manually:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -c gunicorn.conf.py app:app`
4. Create a PostgreSQL database service in Render.
5. Set environment variables:
   - `DATABASE_URL=<Render PostgreSQL connection string>`
   - `FLASK_SECRET_KEY=<strong-random-secret>`
   - `FLASK_SECURE_COOKIE=1`
   - Optional: `PGSSLMODE=require` (recommended for hosted DB)

## 2) Why PostgreSQL is better on Render

PostgreSQL is managed, persistent, and supports concurrent requests better than file-based SQLite for production apps.

## 3) Health checks

After deploy, verify:
- `/health`
- `/healthz`

Both should return status `ok`.

## 4) Notes

- Database tables are auto-created by `config.py` at app startup.
- Admin default is seeded only when `admin` table is empty.
- Existing frontend (HTML/CSS/JS) remains unchanged; only backend database is migrated.
