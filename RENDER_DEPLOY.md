# Render Deployment (SQLite)

This project is now configured to run with SQLite on Render.

## 1) One-time setup on Render

1. Push this repo to GitHub.
2. In Render, create a new Web Service from this repo.
3. Use `render.yaml` (Blueprint) or set values manually:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -c gunicorn.conf.py app:app`
4. Add a Persistent Disk:
   - Mount path: `/var/data`
   - Size: `1 GB` (or more)
5. Set environment variables:
   - `SQLITE_DB_PATH=/var/data/college.db`
   - `FLASK_SECRET_KEY=<strong-random-secret>`
   - `FLASK_SECURE_COOKIE=1`

## 2) Why persistent disk is required

SQLite file must survive restarts. Without a disk mount, Render's filesystem is ephemeral and data can be lost on redeploy/restart.

## 3) Health checks

After deploy, verify:
- `/health`
- `/healthz`

Both should return status `ok`.

## 4) Notes

- Database tables are auto-created by `config.py` at app startup.
- Admin default is seeded only when `admin` table is empty.
- For SQLite stability, Gunicorn threads default is set to 1 in `gunicorn.conf.py`.
