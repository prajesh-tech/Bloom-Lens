# Contributing to BloomLens

Thank you for your interest in contributing to **BloomLens**! We welcome contributions from developers, researchers, and educators interested in AI-powered educational document analysis and question paper evaluation.

This document outlines the workflow, development environment setup, coding conventions, and verification steps required when contributing to this repository.

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

All contributors and maintainers are expected to follow our [Code of Conduct](file:///home/Prajesh/sp/CODE_OF_CONDUCT.md). Please read it before participating.

---

## How Can I Contribute?

- **Bug Fixes**: Resolve open issues on GitHub or fix edge cases in question extraction/classification.
- **Feature Enhancements**: Contribute improvements aligned with the V1 scope (see [`backend/README.md`](file:///home/Prajesh/sp/backend/README.md) and [`spec/plan.md`](file:///home/Prajesh/sp/spec/plan.md)).
- **Documentation**: Improve code comments, docstrings, API specifications, and setup instructions.
- **Testing**: Add test cases for complex question structures, ambiguous Bloom taxonomy verbs, and frontend components.

> [!NOTE]
> Note the V1 / V2 scope boundary: Course Outcomes (COs), student predictive analytics, and automated paper generation are out of scope for V1.

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
   Edit `.env` to configure your local keys and database URL:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./bloomlens.db
   GEMINI_API_KEY=your_gemini_api_key_here
   API_KEY=bloomlens-dev-secret-key-change-in-production
   AUTH_ENABLED=true
   ```

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
   VITE_API_KEY=bloomlens-dev-secret-key-change-in-production
   VITE_USE_MOCK_API=false
   ```

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

For in-depth developer guidelines, consult [`user_contributions.md`](file:///home/Prajesh/sp/user_contributions.md) and [`AGENTS.md`](file:///home/Prajesh/sp/AGENTS.md).

### Backend Conventions
- **Configuration**: Use Pydantic `BaseSettings` defined in [`backend/app/core/config.py`](file:///home/Prajesh/sp/backend/app/core/config.py). Never hardcode parameters or secrets.
- **Database Transactions**: Sessions yielded by `get_db()` do NOT auto-commit and roll back on exceptions. Mutating endpoints must explicitly call `await db.commit()`.
- **Authentication**: Protect state-mutating and analytics endpoints with FastAPI dependency-based auth (`get_current_user` in [`backend/app/core/auth.py`](file:///home/Prajesh/sp/backend/app/core/auth.py)).
- **Concurrency**: Guard ML model and vector index lazy singletons with thread-safe double-checked locks (`threading.Lock`).
- **Error Handling**: Use structured exceptions from [`backend/app/core/errors.py`](file:///home/Prajesh/sp/backend/app/core/errors.py) to return consistent error payloads.

### Frontend Conventions
- **React Query**: Manage server state with queries and mutations in [`frontend/src/services/queries.ts`](file:///home/Prajesh/sp/frontend/src/services/queries.ts). Invalidate query caches on mutation success.
- **Error Handling**: Surface structured errors with `ApiError` and display user-friendly notifications via `sonner` toasts.
- **UI & Styling**: Use Tailwind CSS utility classes adhering to the project's slate palette and typography tokens.

### Database Migrations
When altering database models in [`backend/app/models/`](file:///home/Prajesh/sp/backend/app/models/):
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

- **Bug Reports**: Use the [Bug Report Template](file:///home/Prajesh/sp/.github/ISSUE_TEMPLATE/bug_report.md) on GitHub. Include reproduction steps, sample paper formats (if applicable), and error traces.
- **Feature Requests**: Use the [Feature Request Template](file:///home/Prajesh/sp/.github/ISSUE_TEMPLATE/feature_request.md). Explain the context, motivation, and proposed solution.
- **Security Vulnerabilities**: Refer to [SECURITY.md](file:///home/Prajesh/sp/SECURITY.md) for private disclosure instructions. Do not report security issues in public issues.
