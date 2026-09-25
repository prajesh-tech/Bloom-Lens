# BloomLens V1 System Architecture

This document provides a comprehensive architectural guide for **BloomLens V1**, an AI-powered historical question-paper analysis system.

---

## 1. System Overview

BloomLens analyzes historical examination question papers (PDF & DOCX) to answer:
> **What has been asked historically, how frequently has it been asked, and at what cognitive level has it been asked?**

The system consists of two primary components:
1. **React + TypeScript Frontend**: An interactive analytical web user interface.
2. **FastAPI Python Backend**: A service-oriented AI/NLP backend executing document parsing, hybrid Bloom taxonomy classification, FAISS vector search, and metric aggregation.

---

## 2. High-Level Architecture

```mermaid
flowchart TD
    User([User / Instructor])

    subgraph Frontend["React 18 + TypeScript Frontend"]
        UI[React UI Pages]
        State[Component & Router State]
        API_Layer[Dual-Mode API Layer]
        Mock[Mock Engine & Latency Simulator]
    end

    subgraph Backend["FastAPI Backend Services"]
        REST[REST API Controllers /api/v1/]
        DocProc[Document Processor: PyMuPDF / docx / PaddleOCR]
        QExtract[Question Extraction & Marks Validation]
        BloomClassifier[5-Stage Hybrid Bloom Classifier]
        Gemini[Google Gemini Verification Fallback]
        Similarity[FAISS CPU Vector Similarity Engine]
        Analytics[Analytics Aggregator]
    end

    subgraph DatabaseLayer["Data & Persistence"]
        DB[(MySQL 8 / SQLite)]
        Storage[(File Storage /uploads)]
    end

    User --> UI
    UI --> API_Layer
    API_Layer -- VITE_USE_MOCK_API=true --> Mock
    API_Layer -- VITE_USE_MOCK_API=false --> REST

    REST --> DocProc
    DocProc --> Storage
    DocProc --> QExtract
    QExtract --> BloomClassifier
    BloomClassifier -- Confidence < 0.80 --> Gemini
    BloomClassifier --> Similarity
    QExtract --> DB
    BloomClassifier --> DB
    Similarity --> DB
    Analytics --> DB
    REST <-- Analytics
```

---

## 3. Frontend Architecture

The frontend follows a layered component-driven architecture:

```text
Pages (Route Level Composition)
   ↓
Reusable Components (UI & Visualizations)
   ↓
Custom Hooks & State Management
   ↓
Service/API Layer (Dual-Mode Axios / Mock)
   ↓
Backend API (/api/v1/)
```

### Layer Responsibilities
- **Pages**: Top-level route containers (`Home`, `Analyze`, `AnalysisResults`, `History`, `Settings`).
- **Components**: Reusable UI primitives (`Button`, `Badge`, `BloomBadge`, `Card`, `Drawer`, `Skeleton`, `Toast`) and visualization modules (`BloomDonutChart`, `BloomBarChart`, `QuestionTable`, `QuestionFilterBar`, `QuestionDrawer`).
- **Services**: Encapsulated network communication (`api.ts`, `analysisApi.ts`, `historyApi.ts`) and mock data provider (`mockData.ts`).
- **Config**: Centralized Bloom Taxonomy design tokens (`bloomConfig.ts`).
- **Types**: Strict TypeScript domain models (`bloom.ts`, `paper.ts`, `question.ts`, `analytics.ts`).

---

## 4. Backend Architecture

The backend is built as a modular service-oriented architecture:

```text
FastAPI API Routes (/api/v1/)
    ↓
Validation Schemas (Pydantic v2)
    ↓
Business Services
    ├── Document Processing (PyMuPDF, python-docx, PaddleOCR)
    ├── Question Extraction & Marks Normalization
    ├── Hybrid Bloom Taxonomy Classifier
    ├── FAISS Similarity Engine
    └── Analytics Aggregator
    ↓
Database Access Layer (SQLAlchemy 2.x Async ORM)
    ↓
Persistence (MySQL 8 / SQLite)
```

---

## 5. End-to-End Question Paper Pipeline Flow

```text
1. User uploads PDF/DOCX paper via React Dropzone
2. Frontend sends multipart/form-data to POST /api/v1/papers/upload
3. FastAPI saves original file to /uploads directory
4. DocumentService extracts text (PyMuPDF for PDF, python-docx for DOCX, PaddleOCR fallback for scanned PDFs)
5. QuestionExtractionService segments main questions (Q1, Q2) & sub-questions (Q1a, Q1b)
6. MarksService normalizes marks notation ([5 Marks], 2x5=10, 5+5)
7. Paper marks validator checks maximum paper marks vs sum of extracted marks
8. TopicService identifies primary unit and topic
9. BloomService runs 5-stage hybrid classifier (Verb 30%, Semantic 35%, Cognitive 25%, Structure 10%)
10. If confidence < 0.80, calls Google Gemini SDK fallback for verification
11. SimilarityService indexes questions into FAISS CPU vector index for duplicate detection
12. Database entities persisted via SQLAlchemy 2.x
13. Frontend renders interactive results dashboard with charts, table, and inspect drawer
```

---

## 6. Bloom’s Taxonomy Classification Flow

```text
Question Text
   ↓
[Stage 1: Action Verb Analysis (30%)] ──> Verb Dictionary Match
   ↓
[Stage 2: Semantic Vector Similarity (35%)] ──> SentenceTransformers (all-MiniLM-L6-v2) vs Anchor Vectors
   ↓
[Stage 3: Cognitive Operation Hierarchy (25%)] ──> Target Task Complexity Analysis
   ↓
[Stage 4: Question Structure Analysis (10%)] ──> Architectural & Synthesis Cues
   ↓
[Stage 5: Weighted Aggregation & Confidence Calculation]
   ↓
Confidence >= 0.80 ──> Accept Hybrid Classification Result
Confidence < 0.80  ──> Google Gemini SDK Verification Fallback
   ↓
Store Primary Bloom Level (L1-L6), Confidence, and Explainability JSON
```

---

## 7. API Architecture
 
All endpoints reside under `/api/v1/`:

| Method | Endpoint | Description | Auth Required |
| ------ | -------- | ----------- | ------------- |
| `GET` | `/api/v1/health` | Health check & DB status | No |
| `GET` | `/api/v1/health/deep` | Deep subsystem health check | No |
| `POST` | `/api/v1/papers/upload` | Upload & analyze paper | Yes |
| `GET` | `/api/v1/papers` | Paginated paper history list | No |
| `GET` | `/api/v1/papers/{id}` | Get paper details | No |
| `GET` | `/api/v1/papers/{id}/status` | Poll paper processing status | No |
| `DELETE` | `/api/v1/papers/{id}` | Delete paper and cascade questions | Yes |
| `GET` | `/api/v1/questions` | Search, filter & paginate questions | No |
| `GET` | `/api/v1/questions/{id}` | Single question detail & sub-questions | No |
| `PATCH` | `/api/v1/questions/{id}` | Human review & classification override | Yes |
| `GET` | `/api/v1/analytics/overview` | Macro overview statistics | Yes |
| `GET` | `/api/v1/analytics/bloom` | Question-count & marks-weighted Bloom distributions | Yes |
| `GET` | `/api/v1/analytics/topics` | Topic frequency analytics | Yes |
| `GET` | `/api/v1/analytics/trends` | Historical cognitive Bloom level trends | Yes |

---

## 8. Data Models

### Database Entities (SQLAlchemy)
- `subjects`: Academic subjects/courses.
- `question_papers`: Upload metadata, exam type, maximum marks, processing status, validation metadata.
- `bloom_levels`: Seeded L1 (Remember) to L6 (Create) levels with keywords.
- `questions`: Main/sub-question self-referential hierarchy, original/normalized text, marks, AI vs Human vs Effective Bloom level, AI analysis explainability JSON.
- `topics` & `question_topics`: Topic classification with unique question-topic constraints.
- `question_similarities`: Exact and semantic repeat tracking.

---

## 9. Security Architecture

- **API Authentication**: Sensitive endpoints (paper upload/deletion, question override PATCH, and analytics routes) are protected via FastAPI dependency authentication using `X-API-Key` or `Authorization: Bearer <token>` verified with constant-time comparison (`secrets.compare_digest`).
- **Transactional Integrity**: Database sessions yield without auto-committing, guaranteeing automatic rollback on exceptions. Write routes commit explicitly, while read routes execute without write transactions. Failed file uploads clean up orphaned files from disk.
- **Thread-Safe AI Engines**: Lazy-initialized ML/NLP services (OCR engine, embedding transformer, anchor vectors) use thread-safe double-checked locking to prevent race conditions during concurrent request processing.
- **Backend Isolation**: Gemini API keys, API authentication tokens, and database credentials reside exclusively in backend environment variables.
- **Input Sanitization**: File type validation, maximum upload size constraints, supported exam types validation, and SQL parameterization via SQLAlchemy ORM.
- **Safe Error Responses**: Health check endpoints and API error handlers return sanitized JSON without exposing raw database connection exceptions or internal filesystem paths.

---

## 10. Future V2 Extension Points

The architecture cleanly supports future V2 extensions without restructuring V1 code:
- **Course Outcomes (COs)**: Adding `course_outcomes` and `question_course_outcomes` tables.
- **CO-PO Attainment Matrices**: Linking Bloom levels to program outcomes.
- **Student Performance Analytics**: Student response modeling.

---

## 11. Documentation & Design Reference

For guides on how to setup, run, and modify this project:
- **System Design & Architecture**: [`design.md`](file:///home/Prajesh/sp/design.md) (comprehensive system-wide architecture and design patterns)
- **Developer Contribution Guide**: [`user_contributions.md`](file:///home/Prajesh/sp/user_contributions.md) (setup, workflows, and PR standards)
- **Technical Specification**: [`spec/spec.md`](file:///home/Prajesh/sp/spec/spec.md)
- **Roadmap & Plan**: [`spec/plan.md`](file:///home/Prajesh/sp/spec/plan.md)
- **Tasks & Backlog**: [`spec/tasks.md`](file:///home/Prajesh/sp/spec/tasks.md)
- **Skills Matrix**: [`spec/skills.md`](file:///home/Prajesh/sp/spec/skills.md)
