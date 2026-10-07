# Project Roadmap & Plan — BloomLens

This document maps out the roadmap, implementation phases, and boundaries separating the features in **BloomLens V1** from future releases.

---

## 1. V1 Implementation Phases

The development of BloomLens is structured into four sequential phases:

```
+------------------------------------+
|  Phase 1: Foundation               |
|  - Relational Database Models      |
|  - File upload API & Validation    |
|  - PyMuPDF & DOCX parsing          |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 2: Core AI Engines          |
|  - 5-Stage Bloom Classifier        |
|  - Gemini API Fallback (10s timeout)|
|  - Thread-Safe Lazy Model Loaders  |
|  - FAISS Similarity Indexes        |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 3: Web App Integration      |
|  - FastAPI REST Controllers & Auth |
|  - React frontend UI Dashboards    |
|  - Recharts visual analytics       |
|  - Human-in-the-Loop review drawer |
|  - Multi-page question pagination  |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 4: Quality & Hardening      |
|  - API Key & Bearer Authentication |
|  - DB Transaction Integrity        |
|  - Failed Upload File Disk Cleanup |
|  - Single-Query Analytics (No N+1) |
|  - 35 Pytest & 12 Vitest suites    |
|  - Frontend TS type-check & builds |
+------------------------------------+
```

- **Phase 1: Foundation**: Set up schemas (SQLAlchemy models), setup Alembic migrations, establish local files storage paths under `/uploads`, write initial unit test templates. Implement `DocumentService` utilizing PyMuPDF and `python-docx`.
- **Phase 2: Core AI Engines**: Integrate standard sentence embeddings via Hugging Face (`all-MiniLM-L6-v2`) and configure localized FAISS vector matching. Build the hybrid classifier combining regex verb checks, semantic similarity, and bounded Google Gemini verification fallback with thread-safe double-checked caching.
- **Phase 3: Web App Integration**: Map out endpoints, connect React frontend pages (`Home`, `Analyze`, `AnalysisResults`, `History`), integrate React Query caching to coordinate queries, build the custom interactive drawer for human overrides, and implement complete multi-page pagination.
- **Phase 4: Quality & Hardening**: Configure API Key authentication (`app/core/auth.py`), remove auto-commit from `get_db()`, clean up orphaned files on failed upload, optimize analytics queries, resolve TypeScript type-checks and Vitest specs, write comprehensive integration tests, compile static production build scripts.

---

## 2. V1 / V2 Scope & Boundaries

To maintain focus and deliver a stable initial version, boundaries have been established:

### Included in V1 (Current Release)
- **Multi-Format Extraction**: PDF/DOCX structure extracting (including OCR fallback for scanned images).
- **Hierarchical Question Mapping**: Preserves parent-child associations for multi-level questions.
- **Marks Validation**: Automated marks extraction, pattern validation, and paper sum matching.
- **Hybrid Cognitive Analysis**: Five stages of NLP checks yielding an effective Bloom level.
- **Duplicate & Semantic Detection**: Identifies exact and semantic repetitions across the historical dataset.
- **Human-in-the-Loop Reviews**: UI interface allowing reviewers to verify and correct AI classifications with atomic topic updates.
- **Estimated Student Performance Heuristic**: Pure deterministic projection of estimated pass percentage and average marks computed solely from the paper's marks-weighted Bloom's Taxonomy distribution (never actual student statistics; does not pull forward V2 Student Performance Analytics).
- **Security & Reliability Hardening**: API key authentication, bounded Gemini timeouts, thread-safe model caching, explicit database transactions, and disk cleanup.

### Excluded (Reserved for V2 Milestone)
- **Course Outcomes (COs) Mapping**: Linking specific questions to Course Outcomes (COs) or Program Outcomes (POs).
- **Attainment Matrices**: Automatically computing academic attainment charts or matrices based on examination results.
- **Student Performance Models (Empirical/Cohort)**: Full empirical student response modeling, actual student marks/cohort records, and evaluator factor modeling.
- **Automatic Exam Paper Generation**: AI-driven generation of new question papers or prediction of future exam questions.
