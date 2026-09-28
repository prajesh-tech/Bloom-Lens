# BloomLens

<div align="center">

**AI-Powered Historical Question-Paper Analysis & Cognitive Level Evaluation System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](file:///home/Prajesh/sp/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF.svg)](https://vitejs.dev/)

</div>

---

## Overview

**BloomLens** is a full-stack, AI-powered document intelligence and curriculum analytics platform designed for higher education institutions and accreditation bodies. It ingests historical examination question papers in PDF and DOCX formats, extracts hierarchical questions, classifies cognitive complexity according to **Revised Bloom's Taxonomy (L1 Remember to L6 Create)**, detects duplicate/semantically similar questions across examination years, and delivers actionable cognitive distribution analytics.

BloomLens answers three foundational academic questions:
> 1. **What has been asked historically?**
> 2. **How frequently has it been asked?**
> 3. **At what cognitive level has it been asked?**

---

## Key Features

- **Multi-Format Document Parsing**: High-fidelity structured text and layout extraction for digital PDFs (PyMuPDF), Word documents (`python-docx`), and scanned image PDFs with PaddleOCR fallback.
- **Hierarchical Question Segmentation**: Automatically identifies main questions (`Q1`, `Q2`), sub-questions (`Q1(a)`, `Q1(b)`), marks allocations, and paper constraints (e.g., choice rules such as *"Answer any 4 questions"*).
- **Hybrid Bloom Classifier**: 5-stage classification engine combining action verb analysis, cognitive operation hierarchy, SentenceTransformers semantic embeddings (`all-MiniLM-L6-v2`), structure analysis, and Google Gemini LLM fallback verification (`google-genai`).
- **Duplicate & Similarity Search**: FAISS vector indexing combined with text normalization to identify repeated or closely related historical questions across terms and subjects.
- **Explainable AI (XAI)**: Full transparency into classification rationale, including verb detection, component weights, semantic similarity metrics, and LLM reasoning.
- **Interactive Analytics Engine**: Single-query aggregation for cognitive distribution (count & marks-weighted), topic frequency, and longitudinal multi-year cognitive trends.
- **Human-in-the-Loop Review Workflow**: Reviewers can override Bloom levels, question text, topics, or marks while maintaining original AI predictions for academic auditability.
- **Modern Responsive Web UI**: React 18, TypeScript, Tailwind CSS, Lucide icons, and React Query with offline mock mode support.

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, Alembic |
| **Database** | SQLite / aiosqlite (Local), MySQL 8 (Production) |
| **AI / NLP & OCR** | PyMuPDF, python-docx, PaddleOCR, SentenceTransformers, FAISS-CPU, Google Gemini SDK (`google-genai`) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, TanStack React Query, Lucide Icons, Sonner |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX, Vitest |

---

## Repository Structure

```text
BloomLens/
├── backend/                       # FastAPI async backend service
│   ├── app/                       # Application code (API, Core, Models, Services, Schemas)
│   ├── alembic/                   # Database migrations & initial seed data
│   ├── tests/                     # Automated Pytest suite
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # Backend-specific documentation
├── frontend/                      # React + TypeScript + Vite frontend application
│   ├── src/                       # Components, pages, hooks, services, types
│   ├── package.json               # Node.js dependencies & scripts
│   └── README.md                  # Frontend-specific documentation
├── spec/                          # Technical specifications, roadmap, and skills matrix
│   ├── spec.md                    # Detailed API contracts & data models
│   ├── plan.md                    # Roadmap & milestone boundaries
│   ├── tasks.md                   # Operational tasks & backlog
│   └── skills.md                  # Developer competencies & design rules
├── design.md                      # System architecture & pipeline diagrams
├── user_contributions.md          # Comprehensive developer guide
├── CONTRIBUTING.md                # Contribution guidelines & Git workflow
├── CODE_OF_CONDUCT.md             # Contributor Covenant Code of Conduct
├── SECURITY.md                    # Vulnerability disclosure & security policy
├── LICENSE                        # MIT License
└── AGENTS.md                      # AI agent coding guidelines & conventions
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/prajesh-tech/Bloom-Lens.git
cd Bloom-Lens
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations (seeds L1–L6 Bloom levels)
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start Vite development server
npm run dev
```

- **Web Application**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:3000](http://localhost:3000))

---

## Verification & Testing

To run the complete verification suite across backend and frontend:

```bash
# 1. Backend test suite
cd backend
.venv/bin/pytest tests/ -v

# 2. Frontend validation
cd ../frontend
npm run type-check
npm run lint
npm run test
npm run build
```

---

## Documentation Links

- **Architecture & Pipeline**: [System Design (`design.md`)](file:///home/Prajesh/sp/design.md)
- **Technical Specification**: [API & Model Spec (`spec/spec.md`)](file:///home/Prajesh/sp/spec/spec.md)
- **Roadmap & Plan**: [V1/V2 Milestones (`spec/plan.md`)](file:///home/Prajesh/sp/spec/plan.md)
- **Contributing**: [Contribution Guidelines (`CONTRIBUTING.md`)](file:///home/Prajesh/sp/CONTRIBUTING.md)
- **Code of Conduct**: [Code of Conduct (`CODE_OF_CONDUCT.md`)](file:///home/Prajesh/sp/CODE_OF_CONDUCT.md)
- **Security**: [Security Policy (`SECURITY.md`)](file:///home/Prajesh/sp/SECURITY.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](file:///home/Prajesh/sp/LICENSE) file for details.
