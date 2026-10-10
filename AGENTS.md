# AGENTS.md

Guidance for AI coding agents (and humans) working in the BloomLens repository. Read this before making changes.

## Project overview

BloomLens is a document-intelligence application.

| Area | Stack |
|------|-------|
| Backend (`backend/`) | FastAPI, SQLAlchemy 2.0 (async), AI document processing, FAISS vector search, analytics |
| Frontend (`frontend/`) | Vite, React, TypeScript, React Query |

## Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in values locally; never commit

# Frontend
cd frontend
npm install
cp .env.example .env        # if present
```

## Commands

| Task | Command |
|------|---------|
| Backend tests | `cd backend && .venv/bin/pytest tests/ -v` |
| Frontend type-check | `cd frontend && npm run type-check` |
| Frontend tests | `cd frontend && npm run test` |
| Frontend build | `cd frontend && npm run build` |

Use these exact commands so results are comparable across contributors and CI.

## Working principles

1. **Small, targeted changes.** Prefer minimal diffs over broad rewrites or drive-by refactors. If a larger change is needed, explain why first.
2. **Follow existing patterns.** Look at neighbouring code before introducing a new approach, library, or abstraction.
3. **Be honest about results.** Never silently suppress, skip, or loosen failing tests, audits, or lint checks. Report them.
4. **Verify before claiming done.** "It should work" is not evidence; command output is.

## Backend conventions

- **Config and settings:** use the existing FastAPI settings/config pattern. Do not read `os.environ` ad hoc in route or service code.
- **Auth:** use dependency-based auth from `app/core/auth.py`. Every new route must declare its auth dependency explicitly, including intentionally public ones.
- **Database sessions:**
  - `get_db()` yields a session and rolls back on exception. It does **not** auto-commit.
  - Write routes must commit explicitly. Read routes must not commit.
  - Keep transactions short; do not hold a session open across slow AI or network calls.
- **Async correctness:** use `async`/`await` consistently. Do not call blocking I/O (file, network, CPU-heavy embedding work) on the event loop; offload it to a thread or worker.
- **Lazy singletons** (models, FAISS indexes, clients): initialise at module level lazily, protected by `threading.Lock` with double-checked initialisation.
- **Schemas:** keep request/response models in Pydantic; do not leak ORM objects through the API.
- **Migrations:** schema changes ship with a migration and a note on rollback.

## Frontend conventions

- Use the existing React Query setup for all server state; do not add parallel fetching or caching layers.
- Route errors through the existing error-handling structure rather than local `try/catch` with `console.error`.
- Keep types strict. No `any` or `@ts-ignore` without a comment explaining why.
- Reuse existing components and hooks before adding new ones.

## Security and configuration

- Keep secrets out of source control. Use local `.env` files only; update `.env.example` when adding variables (names only, no values).
- Validate required environment variables at startup and fail fast with a clear message.
- Never log secrets, tokens, or raw document contents.
- Treat uploaded documents and model output as untrusted input: validate type, size, and content before processing or rendering.
- Run a dependency audit when adding or upgrading packages, and report the findings.

## Testing expectations

- New behaviour needs tests; bug fixes need a regression test that fails without the fix.
- Prefer testing observable behaviour (API responses, rendered UI) over implementation details.
- Do not mark a task complete with failing, skipped, or newly flaky tests.

## Definition of done

A task is closed only when all of the following hold:

- [ ] Backend: full suite passes (`.venv/bin/pytest tests/ -v`)
- [ ] Frontend: type-check, tests, and build all pass
- [ ] No unrelated files modified; no secrets or debug code committed
- [ ] Docs and `.env.example` updated if behaviour or configuration changed
- [ ] Summary states what changed, what was verified, and what was not

If a sandbox or environment problem prevents a command from running, say so plainly and quote the exact command and its output. Do not substitute a weaker check without saying so.

## Boundaries

**Ask first** before: adding dependencies, changing the database schema, altering auth or permission logic, changing CI or build configuration, or touching V2-scoped work (see the plan).

**Never:** commit secrets, disable auth for convenience, force-push shared branches, delete or rewrite tests to make them pass, or claim production readiness without verification evidence for security, transactions, and build quality.

## Documentation references

| Document | Purpose |
|----------|---------|
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Canonical onboarding, setup, and contribution guidelines |
| [`user_contributions.md`](./user_contributions.md) | Compatibility pointer to the canonical developer guide |
| [`design.md`](./design.md) | System diagrams, pipeline flows |
| [`spec/spec.md`](./spec/spec.md) | API contract, models |
| [`spec/plan.md`](./spec/plan.md) | Milestones, V1/V2 scope boundaries |
| [`spec/tasks.md`](./spec/tasks.md) | Task management and maintenance checks |
| [`spec/skills.md`](./spec/skills.md) | Competency matrix and developer guidelines |

If these documents conflict with this file, flag the conflict rather than guessing.
