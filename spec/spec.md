# Technical Specification — BloomLens

This document details the technical requirements, constraints, API specifications, and database entity models for **BloomLens V1**.

---

## 1. Input & Output Formats

### Document Inputs
- **Supported Formats**: Native PDF (`.pdf`), Scanned PDF (`.pdf`), Microsoft Word (`.docx`).
- **File Constraints**: Maximum size is 20MB (default configure via `MAX_UPLOAD_SIZE_MB` in settings).
- **Processing Capabilities**:
  - **Native PDF**: Text and layout extraction via PyMuPDF (`fitz`).
  - **Scanned PDF**: Image extraction and OCR processing via the PaddleOCR engine.
  - **DOCX**: Element structure and text extraction via `python-docx`.

### Data Outputs
- **Question Hierarchy**: A JSON representation tree showing main questions (e.g., `Q1`, `Q2`) and sub-questions (e.g., `Q1(a)`, `Q1(b)`).
- **Taxonomy Mapping**: Every question is annotated with an AI-classified Bloom level (`L1` to `L6`), a confidence score (`0.00` to `1.00`), and explainability logs detailing why the classification was selected.
- **Vector Indexing**: Question texts are indexed as 384-dimensional dense vectors using FAISS.

---

## 2. API Contract Specification

All routes are served under `/api/v1`.

### System Health
- **`GET /api/v1/health`**
  - **Description**: Returns server running status and database connectivity.
  - **Response**:
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "timestamp": "2026-08-24T16:00:00Z"
    }
    ```

### Question Papers Management
- **`POST /api/v1/papers/upload`**
  - **Payload**: `multipart/form-data` with keys:
    - `file`: Binary file.
    - `subject_id`: Integer (associated course).
    - `exam_year`: Integer (e.g. 2025).
    - `exam_type`: String (e.g. "MID_TERM", "END_SEM").
  - **Response**: The created `QuestionPaper` object containing processing status.

- **`GET /api/v1/papers`**
  - **Query Parameters**: `page` (int), `limit` (int).
  - **Response**: Paginated list of uploaded question papers.

- **`GET /api/v1/papers/{id}/status`**
  - **Description**: Poll processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
  - **Response**:
    ```json
    {
      "id": 1,
      "status": "COMPLETED",
      "validation_error": null
    }
    ```

### Question Queries & Review
- **`GET /api/v1/questions`**
  - **Query Parameters**: `paper_id` (int), `bloom_level_id` (int), `search` (str), `page` (int), `limit` (int).
  - **Response**: List of matching questions.

- **`PATCH /api/v1/questions/{id}`**
  - **Description**: Applied by reviewers to override details (Human-in-the-Loop review).
  - **Payload**:
    ```json
    {
      "marks": 5.0,
      "bloom_level_id": 3,
      "question_type": "Analytical",
      "topic": "Binary Search Trees",
      "unit": "Unit II"
    }
    ```
  - **Response**: The updated question instance.

### Analytics Endpoints
- **`GET /api/v1/analytics/overview`**
  - **Response**: Macro stats (`total_papers`, `total_questions`, `total_marks`, `duplicate_questions_count`).
- **`GET /api/v1/analytics/bloom`**
  - **Response**: Distribution metrics counting count-based and marks-weighted Bloom level ratios.
- **`GET /api/v1/analytics/topics`**
  - **Response**: Frequencies of classified syllabus topics.
- **`GET /api/v1/analytics/trends`**
  - **Response**: Historical cognitive levels change graph data grouped by academic year.

---

## 3. Database Schema Specification

Below is the database table schema mapped via SQLAlchemy 2.x models:

### Table: `bloom_levels`
- `id` (int, PK)
- `code` (str, unique) - e.g., "L1", "L2"
- `name` (str) - e.g., "Remember", "Understand"
- `description` (text)

### Table: `questions`
- `id` (int, PK)
- `question_paper_id` (int, FK -> `question_papers.id`)
- `parent_question_id` (int, FK -> `questions.id`, Nullable)
- `question_number` (str) - e.g., "Q1(a)"
- `original_text` (text)
- `normalized_text` (text)
- `marks` (float)
- `marks_confidence` (str) - "high", "medium", "low"
- `ai_bloom_level_id` (int, FK -> `bloom_levels.id`)
- `human_bloom_level_id` (int, FK -> `bloom_levels.id`, Nullable)
- `effective_bloom_level_id` (int, FK -> `bloom_levels.id`) - *Calculated as: human override value if present, else AI value.*
- `bloom_confidence` (float)
- `bloom_explanation` (text)
- `review_status` (str) - "AUTO_CLASSIFIED", "REVIEWED", "CORRECTED", "FLAGGED"
- `unit` (str, Nullable)
- `choice_group` (str, Nullable) - Group identifier for optional choices.

### Table: `question_similarities`
- `id` (int, PK)
- `source_question_id` (int, FK -> `questions.id`)
- `target_question_id` (int, FK -> `questions.id`)
- `similarity_score` (float) - Cosine similarity calculated by SentenceTransformers & FAISS.
- `match_type` (str) - "EXACT", "SEMANTIC"
