# Developer Contribution Guide

Welcome to the **BloomLens** project! This guide is designed to help you onboard quickly, understand our workflows, and make meaningful contributions without disrupting the existing codebase flow.

---

## 1. Getting Started & Development Setup

BloomLens consists of a **FastAPI** backend and a **Vite + React + TypeScript** frontend.

### Prerequisites
- **Python 3.12+**
- **Node.js 18.x or 20.x** (with `npm 9.x+`)
- **SQLite** (default for local development) or **MySQL 8**

---

### Backend Setup

1. **Navigate to the Backend Directory**:
   ```bash
   cd backend
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(On Windows: `.venv\Scripts\activate`)*

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Modify `.env` to include your configuration settings:
   ```env
   DATABASE_URL=sqlite:///./bloomlens.db
   GEMINI_API_KEY=your_actual_gemini_api_key
   AUTH_ENABLED=true
   API_KEY=bloomlens-dev-secret-key-change-in-production
   ```
   > [!WARNING]
   > Never commit `.env` files or hardcoded credentials to Git.

5. **Initialize/Upgrade Database Schema**:
   Run Alembic migrations to seed the database (including the L1-L6 Bloom Taxonomy levels):
   ```bash
   alembic upgrade head
   ```

---

### Frontend Setup

1. **Navigate to the Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Install Node Dependencies**:
   ```bash
   npm install
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Specify your API URL, authentication key, and mock mode configuration:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_KEY=bloomlens-dev-secret-key-change-in-production
   VITE_USE_MOCK_API=false
   ```
   - Set `VITE_USE_MOCK_API=true` to run the frontend in offline demo mode using simulated network latency (1.5s - 2.5s).
   - Set `VITE_USE_MOCK_API=false` to connect to the live backend server.

---

## 2. Core Commands Reference

Always run commands from their respective subfolders.

### Backend Commands
- **Start Dev Server**: `source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **Run Tests**: `source .venv/bin/activate && pytest tests/ -v` (or `.venv/bin/pytest tests/ -v`)

### Frontend Commands
- **Start Dev Server**: `npm run dev` (runs at `http://localhost:3000` or `http://localhost:5173`)
- **Type-Check TypeScript**: `npm run type-check`
- **Linter Check**: `npm run lint`
- **Run Tests**: `npm run test` (Vitest)
- **Compile Production Build**: `npm run build`

---

## 3. Working Conventions & Code Style

### General Rules
- **Small, targeted changes**: Avoid large refactorings or rewrites unless explicitly planned.
- **Do not suppress audit/test failures**: If a test or check fails, fix it before requesting a review.

### Backend Conventions
- **FastAPI Config Patterns**: Keep settings defined inside [`backend/app/core/config.py`](file:///home/Prajesh/sp/backend/app/core/config.py) using Pydantic's `BaseSettings`. Do not hardcode values outside this module.
- **Database Transaction Management**: Sessions yielded by `get_db()` do NOT auto-commit and automatically roll back on exceptions. Write routes must explicitly execute `db.commit()` upon successful completion of business logic. Read-only endpoints must never commit transactions.
- **API Authentication**: Protect state-mutating and analytics endpoints using `get_current_user` dependency from [`backend/app/core/auth.py`](file:///home/Prajesh/sp/backend/app/core/auth.py).
- **Concurrency & Lazy Initialization**: Shared ML engines and vector models must use thread-safe double-checked locks (`threading.Lock`) during lazy initialization.
- **Exception Handling**: Raise custom exceptions from [`backend/app/core/errors.py`](file:///home/Prajesh/sp/backend/app/core/errors.py) to return consistent structured JSON errors. Avoid exposing internal stack traces or connection errors in API responses.

### Frontend Conventions
- **React Query**: Align data fetching and state invalidation with hooks in [`frontend/src/services/queries.ts`](file:///home/Prajesh/sp/frontend/src/services/queries.ts). Always invalidate queries or update query cache correctly upon success of mutations (e.g., upload, patch, delete).
- **Error Handling**: Use the Custom `ApiError` class when communicating with the backend. Keep error handling unified so toast notifications (using `sonner`) accurately display the API error message.
- **Styling**: Use Vanilla Tailwind CSS utility classes and ensure visual layout components align with the `bg-slate-50` background theme and JetBrains Mono monospace typography.

---

## 4. Database Schema Migrations

We use **Alembic** to manage database schema updates.

1. If you modify any SQLAlchemy model in [`backend/app/models/`](file:///home/Prajesh/sp/backend/app/models/), generate a new migration script:
   ```bash
   cd backend
   source .venv/bin/activate
   alembic revision --autogenerate -m "describe your changes"
   ```
2. Open the generated script in `backend/alembic/versions/` and manually inspect the `upgrade()` and `downgrade()` code blocks to verify correctness.
3. Apply the migration locally:
   ```bash
   alembic upgrade head
   ```

---

## 5. Pre-Merge Verification Checklist

Before pushing your branch or submitting a PR, make sure you check off all items:

- [ ] All environment configurations are validated (e.g., test runtime configs).
- [ ] Backend test suite passes: `cd backend && .venv/bin/pytest tests/ -q`
- [ ] Frontend static type checking passes: `cd frontend && npm run type-check`
- [ ] Frontend linter passes: `cd frontend && npm run lint`
- [ ] Frontend unit tests pass: `cd frontend && npm run test`
- [ ] Frontend production compilation succeeds: `cd frontend && npm run build`
- [ ] No secrets or keys are committed to Git (sensitive configs belong in `.env`).
- [ ] Relevant documentation has been updated.
