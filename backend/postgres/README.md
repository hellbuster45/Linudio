# Using PostgreSQL instead of SQLite

Linudio uses a local SQLite file by default (`backend/storage/linudio.db`), which needs no setup.
PostgreSQL still works if you prefer it; this folder keeps everything needed to switch.

1. Install the driver (or run the installer with `python install.py --postgres`):

   ```bash
   pip install -r postgres/requirements-postgres.txt
   ```

2. Create an empty database:

   ```sql
   CREATE DATABASE linudio;
   ```

3. Point `DATABASE_URL` at it in `backend/.env` (see `.env.postgres.example`).

4. Start the backend. Tables are created automatically on startup; there is nothing to migrate.

Switching databases does not carry data over. Transcripts and video records live in whichever
database `DATABASE_URL` points to, so going back and forth means re-transcribing.
