# BloomLens

<div align="center">

**AI-Powered Historical Question-Paper Analysis & Cognitive Level Evaluation System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-7.x-646CFF.svg)](https://vitejs.dev/)

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
- **Hybrid Bloom Classifier**: Weighted heuristic classifier combining leading action verbs, cognitive operations, semantic embeddings, and question structure, with optional bounded Google Gemini verification. Scores are uncalibrated, not probabilities.
- **Duplicate & Similarity Search**: One index per upload, with FAISS when available and NumPy fallback. Normalized exact matches and near duplicates are distinct; comparisons default to the same subject and reject incompatible embedding versions. A versioned hashing fallback is exposed when the semantic model is unavailable.
- **Explainable AI (XAI)**: Heuristic explanations expose detected verbs, component scores, and optional model output. These describe classifier signals; they do not establish causal explanations or independently validated correctness.
- **Interactive Analytics Engine**: Leaf-question aggregation for count and marks distributions, topics, and exam-date trends, with subject filters and explicit unknown levels. Optional choices are reported as uncertain rather than selecting an arbitrary question subset.
- **Human-in-the-Loop Review Workflow**: Reviewers can override Bloom levels, question text, topics, or marks with actor-attributed immutable revision history. Text edits mark analysis stale until re-analysis.
- **Modern Responsive Web UI**: React 18, TypeScript, Tailwind CSS, Lucide icons, and React Query with offline mock mode support.

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, Alembic |
| **Database** | SQLite / aiosqlite (Local), MySQL 8 / asyncmy (Production); PyMySQL for migrations |
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
pip install --require-hashes -r requirements.lock

# Configure environment variables
cp .env.example .env

# Run database migrations (seeds L1–L6 Bloom levels)
alembic upgrade head

# Provision a reviewer (password is prompted; no public registration)
python -m app.manage_reviewers reviewer --role admin

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 3. Frontend Setup

```bash
cd frontend

# Install locked dependencies (Node 20.19+ or Node 22.12+)
npm ci

# Configure environment variables
cp .env.example .env

# Start Vite development server
npm run dev
```

- **Web Application**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:3000](http://localhost:3000))

---

## Processing, authentication, and measured limits

Uploads return `202` after committing `UPLOADED`; the UI polls extraction and
analysis stages until a terminal status. The initial worker uses in-process
BackgroundTasks and is not durable. Restarted interrupted jobs are marked failed;
a durable external queue is future work. Stored uploads are removed after
extraction by default. Size/rate limits and same-subject content hashes guard
admission and concurrent duplicates.

Browser requests use same-origin HttpOnly reviewer sessions and CSRF protection
through the backend deployment; service credentials remain server-side. Set up
HTTPS and secure cookies for production. Mock mode is enabled only by the literal
`VITE_USE_MOCK_API=true` and uses isolated copies of fixtures.

The internally authored 150-question evaluation across three subjects measured
**98.67% (148/150) before classifier changes** and **100% (150/150) afterward**
using deterministic offline embeddings. This is a templated engineering regression
set, not independent validation or a production accuracy estimate. See the
[evaluation protocol](backend/tests/data/EVALUATION.md).

Google verification, when enabled, transmits question text to Google. Disable it
for documents that must remain local. Automated CO mapping remains V2; supplied
mappings are honored. Container/MySQL runtime and remote CI verification remain
outstanding because Docker is unavailable in this workspace. See the
[remediation status](spec/remediation-status.md) and
[dependency audit and verification limits](spec/dependency-audit.md).

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

- **Architecture & Pipeline**: [System Design (`design.md`)](./design.md)
- **Technical Specification**: [API & Model Spec (`spec/spec.md`)](./spec/spec.md)
- **Roadmap & Plan**: [V1/V2 Milestones (`spec/plan.md`)](./spec/plan.md)
- **Contributing**: [Contribution Guidelines (`CONTRIBUTING.md`)](./CONTRIBUTING.md)
- **Code of Conduct**: [Code of Conduct (`CODE_OF_CONDUCT.md`)](./CODE_OF_CONDUCT.md)
- **Security**: [Security Policy (`SECURITY.md`)](./SECURITY.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.
