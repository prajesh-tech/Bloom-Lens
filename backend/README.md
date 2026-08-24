# BloomLens V1 — Production Backend

BloomLens is an AI-powered historical question-paper analysis system designed for higher education institutions. It analyzes historical examination question papers (PDF & DOCX) to answer:

> **What has been asked historically, how frequently has it been asked, and at what cognitive level has it been asked?**

---

## Key Features

- **Document Parsing & OCR**: Structured extraction for PDF (PyMuPDF), DOCX (`python-docx`), and scanned image PDFs using PaddleOCR fallback.
- **Hierarchical Question Segmentation**: Detects main questions (`Q1`, `Q2`) and sub-questions (`Q1(a)`, `Q1(b)`), preserving parent-child relationships.
- **Marks & Paper Validation**: Extracts question marks, detects optional question structures (`Answer 4 out of 5`), and validates paper maximum marks against extracted sums.
- **Hybrid Bloom Classifier**: 5-stage classifier based on Revised Bloom's Taxonomy (L1 Remember to L6 Create) combining verb analysis, cognitive operation hierarchy, SentenceTransformers semantic similarity, structure analysis, weighted scoring, and Google Gemini LLM fallback verification (`google-genai`).
- **Explainable AI Metadata**: Detailed component scores, detected verbs, cognitive operations, and confidence scores saved for every question.
- **Similarity & Vector Search**: FAISS CPU vector index and text normalization to detect exact duplicate questions and semantically similar questions across historical years.
- **Analytics Engine**: Question-count Bloom distribution, marks-weighted Bloom distribution, topic frequency, historical cognitive trends, and question type breakdown.
- **Human-in-the-Loop Review**: Override question text, marks, topic, unit, Bloom level, and question type while preserving original AI predictions for research evaluation.
- **REST APIs & OpenAPI**: Versioned `/api/v1/` endpoints ready for React frontend integration.

---

## Tech Stack

- **Language & Core Framework**: Python 3.12, FastAPI, Pydantic v2, Pydantic Settings
- **Database**: SQLAlchemy 2.x, Alembic, MySQL 8 / SQLite (`aiosqlite`)
- **Document Processing**: PyMuPDF (`fitz`), `python-docx`, PaddleOCR
- **AI / NLP & Vectors**: Hugging Face `transformers`, `sentence-transformers` (`all-MiniLM-L6-v2`), `faiss-cpu`, Google GenAI SDK (`google-genai`)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## Project Structure

```text
backend/
├── app/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── core/                       # Config, database & logging
│   ├── api/routes/                 # Versioned REST API endpoints (/api/v1/)
│   │   ├── health.py               # System health check
│   │   ├── papers.py               # Paper upload, processing & status
│   │   ├── questions.py            # Search, filter, pagination & human review
│   │   └── analytics.py            # Overview, Bloom metrics, topics & trends
│   ├── models/                     # SQLAlchemy 2.x database models
│   ├── schemas/                    # Pydantic v2 validation schemas
│   ├── services/                   # Business & AI service logic
│   │   ├── document_service.py     # PDF/DOCX/OCR abstraction
│   │   ├── question_extraction_service.py # Parsing & paper validation
│   │   ├── bloom_service.py        # Hybrid Bloom classifier & Gemini fallback
│   │   ├── similarity_service.py   # FAISS vector similarity engine
│   │   └── analytics_service.py    # Analytics aggregations
│   └── utils/                      # Text cleaning & validation helpers
├── alembic/                        # Alembic migrations & initial seed data
├── tests/                          # Automated Pytest test suite
├── uploads/                        # Stored question paper files
├── .env.example                    # Environment variable template
└── requirements.txt                # Python dependencies
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.12+
- MySQL 8 (or SQLite for local development)

### 2. Environment Setup
Clone the repository and set up a virtual environment:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your `.env` settings:
```env
DATABASE_URL=sqlite+aiosqlite:///./bloomlens.db
# For MySQL 8: mysql+pymysql://user:password@localhost:3306/bloomlens

GEMINI_API_KEY=your_google_gemini_api_key
UPLOAD_DIR=uploads
BLOOM_VERIFICATION_THRESHOLD=0.80
```

### 4. Database Migrations
Run Alembic migrations to create tables and seed Bloom taxonomy levels (L1–L6):

```bash
alembic upgrade head
```

---

## Running the Server

Start the FastAPI development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access Interactive API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running Tests

Execute the automated test suite:

```bash
pytest tests/ -v
```

The test suite covers:
- Document extraction (PDF, DOCX, OCR fallback)
- Question hierarchy, marks extraction, and paper validation
- Mandatory Bloom Classifier test cases (L1 Remember to L6 Create, compound questions, ambiguous cases)
- FAISS duplicate question similarity search
- Count-based and marks-weighted analytics metrics
- REST API upload, search, pagination, and human override endpoints

---

## V1 / V2 Boundary & Scope

### Implemented in V1
- Historical question paper parsing & sub-question hierarchy
- Marks normalization and paper mark validation
- Hybrid Revised Bloom Taxonomy classification (L1–L6) with explainability
- Duplicate & semantic repeated question detection
- Question-count and marks-weighted Bloom distributions
- Historical cognitive level trends
- Human-in-the-loop overrides & review workflows

### Strictly Excluded (Reserved for V2)
- Course Outcomes (COs)
- CO extraction, mapping, or attainment matrices
- Student performance prediction
- Automatic question paper generation or exam prediction

---

## Documentation & Contribution Reference

For guides on how to setup, run, and modify this project:
- **System Design & Architecture**: [`design.md`](file:///home/Prajesh/sp/design.md)
- **Developer Contribution Guide**: [`user_contributions.md`](file:///home/Prajesh/sp/user_contributions.md)
- **Technical Specification**: [`spec/spec.md`](file:///home/Prajesh/sp/spec/spec.md)
- **Operational Tasks & Roadmap**: [`spec/plan.md`](file:///home/Prajesh/sp/spec/plan.md) and [`spec/tasks.md`](file:///home/Prajesh/sp/spec/tasks.md)
- **Skills Matrix**: [`spec/skills.md`](file:///home/Prajesh/sp/spec/skills.md)

