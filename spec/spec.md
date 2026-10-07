# Technical Specification — BloomLens

This document details the technical requirements, constraints, API specifications, and database entity models for **BloomLens V1**.

---

## 1. Input & Output Formats

### Document Inputs
- **Supported Formats**: Native PDF (`.pdf`), Scanned PDF (`.pdf`), Microsoft Word (`.docx`).
- **File Constraints**: Maximum size is 20MB (default configure via `MAX_UPLOAD_SIZE_MB` in settings).
- **Exam Types**: Enforced against `SUPPORTED_EXAM_TYPES` ("Mid-Term", "Internal", "Unit Test", "End-Semester", "Model Examination", "Quiz", "Other").
- **Processing Capabilities**:
  - **Native PDF**: Text and layout extraction via PyMuPDF (`fitz`).
  - **Scanned PDF**: Image extraction and OCR processing via the PaddleOCR engine.
  - **DOCX**: Element structure and text extraction via `python-docx`.

### Data Outputs
- **Question Hierarchy**: A JSON representation tree showing main questions (e.g., `Q1`, `Q2`) and sub-questions (e.g., `Q1(a)`, `Q1(b)`).
- **Taxonomy Mapping**: Every question is annotated with an AI-classified Bloom level (`L1` to `L6`), a confidence score (`0.00` to `1.00`), and explainability logs detailing why the classification was selected.
- **Vector Indexing**: Question texts are indexed as 384-dimensional dense vectors using FAISS.

---

## 2. API Contract & Security Specification

All routes are served under `/api/v1`. Sensitive write and analytics endpoints require authentication via `X-API-Key: <key>` header or `Authorization: Bearer <key>`.

### Authentication & Authorization
- **Dependency**: `get_current_user` in [`app/core/auth.py`](file:///home/Prajesh/sp/backend/app/core/auth.py).
- **Status Codes**: Returns `401 Unauthorized` for missing/invalid keys; `403 Forbidden` for insufficient role permissions.

### System Health (Public)
- **`GET /api/v1/health`**
  - **Description**: Returns server online status and API version.
- **`GET /api/v1/health/deep`**
  - **Description**: Returns database health status (`"healthy"` / `"unhealthy"`), embedding backend status, and metric snapshots without leaking internal error strings.

### Question Papers Management
- **`POST /api/v1/papers/upload`** *(Authenticated)*
  - **Payload**: `multipart/form-data` with keys:
    - `file`: Binary `.pdf` or `.docx` file.
    - `subject_code`: String (e.g., "CS301").
    - `subject_name`: String (e.g., "Database Systems").
    - `examination_type`: String (one of `SUPPORTED_EXAM_TYPES`).
    - `maximum_marks`: Float (> 0).
    - `year_date`: String (optional, e.g. "2024").
  - **Response**: Created `PaperResponse` object. On processing failure, rolls back DB state and deletes temporary upload files.

- **`GET /api/v1/papers`** *(Public)*
  - **Query Parameters**: `page` (int, ge=1), `limit` (int, 1-100).
  - **Response**: Paginated list of uploaded question papers.

- **`GET /api/v1/papers/{id}`** *(Public)*
  - **Description**: Fetches single question paper details by ID.

- **`GET /api/v1/papers/{id}/status`** *(Public)*
  - **Description**: Poll processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).

- **`GET /api/v1/papers/{id}/performance-estimate`** *(Public)*
  - **Description**: Derives heuristic estimated student performance (`estimated_pass_percentage` and `estimated_average_marks`) using only the paper's marks-weighted Bloom's Taxonomy distribution (L1–L6). Not actual student statistics.
  - **Response**:
    ```json
    {
      "estimated_pass_percentage": 72.0,
      "estimated_average_marks": 58.0,
      "reason": null
    }
    ```
    If paper is not completed or questions with missing/invalid marks or levels exceed 20%, returns `{ "estimated_pass_percentage": null, "estimated_average_marks": null, "reason": "reason_code" }`.

- **`DELETE /api/v1/papers/{id}`** *(Authenticated)*
  - **Description**: Deletes paper, cascade-deletes associated questions, topics, and similarities, and removes stored file from disk.

### Question Queries & Review
- **`GET /api/v1/questions`** *(Public)*
  - **Query Parameters**: `paper` (int), `bloom_level` (str), `topic` (str), `unit` (str), `marks` (float), `question_text` (str), `page` (int), `limit` (int).
  - **Response**: Paginated list of matching questions.

- **`GET /api/v1/questions/{id}`** *(Public)*
  - **Description**: Fetches single question details including sub-questions.

- **`PATCH /api/v1/questions/{id}`** *(Authenticated)*
  - **Description**: Applied by reviewers to override details (Human-in-the-Loop review). Replaces topic associations cleanly without duplicate links.
  - **Payload**:
    ```json
    {
      "question_text": "Optional modified text",
      "marks": 5.0,
      "bloom_level": "L5",
      "question_type": "Analytical",
      "topic_name": "Binary Search Trees",
      "unit": "Unit II"
    }
    ```
  - **Response**: The updated question instance with effective values.

### Analytics Endpoints *(Authenticated)*
- **`GET /api/v1/analytics/overview`**
  - **Response**: Macro stats (`total_papers`, `total_questions`, `total_marks`, `duplicate_questions_count`).
- **`GET /api/v1/analytics/bloom`**
  - **Response**: Question-count and marks-weighted Bloom level distributions (L1–L6).
- **`GET /api/v1/analytics/topics`**
  - **Response**: Topic frequencies and marks allocations.
- **`GET /api/v1/analytics/questions`**
  - **Response**: Repeated questions, highest-mark questions, and question types.
- **`GET /api/v1/analytics/trends`**
  - **Query Parameters**: `metric_type` (`"count"` or `"marks_weighted"`), `subject_id` (optional int).
  - **Response**: Aggregated historical cognitive level trend metrics.

---

## 3. Database Schema Specification

Below is the database table schema mapped via SQLAlchemy 2.x models:

### Table: `bloom_levels`
- `id` (int, PK)
- `code` (str, unique) - e.g., "L1", "L2"
- `name` (str) - e.g., "Remember", "Understand"
- `description` (text)
- `keywords` (json)

### Table: `subjects`
- `id` (int, PK)
- `code` (str, unique, index) - e.g., "CS301"
- `name` (str, index)
- `department` (str, Nullable)
- `description` (text, Nullable)

### Table: `question_papers`
- `id` (int, PK)
- `subject_id` (int, FK -> `subjects.id`)
- `examination_type` (str)
- `maximum_marks` (float)
- `original_filename` (str)
- `stored_file_path` (str)
- `upload_timestamp` (datetime)
- `year_date` (str, Nullable)
- `processing_status` (str) - "PENDING", "PROCESSING", "COMPLETED", "FAILED"
- `extraction_status` (str)
- `validation_status` (str)
- `optional_question_flag` (bool)
- `validation_metadata` (json, Nullable)

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
- `co_mapping` (json, Nullable)
- `choice_group` (str, Nullable)

### Table: `topics`
- `id` (int, PK)
- `subject_id` (int, FK -> `subjects.id`)
- `name` (str, index)
- `description` (text, Nullable)

### Table: `question_topics`
- `id` (int, PK)
- `question_id` (int, FK -> `questions.id`)
- `topic_id` (int, FK -> `topics.id`)
- `confidence` (float)
- `is_primary` (bool)
- **Constraint**: `UniqueConstraint("question_id", "topic_id", name="uq_question_topic")`

### Table: `question_similarities`
- `id` (int, PK)
- `source_question_id` (int, FK -> `questions.id`)
- `target_question_id` (int, FK -> `questions.id`)
- `similarity_score` (float)
- `similarity_type` (str) - "exact_repeat", "semantic_repeat"
- `classification` (str) - "exact_repeat", "potentially_repeated"
