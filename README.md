# BloomLens

## Overview

BloomLens analyzes PDF and DOCX exam papers. It extracts questions and marks,
classifies Bloom levels, finds repeated or similar questions, and provides
subject and topic analytics. Reviewers can correct results and view edit history.

The backend uses FastAPI; the frontend uses React and Vite. **SQLite is included
for local development—you do not need to install MySQL.** MySQL is supported for
deployment.

## Key Features

- **Document extraction:** Read PDF and DOCX papers, with OCR for scanned PDF
  pages, while preserving printed question numbers and sub-question hierarchy.
- **Marks validation:** Extract marks, count scoring sub-questions, and flag
  uncertain optional-question rules.
- **Bloom classification:** Classify questions from L1 Remember to L6 Create
  using verbs, semantic embeddings, question structure, and optional Google verification.
- **Similarity search:** Find exact repeats and near duplicates within a subject.
- **Analytics:** Explore Bloom distributions, topic frequencies, and exam-date
  trends with subject filters.
- **Reviewer workflow:** Correct extracted results and inspect attributed
  revision history using administrator-provisioned accounts.

## Tech Stack

| Area | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy async, Alembic |
| Database | SQLite with aiosqlite locally; MySQL with asyncmy for deployment |
| Document processing | PyMuPDF, python-docx, PaddleOCR |
| Classification and similarity | SentenceTransformers, FAISS/NumPy, optional Google GenAI SDK |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Query, Recharts |
| Testing | Pytest, HTTPX, Vitest, React Testing Library |

## Repository Structure

```text
BloomLens/
├── backend/
│   ├── app/                 # API routes, models, schemas, and services
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests and evaluation fixtures
│   ├── requirements.lock    # Locked backend dependencies
│   └── README.md            # Backend setup and configuration
├── frontend/
│   ├── src/                 # Pages, components, hooks, and API clients
│   ├── tests/               # Frontend tests
│   ├── package-lock.json    # Locked frontend dependencies
│   └── README.md            # Frontend setup and troubleshooting
├── spec/                    # Specifications, scope, and verification reports
├── .github/workflows/       # CI workflows
├── docker-compose.yml       # Backend, frontend, and MySQL services
├── CONTRIBUTING.md          # Development guidelines
├── design.md                # Architecture and processing pipeline
└── LICENSE                  # MIT license
```

## Requirements

- Python 3.12
- Node.js 20.19+ or 22.12+, with npm
- Git

The commands below use a Linux/macOS shell. The backend dependency lock was
verified on Python 3.12 with Linux CPU packages.

## First-time setup

Run these commands from the repository root. Copy each `.env.example` only on
first setup; keep an existing `.env` when updating the project.

```bash
# Backend
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
cp .env.example .env
.venv/bin/alembic upgrade head

# Frontend
cd ../frontend
npm ci
cp .env.example .env
```

The backend defaults to a local SQLite database at `backend/bloomlens.db`.
For the frontend, leave `VITE_API_BASE_URL` empty and keep
`VITE_USE_MOCK_API=false` to use the real backend.

## Run locally

Open **two terminals**, each starting at the repository root.

Terminal 1 — backend:

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --port 8000 --reload
```

Wait for **`Application startup complete`**. Run migrations after pulling schema
changes, and back up existing database files before applying them.

Terminal 2 — frontend:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite, normally [http://localhost:3000](http://localhost:3000).
API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).
Use `Ctrl+C` in each terminal to stop its server.

The example backend configuration is for local development. To enable reviewer
login, follow the [backend authentication instructions](backend/README.md#reviewer-login).

## Common problems

| Problem | Action |
| --- | --- |
| “Unable to connect to BloomLens” | Check that the backend reached `Application startup complete`. Then click Retry. |
| Missing column/table or outdated schema | From `backend/`, run `.venv/bin/alembic upgrade head`, then restart the backend. |
| Mock data instead of uploaded papers | Set `VITE_USE_MOCK_API=false` in `frontend/.env` and restart Vite. |
| Address already in use | Stop the existing server before starting another on that port. |

More connection troubleshooting is in the [frontend guide](frontend/README.md#troubleshooting).

## Verify changes

From the repository root:

```bash
cd backend
.venv/bin/pytest tests/ -v
cd ../frontend
npm run type-check
npm run lint
npm run test
npm run build
```

## Behavior and limits

- Upload processing runs in the background; the UI polls its status. The current
  worker is in-process and jobs can fail on restart. Use one backend worker.
- Uploaded files are deleted after extraction by default. This is configurable.
- Classifier scores are uncalibrated, not probabilities. Semantic search can use
  a hashing fallback when the embedding model is unavailable; FAISS has a NumPy
  fallback. Optional question choices can make distributions uncertain.
- Google verification, when configured, sends question text to Google. Leave
  `GEMINI_API_KEY` empty for local development without that service.

## Further reading

- [Backend setup, configuration, and login](backend/README.md)
- [Frontend setup and troubleshooting](frontend/README.md)
- [Contributing and operational details](CONTRIBUTING.md)
- [Classifier evaluation and limitations](backend/tests/data/EVALUATION.md)
- [Implementation status](spec/remediation-status.md) and [deployment verification limits](spec/dependency-audit.md)
- [Architecture](design.md), [V1/V2 scope](spec/plan.md), and [security policy](SECURITY.md)

[MIT License](LICENSE)
