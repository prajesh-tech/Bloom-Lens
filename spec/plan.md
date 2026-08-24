# Project Roadmap & Plan — BloomLens

This document maps out the roadmap, implementation phases, and boundaries separating the features in **BloomLens V1** from future releases.

---

## 1. V1 Implementation Phases

The development of BloomLens is structured into four sequential phases:

```
+------------------------------------+
|  Phase 1: Foundation               |
|  - Relational Database Models      |
|  - File upload API                 |
|  - PyMuPDF & DOCX parsing          |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 2: Core AI Engines          |
|  - 5-Stage Bloom Classifier        |
|  - Gemini API Verification fallback|
|  - FAISS Similarity indexes        |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 3: Web App Integration      |
|  - FastAPI REST Controller endpoints|
|  - React frontend UI Dashboards    |
|  - Recharts visual analytics       |
|  - Human-in-the-Loop review drawer |
+-----------------+------------------+
                  |
                  v
+-----------------+------------------+
|  Phase 4: Quality & Deployment     |
|  - Error boundary handling         |
|  - Full pytest coverage verification|
|  - Frontend TS type-check & builds |
+------------------------------------+
```

- **Phase 1: Foundation**: Set up schemas (SQLAlchemy models), setup Alembic migrations, establish local files storage paths under `/uploads`, write initial unit test templates. Implement `DocumentService` utilizing PyMuPDF and `python-docx`.
- **Phase 2: Core AI Engines**: Integrate standard sentence embeddings via Hugging Face (`all-MiniLM-L6-v2`) and configure localized FAISS vector matching. Build the hybrid classifier combining regex verb checks, semantic similarity, and Google Gemini verification fallback.
- **Phase 3: Web App Integration**: Map out endpoints, connect React frontend pages (`Home`, `Analyze`, `AnalysisResults`, `History`), integrate React Query caching to coordinate queries, and build the custom interactive drawer for human overrides.
- **Phase 4: Quality & Deployment**: Configure CORS, validate settings via Pydantic `BaseSettings`, resolve TypeScript type-checks and Vitest specs, write comprehensive integration tests, compile static production build scripts.

---

## 2. V1 / V2 Scope & Boundaries

To maintain focus and deliver a stable initial version, boundaries have been established:

### Included in V1 (Current Release)
- **Multi-Format Extraction**: PDF/DOCX structure extracting (including OCR fallback for scanned images).
- **Hierarchical Question Mapping**: Preserves parent-child associations for multi-level questions.
- **Marks Validation**: Automated marks extraction, pattern validation, and paper sum matching.
- **Hybrid Cognitive Analysis**: Five stages of NLP checks yielding an effective Bloom level.
- **Duplicate & Semantic Detection**: Identifies exact and semantic repetitions across the historical dataset.
- **Human-in-the-Loop Reviews**: UI interface allowing reviewers to verify and correct AI classifications.

### Excluded (Reserved for V2 Milestone)
- **Course Outcomes (COs) Mapping**: Linking specific questions to Course Outcomes (COs) or Program Outcomes (POs).
- **Attainment Matrices**: Automatically computing academic attainment charts or matrices based on examination results.
- **Student Performance Models**: Predicting exam performance or student grades based on historical question difficulty.
- **Automatic Exam Paper Generation**: AI-driven generation of new question papers or prediction of future exam questions.
