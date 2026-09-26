# Operational Tasks & Backlog — BloomLens

This document tracks system development status, recurring maintenance activities, and pre-release verification steps.

---

## 1. V1 Development Backlog & Status

The status of the core deliverables in the current release is tracked below:

| Feature / Task | Component | Status |
| --- | --- | --- |
| Database Model & Schema definitions (SQLAlchemy 2.x Async) | Backend | `[x] Completed` |
| PyMuPDF and DOCX text parser helper logic | Backend | `[x] Completed` |
| PaddleOCR scanning fallback engine with thread-safe lazy loading | Backend | `[x] Completed` |
| 5-Stage Hybrid Bloom's Taxonomy Classifier | Backend | `[x] Completed` |
| Gemini API edge-case verification fallback with 10s timeout | Backend | `[x] Completed` |
| FAISS CPU vector similarity pre-built calculation engine | Backend | `[x] Completed` |
| REST API endpoints (`/api/v1`) with API Key authentication | Backend | `[x] Completed` |
| Database transaction hardening (no auto-commit in `get_db`) | Backend | `[x] Completed` |
| Failed upload file disk cleanup & transaction rollback | Backend | `[x] Completed` |
| Single-query aggregated analytics (N+1 query optimization) | Backend | `[x] Completed` |
| QuestionTopic unique constraint & duplicate link reconciliation | Backend | `[x] Completed` |
| Vite + React configuration & TypeScript setup | Frontend | `[x] Completed` |
| Drag & Drop file upload component | Frontend | `[x] Completed` |
| Recharts Bloom distribution donut & bar charts | Frontend | `[x] Completed` |
| Real-time search and Bloom badge pill filters | Frontend | `[x] Completed` |
| Human-in-the-Loop sidebar review/override drawer | Frontend | `[x] Completed` |
| Dual-Mode API Switch (Mock offline vs Live mode with API Key support) | Frontend | `[x] Completed` |
| Multi-page full question pagination retrieval | Frontend | `[x] Completed` |

---

## 2. V2 Course Outcomes & CO Analytics Backlog & Status

The implementation status for the V2 Course Outcomes roadmap is tracked below:

| Phase | Feature / Task | Component | Status |
| --- | --- | --- | --- |
| **Phase 0** | Discovery & Baseline Verification | Backend / Test | `[x] Completed` |
| **Phase 1** | Domain Models & Migration (`Course`, `CourseOutcome`, `QuestionCourseOutcome`, Alembic) | Backend | `[x] Completed` |
| **Phase 2** | Course & Course Outcome Management API (`CourseService`, schemas, CRUD routes) | Backend | `[x] Completed` |
| **Phase 3** | CO Import Flow (Manual-first CO management, extraction preview & confirmation) | Backend | `[ ] Pending` |
| **Phase 4** | Hybrid CO Mapping Service (Semantic + Concept + Bloom consistency + Gemini fallback) | Backend | `[ ] Pending` |
| **Phase 5** | Question API & Human Review Extensions (CO mappings, review status, override audit) | Backend | `[ ] Pending` |
| **Phase 6** | CO Analytics Engine (`co-distribution`, `co-bloom`, `co-trends`, `co-coverage`, `topic-co`) | Backend | `[ ] Pending` |
| **Phase 7** | Configuration, Error Handling & Security (Pydantic settings, sanitization, validation) | Backend | `[ ] Pending` |
| **Phase 8** | Comprehensive Test Suite (Models, services, mock fallbacks, analytics validation) | Backend / Test | `[ ] Pending` |
| **Phase 9** | Documentation & Cleanliness Audit (`README.md`, `design.md`, `spec/*`) | Docs | `[ ] Pending` |


---

## 3. Recurring Maintenance Tasks

To keep the application stable, developers should regularly execute these actions:

### Dependency Audits & Updates
- **Backend**: Inspect packages for vulnerabilities and security updates:
  ```bash
  pip list --outdated
  ```
- **Frontend**: Check and resolve package vulnerabilities:
  ```bash
  npm audit
  npm audit fix
  ```

### Database Maintenance
- Review migration history with Alembic:
  ```bash
  alembic history --verbose
  ```
- Back up database before applying new schema upgrades.

### Storage Optimization
- Monitor size and storage utilization of the `backend/uploads/` directory to prevent disk space exhaustion.

---

## 4. Pre-Release Verification Procedures

Before deploying a release build, the following quality checks must run successfully:

1. **Verify Backend Tests** (35 tests):
   ```bash
   cd backend
   pytest tests/ -v
   ```
   *Ensures all document extractions, Bloom classification, authentication, transactions, cleanup, and similarity matching tests pass.*

2. **Verify Frontend Quality Controls** (12 tests):
   ```bash
   cd frontend
   npm run type-check   # Validate TypeScript types
   npm run lint         # Check style standards via ESLint
   npm run test         # Run unit tests (Vitest)
   ```

3. **Verify Production Compilation**:
   ```bash
   cd frontend
   npm run build
   ```
   *Ensure that the compiled bundle resolves successfully without errors.*
