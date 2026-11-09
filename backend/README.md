# BloomLens backend

FastAPI API for document extraction, Bloom classification, similarity search,
analytics, and reviewer sessions.

## First-time setup

Requires Python 3.12. From the repository root:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
cp .env.example .env
.venv/bin/alembic upgrade head
```

Copy `.env.example` only if `.env` does not already exist. Keep credentials in
`.env` and do not commit it.

## Start the API

Run from `backend/`:

```bash
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --port 8000 --reload
```

Wait for **`Application startup complete`** before opening the frontend. The
reloader's “Uvicorn running” line alone does not confirm successful startup.
Stop the server with `Ctrl+C`.

- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API prefix: `/api/v1`

## Database and migrations

**MySQL is not required locally.** The default `DATABASE_URL` uses SQLite and
creates `bloomlens.db` in the backend directory.

For MySQL, create the database and credentials first, then set `DATABASE_URL` in
`.env` using `mysql+asyncmy://USER:PASSWORD@HOST:3306/DATABASE`. The application
uses asyncmy; Alembic uses the synchronous PyMySQL driver.

After pulling schema changes:

1. Stop the backend and back up the existing database.
2. Run `.venv/bin/alembic upgrade head` from `backend/`.
3. Restart the backend.

If startup reports an outdated schema or `no such column: error_message`, apply
the migrations above. Do not delete the database to resolve a migration error.
Migration rollback notes are in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Reviewer login

The supplied example configuration is for local development. To use reviewer
accounts, set these values in `backend/.env` for **local HTTP only**:

```env
AUTH_ENABLED=true
SESSION_COOKIE_SECURE=false
```

After migrations, provision an account from `backend/`:

```bash
.venv/bin/python -m app.manage_reviewers reviewer --role admin
```

The command prompts for a password of at least 12 characters. There is no public
registration. Running it again for an existing username resets its password and
revokes its sessions. Restart the backend after changing `.env`, then sign in
through the frontend.

Staging/production require authentication, HTTPS, secure cookies, and same-origin
frontend/API routing. Startup also validates required service credentials.
Shared `API_KEY` credentials belong on the server, never in frontend variables.
See [authentication details](../CONTRIBUTING.md).

## Useful settings

All settings are read from `backend/.env`; see [.env.example](.env.example).

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLite or MySQL connection |
| `GEMINI_API_KEY` | Optional Google verification in local development; question text is sent to Google when used |
| `MAX_UPLOAD_SIZE_MB` | File size limit, default 20 MB |
| `MAX_REQUEST_BODY_SIZE_MB` | Whole-request limit; must exceed the file limit |
| `UPLOAD_RATE_LIMIT_PER_MINUTE` | Upload admission limit per principal |
| `RETAIN_UPLOADED_FILES` | Keep source files after extraction; default false |
| `OCR_DPI` | Rendering resolution for OCR |

Uploads return `202`; processing updates can be read at
`/api/v1/papers/{id}/status`. Background tasks run inside the API process and are
not durable. Use one worker; interrupted jobs are marked failed on restart.

## Tests

Run from `backend/`:

```bash
.venv/bin/pytest tests/ -v
```

To reproduce the internal classifier evaluation:

```bash
.venv/bin/python -m scripts.evaluate_bloom
```

See the [evaluation protocol](tests/data/EVALUATION.md) for score interpretation,
embedding fallbacks, Google transmission, and benchmark limitations.
For containers and deployment verification limits, see the
[operations report](../spec/dependency-audit.md).
