# BloomLens frontend

React, TypeScript, and Vite UI for uploading exam papers, reviewing questions,
and viewing Bloom, topic, similarity, and history analytics.

## First-time setup

Requires Node.js 20.19+ or 22.12+ and npm. From the repository root:

```bash
cd frontend
npm ci
cp .env.example .env
```

Copy `.env.example` only if `.env` does not already exist. For the real backend,
keep these settings in `frontend/.env`:

```env
VITE_API_BASE_URL=
VITE_USE_MOCK_API=false
```

An empty API host uses the same origin. Vite forwards `/api` to the backend on
port 8000. The API client appends `/api/v1`; do not include that path in
`VITE_API_BASE_URL`. Never put shared service keys in `VITE_` variables, which
are visible to the browser.

## Run locally

Start the backend in a separate terminal using the
[backend guide](../backend/README.md#start-the-api). Wait for
**`Application startup complete`**.

Then run from `frontend/`:

```bash
npm run dev
```

Open the URL printed by Vite, normally [http://localhost:3000](http://localhost:3000).
Stop Vite with `Ctrl+C`. Restart it after changing `.env`.

If backend authentication is enabled, sign in with an
[administrator-provisioned reviewer account](../backend/README.md#reviewer-login).

## Using the app

1. Open **Analyze**, select a PDF or DOCX file, and enter its subject and exam details.
2. Submit the upload and wait for extraction and analysis. Processing failures
   appear in the UI; a failed status request can be retried.
3. Open a question to review classifier signals, make corrections, find similar
   questions, or inspect revision history.
4. Use **Analytics** and the dashboard's subject filter to explore results.

For a standalone demonstration, set `VITE_USE_MOCK_API=true` and restart Vite.
Only the literal `true` enables mocks. Demo edits stay in memory and reset on
reload; they do not update the backend. The “Real API” badge describes the
selected mode, not backend health.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| “Unable to connect to BloomLens” | Check the backend terminal for startup errors. Wait for `Application startup complete`, then click Retry. |
| Missing column/table or outdated database | From `backend/`, back up the database, run `.venv/bin/alembic upgrade head`, and restart the API. |
| Requests go to the wrong address or return 404 | Leave `VITE_API_BASE_URL` empty for normal local development, then restart Vite. |
| Sign-in succeeds but the session is lost on local HTTP | Check the backend's local cookie configuration in the [login guide](../backend/README.md#reviewer-login). |
| CORS errors with a separate API host | Prefer the default Vite proxy. For intentional cross-origin setups, configure the exact frontend origin in backend `FRONTEND_ORIGINS`. |
| Mock data remains visible | Set `VITE_USE_MOCK_API=false` and restart Vite. |

Retrying in the browser cannot repair a backend that failed to start. SQLite is
supported locally; switching to MySQL is not necessary to fix missing migrations.

## Checks and build

Run from `frontend/`:

```bash
npm run type-check
npm run lint
npm run test
npm run build
```

The build writes `dist/` and enforces a 400 kB uncompressed budget for entry
JavaScript plus static imports. Routes load on demand; Recharts has its own chunk.
Serve production assets and `/api` under the same HTTPS origin. The included
[nginx configuration](nginx.conf) provides that routing for the container setup.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development conventions and
[the main README](../README.md) for the complete local setup.
