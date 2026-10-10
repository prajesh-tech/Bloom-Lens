# System Design & Architecture — BloomLens

This document details the high-level architecture, pipeline flows, and component designs that make up **BloomLens**, an AI-powered historical question-paper analysis system.

For frontend-specific component and state-management details, see [Frontend Architecture](./frontend/ARCHITECTURE.md).

---

## 1. High-Level Architecture

BloomLens is structured as a decoupled web application containing:
1. **React 18 & TypeScript Frontend**: Renders analytical charts, list views, and a review drawer using custom badges and monospace typography. It does not contain shared server credentials.
2. **FastAPI Python Backend**: Processes document uploads, parses hierarchical sub-question structures, runs thread-safe AI models, indexes FAISS vector indices, and serves REST APIs with configurable API-key authentication.
3. **Database & File Storage Layer**: Persists structured data inside a relational database (SQLite/MySQL) using SQLAlchemy 2.0 Async ORM with explicit transaction boundaries, and stores uploaded papers inside the local `/uploads` directory.

```
                +------------------------------------+
                |          User Interface            |
                |   (React 18 + TS + Tailwind CSS)   |
                +-----------------+------------------+
                                  |
               REST API calls     | (Axios / Mock Mode)
                                  v
                +-----------------+------------------+
                |          FastAPI Backend           |
                |   (app.main:app, v1 API + Auth)    |
                +--------+------------------+--------+
                         |                  |
    Saves raw files      |                  | Reads/Writes entities
    to local storage     v                  v (SQLAlchemy 2.x ORM)
                  +------+---+      +-------+--------+
                  | /uploads |      | Relational DB  |
                  | Folder   |      | SQLite/MySQL 8 |
                  +----------+      +----------------+
```

## 2. Core API Endpoints

All endpoints are served under `/api/v1`. Mutating and analytics endpoints depend on backend API-key authentication when `AUTH_ENABLED=true`. The browser frontend does not contain or send a shared API key; authenticated browser actions require a trusted server-side integration.

| Method | Endpoint | Description | Auth required |
| --- | --- | --- | --- |
| `GET` | `/health` | Liveness check | No |
| `GET` | `/health/deep` | Database and subsystem health details | No |
| `POST` | `/papers/upload` | Upload and analyze a paper | Yes |
| `GET` | `/papers` | Paginated paper history | No |
| `GET` | `/papers/{id}` | Paper details | No |
| `GET` | `/papers/{id}/status` | Processing status | No |
| `GET` | `/papers/{id}/performance-estimate` | Heuristic performance estimate | No |
| `DELETE` | `/papers/{id}` | Delete a paper | Yes |
| `GET` | `/questions` | Search and paginate questions | No |
| `GET` | `/questions/{id}` | Question details | No |
| `PATCH` | `/questions/{id}` | Human question override | Yes |
| `GET` | `/analytics/overview` | Summary analytics | Yes |
| `GET` | `/analytics/bloom` | Bloom level distribution | Yes |
| `GET` | `/analytics/topics` | Topic analytics | Yes |
| `GET` | `/analytics/questions` | Question analytics | Yes |
| `GET` | `/analytics/trends` | Historical Bloom trends | Yes |

---

## 3. End-to-End Processing Pipeline

When a user uploads a PDF or DOCX file, it travels through the following sequence of backend services:

```
+---------------+     +-----------------+     +--------------------------+
|  File Upload  | --> | DocumentService | --> | QuestionExtractionService|
|  (Multi-part  |     |  (PyMuPDF/DOCX/ |     |   (Segment Q1/Q1a/Q1b &  |
|  + Auth)      |     |  PaddleOCR)     |     |    Normalizes Marks)     |
+---------------+     +-----------------+     +------------+-------------+
                                                           |
                                                           v
+---------------+     +-----------------+     +------------+-------------+
| Persistence & | <-- |SimilarityService| <-- |       BloomService       |
| API Response  |     |   (FAISS CPU    |     | (5-Stage Hybrid Classify |
| (Auto-clean)  |     |  Vector Index)  |     |  + Gemini 10s timeout)   |
+---------------+     +-----------------+     +--------------------------+
```

### Detailed Pipeline Stages:
1. **Upload & Auth Validation**: Uploads use `POST /api/v1/papers/upload`. When backend authentication is enabled, requests must come from a trusted server-side integration; the browser does not send a shared API key.
2. **Parsing & OCR**: [`document_service.py`](./backend/app/services/document_service.py) extracts raw text with thread-safe lazy PaddleOCR engine initialization.
3. **Segmentation & Hierarchy**: [`question_extraction_service.py`](./backend/app/services/question_extraction_service.py) segments parent questions (e.g., `Q1`) and sub-questions (e.g., `Q1(a)`) based on list headers, formatting, and structural regex markers.
4. **Marks Normalization & Validation**: Validates exam marks formats and checks paper maximum marks against extracted sums.
5. **Bloom Classification**: Runs the hybrid classifier model with thread-safe anchor vector caching and bounded 10-second timeout on Gemini fallback.
6. **Vector Search & Similarity**: Compares questions against the corpus using SentenceTransformers (`all-MiniLM-L6-v2`) and FAISS to detect exact and semantic duplicates.
7. **Database Storage & Cleanup**: Explicitly commits transaction on success. On failure, rolls back database state and removes any orphaned temporary files from disk.

---

## 4. Hybrid Bloom's Taxonomy Classifier

BloomLens utilizes a 5-Stage Hybrid Classifier to determine cognitive levels under the Revised Bloom's Taxonomy. It calculates a weighted confidence score based on multiple NLP checks:

```
  Stage 1: Action Verb Analysis (30%)
  Stage 2: Semantic Vector Similarity (35%)
  Stage 3: Cognitive Operation Complexity (25%)
  Stage 4: Question Structure Cues (10%)
                   │
                   ▼
       [ Weighted Aggregation ]
                   │
                   ├─ Confidence >= 0.60 ──> Accept result & store
                   │
                   └─ Confidence <  0.60 ──> Invoke Gemini LLM verification fallback (10s timeout)
```

### The 5 Stages:
- **Stage 1: Action Verb Analysis (30%)**: Matches tokenized verbs against the Bloom Verb dictionary.
- **Stage 2: Semantic Vector Similarity (35%)**: Generates embedding vectors via `SentenceTransformers` and calculates cosine similarity to anchor vectors (thread-safely cached).
- **Stage 3: Cognitive Operation Complexity (25%)**: Evaluates cognitive operation hierarchy (Recall -> Understand -> Apply -> Analyze -> Evaluate -> Create).
- **Stage 4: Question Structure Analysis (10%)**: Analyzes architectural, synthesis, case study, and problem solving cues.
- **Stage 5: Confidence Calculation & Verification**: If combined confidence drops below threshold, triggers Google Gemini SDK (`gemini-2.5-flash`) with a 10.0-second timeout.

---

## 5. Similarity & Vector Engine

The vector search module ([`similarity_service.py`](./backend/app/services/similarity_service.py)) indexes question text into a localized FAISS index:
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions), thread-safely initialized.
- **Exact Matches**: Cosine similarity >= `0.95`.
- **Semantic Repeats**: Cosine similarity between `0.70` and `0.95`.
- **Optimization**: Pre-computed vectors passed directly to `find_similar_questions_prebuilt` to prevent redundant embedding calculations.

---

## 6. Core Data Model (ER relationships)

Our relational database models are organized as follows:
- **`subjects`**: Courses/academic modules (e.g., "Data Structures").
- **`question_papers`**: Upload files metadata, exam type, validation status, max marks.
- **`bloom_levels`**: Seeded dictionary of L1 (Remember) to L6 (Create) levels.
- **`questions`**: Self-referential `parent_question_id` to build hierarchies (`Q1` -> `Q1a`). Tracks original vs. normalized text, marks, AI-predicted Bloom level, Human-reviewed override Bloom level, and effective Bloom level.
- **`topics`**: Topic classifications mapping.
- **`question_topics`**: Association table linking questions to topics with a unique constraint on `(question_id, topic_id)`.
- **`question_similarities`**: Records of identical or semantically similar historical questions linking `source_question_id` to `target_question_id`.

---

## 7. Estimated Student Performance Design

BloomLens computes heuristic projections of student pass percentage and average marks on demand for completed question papers without storing estimates in the database.

> [!NOTE]
> Values are heuristic estimates derived solely from the question paper's Bloom's Taxonomy and marks distribution, not actual student statistics. This read-time feature does not pull forward V2 "Student Performance Analytics".

### Architectural Design
- **Read-Time Derivation**: Computed in [`performance_estimation_service.py`](./backend/app/services/performance_estimation_service.py) on `GET /api/v1/papers/{id}/performance-estimate`. Automatically reflects human overrides without database migration or persisting redundant fields.
- **Leaf-Level Scoring**: Uses only leaf questions (sub-questions or parent questions without sub-questions) matching the marks-weighted analytics rule to prevent double counting parent container marks.
- **Paper Difficulty ($D$)**:
  $$D = \frac{\sum_{i \in \text{valid}} (\text{marks}_i \times w(\text{level}_i))}{\sum_{i \in \text{valid}} \text{marks}_i}$$
- **Linear Clamped Projections**:
  - $\text{Estimated Pass \%} = \text{clamp}(95.0 - 65.0 \times D, 0, 100)$
  - $\text{Estimated Avg \%} = \text{clamp}(80.0 - 50.0 \times D, 0, 100)$
  - $\text{Estimated Average Marks} = \frac{\text{Estimated Avg \%}}{100} \times \text{maximum\_marks}$
- **Configurability**: Configured in [`backend/app/core/config.py`](./backend/app/core/config.py):
  - Difficulty weights: `ESTIMATE_BLOOM_WEIGHT_L1` (0.10) to `L6` (1.00)
  - Mapping slopes and intercepts: `ESTIMATE_PASS_PCT_INTERCEPT`, `ESTIMATE_PASS_PCT_SLOPE`, `ESTIMATE_AVG_PCT_INTERCEPT`, `ESTIMATE_AVG_PCT_SLOPE`
  - Exclusion threshold: `ESTIMATE_MAX_EXCLUDED_MARKS_RATIO` (default 0.20 / 20%). Returns unavailable (`too_many_excluded`) if excluded marks exceed threshold.
