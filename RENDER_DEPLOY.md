# Render + Supabase Deployment (Flask)

This project is configured for PostgreSQL and can be deployed on Render using Supabase as the managed database.

## 1) Create Supabase project

1. Create a new project in Supabase.
2. Choose a region close to your Render region.
3. In Supabase dashboard, open `Project Settings -> Database`.
4. Copy the PostgreSQL connection string (prefer the pooler/transaction URL for production).

## 2) Prepare database schema on Supabase

Use one of these options:

1. Open Supabase SQL Editor and run `database_init.sql`.
2. Import an existing PostgreSQL dump if migrating live data.

This creates the required tables:

1. `admissions`
2. `admin`
3. `gallery_images`

## 3) Configure Render web service

1. Push code to GitHub.
2. Create a new Render Web Service from the repo.
3. Use `render.yaml` or set manually:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -c gunicorn.conf.py app:app`

## 4) Environment variables (Render)

Set these variables in Render:

1. `DATABASE_URL=<Supabase PostgreSQL URL>`
2. `PGSSLMODE=require`
3. `FLASK_SECRET_KEY=<strong-random-secret>`
4. `FLASK_SECURE_COOKIE=1`

Notes:

1. App also supports `SUPABASE_DB_URL` as a fallback if `DATABASE_URL` is not set.
2. If URL starts with `postgres://`, code auto-converts to `postgresql://`.

## 5) Deploy and verify

1. Trigger deploy on Render.
2. Check Render logs for successful app startup and DB connection.
3. Verify health endpoints:
   - `/health`
   - `/healthz`
4. Test these flows:
   - Admission form submit
   - Admin login
   - Gallery view/upload

## 6) Data migration checklist (if moving from old PostgreSQL)

1. Export old DB using `pg_dump`.
2. Import into Supabase using `psql`.
3. Re-run `database_init.sql` only if needed for missing objects.
4. Confirm row counts for `admissions`, `admin`, `gallery_images`.

## 7) Security checklist

1. Change default admin credentials after first login.
2. Never commit DB URLs or secrets to git.
3. Rotate secrets if accidentally exposed.
4. Keep `FLASK_SECURE_COOKIE=1` in production.

## 8) App behavior notes

1. Tables are auto-created at startup by `config.py` when missing.
2. Existing non-hashed admin passwords are migrated to hashed values automatically.
3. Frontend remains unchanged; only DB backend changes.
