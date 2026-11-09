# Contributing to BloomLens

Thank you for your interest in contributing to **BloomLens**! We welcome contributions from developers, researchers, and educators interested in AI-powered educational document analysis and question paper evaluation.

This document outlines the workflow, development environment setup, coding conventions, and verification steps required when contributing to this repository.

Install reproducible backend dependencies with
`pip install --require-hashes -r requirements.lock`. The lock targets the verified
Python 3.12 CPU environment and includes the official PyTorch CPU index. The
declared NumPy version matches the tested environment (2.3.5); SQLAlchemy's
`asyncio` extra includes greenlet. Use `npm ci` for the frontend lock. Regenerate
the backend lock with uv, preserving current pins unless deliberately upgrading:
`uv pip compile requirements.txt --constraint requirements.lock --generate-hashes --emit-index-url --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match --output-file /tmp/bloomlens-new.lock`.
Both indexes are trusted, and install-time hashes verify selected artifacts.

Application logs are JSON, including request IDs, route templates, status codes,
and durations. Known configured secret values are masked without discarding
ordinary token-related messages. Metrics cap route labels at 100 plus overflow;
unmatched routes share a label. OCR uses `OCR_DPI` (default 200) and evaluates each
page against `OCR_MIN_TEXT_CHARS` (default 50), retaining better existing text.
Images pass as pixel arrays rather than temporary filenames.

For local containers, copy `compose.env.example` to root `.env`, supply database
credentials and an encoded `mysql+asyncmy` URL using hostname `mysql`, then run
`docker compose up --build`. The frontend is on port 8080 and proxies `/api`.
Provision accounts with `docker compose exec backend python -m app.manage_reviewers alice`.
The local Compose default uses HTTP and development mode. HTTPS deployments must
set production/staging and secure cookies, supply required keys, and terminate
TLS at the same origin. Frontend Nginx and backend body limits must agree when
increasing the default 20 MB file limit. Containers use one backend worker because
the initial background dispatcher is in-process. PR CI runs backend tests and
frontend type-check, lint, tests, and build; remote results require a pushed PR.

Configuration defaults: Bloom verification uses `BLOOM_VERIFICATION_THRESHOLD=0.60`
and semantic similarity uses `SIMILARITY_THRESHOLD_SEMANTIC=0.70`. The example
environment mirrors these code defaults; changing them locally changes analysis
behavior. Only `VITE_USE_MOCK_API=true` enables the standalone demo. An unset or
false value uses the real backend. Examination types come from authenticated
`GET /api/v1/papers/exam-types`, the same list used by upload validation.
The backend provides a session gateway for browser reviewers; never put the
shared API key in browser configuration. Trusted server integrations can still
use the configured API key. Production/staging require authentication and secure
session cookies. The public health endpoint exposes only liveness; deep health
and all document/course/analytics routes require authentication.

After `alembic upgrade head`, provision a reviewer on the backend host with
`python -m app.manage_reviewers alice` (optionally `--role admin`). The command
prompts for a password of at least 12 characters; re-provisioning resets the
password and revokes existing sessions. There is no public registration.
Browser sessions expire after `SESSION_TTL_HOURS` (default eight), use HttpOnly
SameSite cookies, and require a session-bound CSRF header for writes. In local
HTTP development only, set `SESSION_COOKIE_SECURE=false`; production rejects
that setting. The Vite development proxy forwards `/api` to port 8000. Production
must serve frontend and `/api` on the same HTTPS origin.

`GET /api/v1/questions/{id}/revisions` returns immutable, authenticated review
history with actor, timestamp, and before/after snapshots. Migration
`reviewers_20261109` adds reviewer, session, and revision tables. Back up these
records before `alembic downgrade upload_jobs_20261109`, which deletes them.

Uploads return HTTP 202 with the committed paper ID, `UPLOADED` status, and a
`status_url`. Poll that endpoint for `PROCESSING`, `ANALYZING`, `COMPLETED`, or
`FAILED`; failures include a safe `error_message`. Processing uses FastAPI
BackgroundTasks through a dispatcher interface. This first implementation supports
one application worker: tasks are not durable, and startup marks interrupted jobs
failed. Replace the dispatcher with a durable queue before running multiple
application workers. Delete failed papers before retrying identical files.

`MAX_UPLOAD_SIZE_MB` bounds each file; `MAX_REQUEST_BODY_SIZE_MB` bounds the full
multipart request, including chunked bodies, and must exceed the file limit.
`UPLOAD_RATE_LIMIT_PER_MINUTE` defaults to ten per authenticated principal per
process. Files are deleted after successful extraction unless
`RETAIN_UPLOADED_FILES=true`; failed processing also removes the file. Database
deletion commits before file cleanup, and cleanup failures are logged.

Run `alembic upgrade head` before starting the new upload worker. Migration
`upload_jobs_20261109` adds nullable hashes, subject/hash uniqueness, and failure
details. Existing uploads are not retroactively hashed. Back up before rollback;
`alembic downgrade c0a1b2c3d4e5` removes these fields and their uniqueness rule.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Environment Setup](#development-environment-setup)
   - [Prerequisites](#prerequisites)
   - [Backend Setup (FastAPI)](#backend-setup-fastapi)
   - [Frontend Setup (React + Vite)](#frontend-setup-react--vite)
4. [Development Workflow & Git Guidelines](#development-workflow--git-guidelines)
5. [Coding Conventions & Standards](#coding-conventions--standards)
   - [Backend Conventions](#backend-conventions)
   - [Frontend Conventions](#frontend-conventions)
   - [Database Migrations](#database-migrations)
6. [Pre-Submission Verification](#pre-submission-verification)
7. [Reporting Bugs & Requesting Features](#reporting-bugs--requesting-features)

---

## Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](./CODE_OF_CONDUCT.md). Please read it before participating.

---

## How Can I Contribute?

- **Bug Fixes**: Resolve open issues on GitHub or fix edge cases in question extraction/classification.
- **Feature Enhancements**: Contribute improvements aligned with the V1 scope (see [`backend/README.md`](./backend/README.md) and [`spec/plan.md`](./spec/plan.md)).
- **Documentation**: Improve code comments, docstrings, API specifications, and setup instructions.
- **Testing**: Add test cases for complex question structures, ambiguous Bloom taxonomy verbs, and frontend components.

> [!NOTE]
> Note the V1 / V2 scope boundary: automated Course Outcome mapping and analytics, empirical student prediction, and automated paper generation remain out of scope. Course and outcome CRUD foundations are already present.

---

## Development Environment Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 18.x or 20.x** (with `npm 9.x+`)
- **SQLite** (local development) or **MySQL 8** (production)

---

### Backend Setup (FastAPI)

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(Windows: `.venv\Scripts\activate`)*

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Configure the backend for local development:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./bloomlens.db
   AUTH_ENABLED=false
   ```
   Authentication may be disabled for local development only. Never put a backend API key in a `VITE_` variable; browser code is public.

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the API server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - OpenAPI Documentation: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

### Frontend Setup (React + Vite)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Verify the configuration:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_MOCK_API=false
   ```
   The frontend intentionally does not send a shared API key. Protected actions require a trusted server-side integration when backend authentication is enabled.

4. **Start the development server**:
   ```bash
   npm run dev
   ```

---

## Development Workflow & Git Guidelines

1. **Fork or Branch**: Create a feature branch off `main`:
   ```bash
   git checkout -b feat/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```
2. **Make Targeted Commits**: Write descriptive commit messages using conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
3. **Keep Changes Focused**: Avoid broad, sweeping changes across unrelated components.
4. **Never Commit Secrets**: Do not commit `.env`, private keys, or credentials.

---

## Coding Conventions & Standards

For in-depth developer guidelines, consult [`user_contributions.md`](./user_contributions.md) and [`AGENTS.md`](./AGENTS.md).

### Backend Conventions
- **Configuration**: Use Pydantic `BaseSettings` defined in [`backend/app/core/config.py`](./backend/app/core/config.py). Never hardcode parameters or secrets.
- **Database Transactions**: Sessions yielded by `get_db()` do NOT auto-commit and roll back on exceptions. Mutating endpoints must explicitly call `await db.commit()`.
- **Authentication**: Protect state-mutating and analytics endpoints with FastAPI dependency-based auth (`get_current_user` in [`backend/app/core/auth.py`](./backend/app/core/auth.py)).
- **Concurrency**: Guard ML model and vector index lazy singletons with thread-safe double-checked locks (`threading.Lock`).
- **Error Handling**: Use structured exceptions from [`backend/app/core/errors.py`](./backend/app/core/errors.py) to return consistent error payloads.

### Frontend Conventions
- **React Query**: Manage server state with queries and mutations in [`frontend/src/services/queries.ts`](./frontend/src/services/queries.ts). Invalidate query caches on mutation success.
- **Error Handling**: Surface structured errors with `ApiError` and display user-friendly notifications via `sonner` toasts.
- **UI & Styling**: Use Tailwind CSS utility classes adhering to the project's slate palette and typography tokens.

### Database Migrations
When altering database models in [`backend/app/models/`](./backend/app/models):
```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

---

## Pre-Submission Verification

Before submitting a pull request, ensure all validation checks pass:

```bash
# 1. Run Backend Pytest Suite
cd backend && .venv/bin/pytest tests/ -v

# 2. Run Frontend Type-Check, Linter, Tests, and Build
cd ../frontend
npm run type-check
npm run lint
npm run test
npm run build
```

---

## Reporting Bugs & Requesting Features

- **Bug Reports**: Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) on GitHub. Include reproduction steps, sample paper formats (if applicable), and error traces.
- **Feature Requests**: Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md). Explain the context, motivation, and proposed solution.
- **Security Vulnerabilities**: Refer to [SECURITY.md](./SECURITY.md) for private disclosure instructions. Do not report security issues in public issues.
