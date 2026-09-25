# System Design & Architecture — BloomLens

This document details the high-level architecture, pipeline flows, and component designs that make up **BloomLens**, an AI-powered historical question-paper analysis system.

---

## 1. High-Level Architecture

BloomLens is structured as a decoupled web application containing:
1. **React 18 & TypeScript Frontend**: Renders analytical charts, list views, and a review drawer using custom badges and monospace typography. Connects via Axios with `X-API-Key` authentication support.
2. **FastAPI Python Backend**: Processes document uploads, parses hierarchical sub-question structures, runs thread-safe AI models, indexes FAISS vector indices, enforces API key authentication, and serves REST APIs.
3. **Database & File Storage Layer**: Persists structured data inside a relational database (SQLite/MySQL) using SQLAlchemy 2.0 Async ORM with explicit transaction boundaries, and stores uploaded papers inside the local `/uploads` directory.

```
                +------------------------------------+
                |          User Interface            |
                |   (React 18 + TS + Tailwind CSS)   |
                +-----------------+------------------+
                                  |
               REST API calls     | (Axios / Mock Mode)
             + X-API-Key Auth     v
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

---

## 2. End-to-End Processing Pipeline

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
1. **Upload & Auth Validation**: React's upload container sends files via `POST /api/v1/papers/upload` authenticated via `X-API-Key` or Bearer token.
2. **Parsing & OCR**: [`document_service.py`](file:///home/Prajesh/sp/backend/app/services/document_service.py) extracts raw text with thread-safe lazy PaddleOCR engine initialization.
3. **Segmentation & Hierarchy**: [`question_extraction_service.py`](file:///home/Prajesh/sp/backend/app/services/question_extraction_service.py) segments parent questions (e.g., `Q1`) and sub-questions (e.g., `Q1(a)`) based on list headers, formatting, and structural regex markers.
4. **Marks Normalization & Validation**: Validates exam marks formats and checks paper maximum marks against extracted sums.
5. **Bloom Classification**: Runs the hybrid classifier model with thread-safe anchor vector caching and bounded 10-second timeout on Gemini fallback.
6. **Vector Search & Similarity**: Compares questions against the corpus using SentenceTransformers (`all-MiniLM-L6-v2`) and FAISS to detect exact and semantic duplicates.
7. **Database Storage & Cleanup**: Explicitly commits transaction on success. On failure, rolls back database state and removes any orphaned temporary files from disk.

---

## 3. Hybrid Bloom's Taxonomy Classifier

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

## 4. Similarity & Vector Engine

The vector search module ([`similarity_service.py`](file:///home/Prajesh/sp/backend/app/services/similarity_service.py)) indexes question text into a localized FAISS index:
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions), thread-safely initialized.
- **Exact Matches**: Cosine similarity >= `0.95`.
- **Semantic Repeats**: Cosine similarity between `0.70` and `0.95`.
- **Optimization**: Pre-computed vectors passed directly to `find_similar_questions_prebuilt` to prevent redundant embedding calculations.

---

## 5. Core Data Model (ER relationships)

Our relational database models are organized as follows:
- **`subjects`**: Courses/academic modules (e.g., "Data Structures").
- **`question_papers`**: Upload files metadata, exam type, validation status, max marks.
- **`bloom_levels`**: Seeded dictionary of L1 (Remember) to L6 (Create) levels.
- **`questions`**: Self-referential `parent_question_id` to build hierarchies (`Q1` -> `Q1a`). Tracks original vs. normalized text, marks, AI-predicted Bloom level, Human-reviewed override Bloom level, and effective Bloom level.
- **`topics`**: Topic classifications mapping.
- **`question_topics`**: Association table linking questions to topics with a unique constraint on `(question_id, topic_id)`.
- **`question_similarities`**: Records of identical or semantically similar historical questions linking `source_question_id` to `target_question_id`.
