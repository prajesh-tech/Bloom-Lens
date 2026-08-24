# Developer & AI Agent Skill Matrix — BloomLens

This document maps the core technological skill domains, libraries, and frameworks required to effectively contribute to **BloomLens**, along with guidelines for AI coding agents.

---

## 1. Backend Engineering Domain

### FastAPI & API Design
- **Required Skill**: Asynchronous endpoint design using `async def`, dependency injection using FastAPI `Depends`, CORS configurations, middleware integrations, and custom route handlers.
- **Key Modules**: Refer to [`backend/app/main.py`](file:///home/Prajesh/sp/backend/app/main.py) and files in [`backend/app/api/routes/`](file:///home/Prajesh/sp/backend/app/api/routes/) for endpoint architectures.

### Pydantic v2 & Configuration
- **Required Skill**: Strong knowledge of Pydantic model schemas, serialization, validation rules, and configuration loaders via `pydantic-settings`.
- **Key Modules**: Inspect [`backend/app/schemas/`](file:///home/Prajesh/sp/backend/app/schemas/) for request/response validation schemas.

### Relational Database & ORM
- **Required Skill**: SQLAlchemy 2.0 Async engine operation. Creating relationships, self-referential keys (for parent-child questions), cascade deletes, and transaction management.
- **Key Modules**: Refer to [`backend/app/core/database.py`](file:///home/Prajesh/sp/backend/app/core/database.py) and models in [`backend/app/models/`](file:///home/Prajesh/sp/backend/app/models/).

---

## 2. Artificial Intelligence, OCR, & NLP

### Document Parsing & OCR Fallbacks
- **Required Skill**: Processing textual data from PDF page formats (via PyMuPDF/`fitz`) and Word documents (`python-docx`), and coordinating scanned image page text extraction (via PaddleOCR fallback).
- **Key Modules**: Refer to [`backend/app/services/document_service.py`](file:///home/Prajesh/sp/backend/app/services/document_service.py).

### Semantic Vectors & Similarity Engines
- **Required Skill**: Utilizing SentenceTransformers (`all-MiniLM-L6-v2`) to convert raw text into 384-dimensional dense vectors. Familiarity with FAISS CPU vector index loading, searching, and memory updating.
- **Key Modules**: Refer to [`backend/app/services/similarity_service.py`](file:///home/Prajesh/sp/backend/app/services/similarity_service.py).

### LLM Prompting & Fallbacks
- **Required Skill**: Invoking LLM models using Google's modern `google-genai` SDK, writing deterministic prompts, and utilizing structured JSON schema constraints to enforce output validation.
- **Key Modules**: Refer to [`backend/app/services/bloom_service.py`](file:///home/Prajesh/sp/backend/app/services/bloom_service.py).

---

## 3. Frontend Development Domain

### React 18 & TypeScript
- **Required Skill**: Component modularity, React hooks (`useState`, `useRef`, `useContext`), functional UI patterns, and strict typing using TypeScript interfaces.

### State Cache Management (React Query)
- **Required Skill**: Data loading using TanStack React Query, writing custom query hooks, setting query keys, and handling mutation success callbacks to invalidate and re-cache server responses.
- **Key Modules**: Refer to [`frontend/src/services/queries.ts`](file:///home/Prajesh/sp/frontend/src/services/queries.ts).

### Visualizations & Theme Design
- **Required Skill**: Creating interactive responsive graphs (via Recharts), configuring custom tooltips and legend layers, and styling layouts using Tailwind CSS custom colors and monospace typography.

---

## 4. Special Guidelines for AI Coding Agents

When working as an AI agent (such as Antigravity) in this repository, follow these conventions:

1. **Leverage Pre-existing Services**: Always inspect [`backend/app/services/`](file:///home/Prajesh/sp/backend/app/services/) before building helper utilities. Do not write custom NLP code or database connection methods from scratch.
2. **Follow Configuration Conventions**: Any new configuration parameter or key must be added to [`backend/app/core/config.py`](file:///home/Prajesh/sp/backend/app/core/config.py). Never hardcode API keys, ports, or paths.
3. **Respect Types & Builds**: Before completing your execution turn, you must run frontend verification scripts (`npm run type-check` and `npm run build`) to ensure that your changes have not broken TypeScript typings or bundler constraints.
4. **Preserve Rules in `AGENTS.md`**: Do not remove or violate any instructions inside [`AGENTS.md`](file:///home/Prajesh/sp/AGENTS.md).
