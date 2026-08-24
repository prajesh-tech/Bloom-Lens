# Operational Tasks & Backlog — BloomLens

This document tracks system development status, recurring maintenance activities, and pre-release verification steps.

---

## 1. V1 Development Backlog & Status

The status of the core deliverables in the current release is tracked below:

| Feature / Task | Component | Status |
| --- | --- | --- |
| Database Model & Schema definitions (SQLAlchemy 2.x) | Backend | `[x] Completed` |
| PyMuPDF and DOCX text parser helper logic | Backend | `[x] Completed` |
| PaddleOCR scanning fallback engine | Backend | `[x] Completed` |
| 5-Stage Hybrid Bloom's Taxonomy Classifier | Backend | `[x] Completed` |
| Gemini API edge-case verification fallback | Backend | `[x] Completed` |
| FAISS CPU vector similarity calculation engine | Backend | `[x] Completed` |
| REST API endpoints (`/api/v1`) implementation | Backend | `[x] Completed` |
| Vite + React configuration & TypeScript setup | Frontend | `[x] Completed` |
| Drag & Drop file upload component | Frontend | `[x] Completed` |
| Recharts Bloom distribution donut & bar charts | Frontend | `[x] Completed` |
| Real-time search and Bloom badge pill filters | Frontend | `[x] Completed` |
| Human-in-the-Loop sidebar review/override drawer | Frontend | `[x] Completed` |
| Dual-Mode API Switch (Mock offline vs Live mode) | Frontend | `[x] Completed` |

---

## 2. Recurring Maintenance Tasks

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
- Periodically back up the local database file `bloomlens.db` before applying new schema upgrades.

### Storage Optimization
- Monitor size and storage utilization of the `backend/uploads/` directory to prevent disk space exhaustion from large question paper uploads.
- Implement cleanup scripts to purge temporary mock files or test databases (`test_tmp.db`).

---

## 3. Pre-Release Verification Procedures

Before deploying a release build, the following quality checks must run successfully:

1. **Verify Backend Tests**:
   ```bash
   cd backend
   pytest tests/ -v
   ```
   *Ensure all mocks and FAISS matching test assertions pass.*

2. **Verify Frontend Quality Controls**:
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
   *Ensure that the compiled bundle resolves successfully without warning outputs.*
