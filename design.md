# System Design & Architecture — BloomLens

This document details the high-level architecture, pipeline flows, and component designs that make up **BloomLens**, an AI-powered historical question-paper analysis system.

---

## 1. High-Level Architecture

BloomLens is structured as a decoupled web application containing:
1. **React 18 & TypeScript Frontend**: Renders analytical charts, list views, and a review drawer using custom badges and monospace typography.
2. **FastAPI Python Backend**: Processes document uploads, parses hierarchical sub-question structures, runs AI models, indexes FAISS vector indices, and serves REST APIs.
3. **Database & File Storage Layer**: Persists structured data inside a relational database (SQLite/MySQL) using SQLAlchemy 2.0 Async ORM and stores uploaded papers inside the local `/uploads` directory.

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
                |       (app.main:app, v1 API)       |
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
|  (Multi-part) |     |  (PyMuPDF/DOCX/ |     |   (Segment Q1/Q1a/Q1b &  |
|               |     |  PaddleOCR fallback)  |    Normalizes Marks)     |
+---------------+     +-----------------+     +------------+-------------+
                                                           |
                                                           v
+---------------+     +-----------------+     +------------+-------------+
| Persistence & | <-- |SimilarityService| <-- |       BloomService       |
| API Response  |     |   (FAISS CPU    |     | (5-Stage Hybrid Classify |
|               |     |  Vector Index)  |     |   + Gemini fallback)     |
+---------------+     +-----------------+     +--------------------------+
```

### Detailed Pipeline Stages:
1. **Upload**: React's upload container drops files via `POST /api/v1/papers/upload`.
2. **Parsing & OCR**: [`document_service.py`](file:///home/Prajesh/sp/backend/app/services/document_service.py) extracts raw text. If a PDF is a scanned image, it triggers the PaddleOCR engine.
3. **Segmentation & Hierarchy**: [`question_extraction_service.py`](file:///home/Prajesh/sp/backend/app/services/question_extraction_service.py) segments parent questions (e.g., `Q1`) and sub-questions (e.g., `Q1(a)`) based on list headers, formatting, and structural regex markers.
4. **Marks Normalization**: Validates exam marks formats (e.g., `[5 marks]`, `2x5=10`), checking whether the sum of questions matches the expected paper maximum marks.
5. **Bloom Classification**: Runs the hybrid classifier model to identify the cognitive Bloom level (L1 Remember to L6 Create).
6. **Vector Search & Similarity**: Enters parsed question texts into the FAISS index using SentenceTransformers (`all-MiniLM-L6-v2`) to detect exact and semantic duplicates across past academic years.
7. **Database Storage**: Writes all records into database tables using the SQLAlchemy async ORM.

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
                   ├─ Confidence >= 0.80 ──> Accept result & store
                   │
                   └─ Confidence <  0.80 ──> Invoke Gemini LLM verification fallback
```

### The 5 Stages:
- **Stage 1: Action Verb Analysis (30%)**: Matches tokenized verbs against a pre-defined Bloom Verb dictionary (e.g., *Define* -> L1, *Analyze* -> L4).
- **Stage 2: Semantic Vector Similarity (35%)**: Generates embedding vectors via `SentenceTransformers` and calculates similarity to anchors representing L1–L6 domains.
- **Stage 3: Cognitive Operation Complexity (25%)**: Evaluates sentence complexity and dependency parsing paths (e.g., *Compare and contrast X and Y* represents a higher complexity than *List X*).
- **Stage 4: Question Structure Analysis (10%)**: Checks syntactic cues like case studies, problem solving prompts, or scenario-based phrasing.
- **Stage 5: Confidence Calculation**: If the combined confidence score drops below `0.80`, the classifier triggers the Google Gemini fallback verification (`google-genai` SDK) to parse the edge-case, providing high-quality classifications.

---

## 4. Similarity & Vector Engine

The vector search module ([`similarity_service.py`](file:///home/Prajesh/sp/backend/app/services/similarity_service.py)) indexes question text into a localized FAISS index:
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions).
- **Exact Matches**: Cosine similarity >= `0.95`.
- **Semantic Repeats**: Cosine similarity between `0.70` and `0.95`.
- **Optimization**: To avoid cold starts, the FAISS engine can warm up embeddings on application startup when `WARMUP_EMBEDDING_ON_STARTUP` is set to `True` in `backend/app/core/config.py`.

---

## 5. Core Data Model (ER relationships)

Our relational database models are organized as follows:
- **`users`**: Academic staff profiles.
- **`subjects`**: Courses/academic modules (e.g., "Data Structures").
- **`question_papers`**: Upload files metadata, validation status, max marks.
- **`bloom_levels`**: Seeded dictionary of L1 (Remember) to L6 (Create) levels.
- **`questions`**: Contains the self-referential `parent_question_id` to build hierarchies (`Q1` -> `Q1a` -> `Q1ai`). Tracks original vs. normalized text, marks, AI-predicted Bloom level, Human-reviewed override Bloom level, and the calculated effective Bloom level.
- **`topics`**: Topic classifications mapping.
- **`question_similarities`**: Records of identical or semantically similar historical questions linking `source_question_id` to `target_question_id` with similarity scores.
