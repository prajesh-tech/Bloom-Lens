# AGENTS.md

## Project overview
This repository contains the BloomLens application:
- backend: FastAPI service with SQLAlchemy, AI document processing, and analytics
- frontend: Vite + React + TypeScript UI

## Working conventions
- Keep backend changes aligned with the FastAPI settings/config patterns.
- Keep frontend changes aligned with the existing React Query and error-handling structure.
- Prefer small, targeted changes over broad rewrites.
- When working on security or config, validate environment variables before merging.
- Do not silently suppress audit or test failures.

## Verification expectations
- Backend: prefer focused tests that cover the modified behavior.
- Frontend: run the relevant type-check/test/build commands before closing a task.
- If a sandbox or environment issue prevents a command from running, document that clearly and cite the exact command/output.

## Commands
- Backend tests: `cd backend && pytest tests/ -q`
- Frontend type-check: `cd frontend && npm run type-check`
- Frontend tests: `cd frontend && npm run test`
- Frontend build: `cd frontend && npm run build`

## Notes
- Keep secrets out of source control; use `.env` files locally only.
- Do not claim production readiness without verification evidence for security and build quality.

## Documentation References
For more detailed information, consult the project documentation:
- **Contribution Guide**: [`user_contributions.md`](file:///home/Prajesh/sp/user_contributions.md) (onboarding, setup, style rules)
- **System Design & Architecture**: [`design.md`](file:///home/Prajesh/sp/design.md) (system diagrams, pipeline flows)
- **Technical Specification**: [`spec/spec.md`](file:///home/Prajesh/sp/spec/spec.md) (API contract, models)
- **Roadmap & Plan**: [`spec/plan.md`](file:///home/Prajesh/sp/spec/plan.md) (milestones, V1/V2 scope boundaries)
- **Tasks & Backlog**: [`spec/tasks.md`](file:///home/Prajesh/sp/spec/tasks.md) (task management and maintenance checks)
- **Skills Matrix**: [`spec/skills.md`](file:///home/Prajesh/sp/spec/skills.md) (competency matrix and developer guidelines)
