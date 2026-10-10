# BloomLens V1 Frontend

BloomLens is an AI-powered historical question-paper analysis web application designed for higher education institutions. It analyzes historical examination question papers (PDF & DOCX) to determine:

> **What has been asked historically, how frequently has it been asked, and at what cognitive level has it been asked?**

---

## Overview

The BloomLens V1 frontend is a production-quality, responsive React + TypeScript application built with Vite and Tailwind CSS. It connects to the FastAPI backend API or runs in a standalone Mock API mode with simulated network latency to provide interactive analytics, Bloom taxonomy distributions, search/filtering, and human-in-the-loop review.

---

## Features

- **Document Upload & Validation**: Drag-and-drop support for PDF and DOCX question papers with format, size, and metadata validation.
- **Interactive Bloom Taxonomy Analytics**:
  - **Donut Chart**: Centralized total metric with dark custom tooltips and explicit color legends.
  - **Bar Chart**: Marks-Weighted cognitive distribution vs Question-Count distribution.
- **Combined Search & Filter**: Real-time case-insensitive text/ID search combined with Revised Bloom Taxonomy level pill filters (L1 Remember to L6 Create).
- **Slide-Over Question Drawer**: Right-side drawer for inspecting question details, sub-question hierarchy, AI reasoning, component scores, and human classification overrides.
- **Analytical Typography System**: Slate light theme (`bg-slate-50`) paired with JetBrains Mono font for question IDs (`Q01`), marks (`05 marks`), percentages (`94%`), and confidence scores.
- **Dual API Mode**: Connects to the FastAPI backend at `http://localhost:8000/api/v1` or operates offline in Mock Mode with simulated network latency (1500ms–2500ms).

---

## Tech Stack

- **Framework & Core**: React 18, TypeScript, Vite
- **Styling & Icons**: Tailwind CSS, Lucide React (`lucide-react`)
- **Data Visualization**: Recharts (`recharts`)
- **Notifications**: Sonner (`sonner`)
- **Routing**: React Router v6 (`react-router-dom`)
- **HTTP Client**: Axios (`axios`)
- **Testing**: Vitest (`vitest`), React Testing Library, jsdom

---

## Project Structure

```text
frontend/
├── public/                     # Static public assets & favicons
├── src/
│   ├── components/
│   │   ├── common/             # Badge, BloomBadge, Button, Card, Drawer, Skeleton, Toast
│   │   ├── layout/             # Navbar, Sidebar, Header, Layout
│   │   ├── upload/             # Dropzone, FilePreview, ProcessingProgress
│   │   ├── analysis/           # AnalysisHeader, SummaryCards, QuestionTable, QuestionFilterBar, QuestionDrawer
│   │   ├── charts/             # BloomDonutChart, BloomBarChart, CustomTooltip, CustomLegend
│   │   └── history/            # HistoryTable
│   ├── pages/
│   │   ├── Home.tsx            # Executive Dashboard Overview
│   │   ├── Analyze.tsx         # Document Upload Workflow
│   │   ├── AnalysisResults.tsx # Interactive Analysis Dashboard
│   │   ├── History.tsx         # Analysis History Table
│   │   └── Settings.tsx        # System Configuration & Tokens
│   ├── services/
│   │   ├── api.ts              # Axios client setup
│   │   ├── analysisApi.ts      # Dual-mode Analysis API
│   │   ├── historyApi.ts       # Dual-mode History API
│   │   └── mockData.ts         # Sample dataset for mock mode
│   ├── config/
│   │   ├── bloomConfig.ts      # Centralized Bloom Taxonomy design system
│   │   └── constants.ts        # App constants
│   ├── types/                  # Strict TypeScript interfaces
│   │   ├── bloom.ts
│   │   ├── paper.ts
│   │   ├── question.ts
│   │   └── analytics.ts
│   ├── utils/                  # Text & format utilities
│   │   ├── formatters.ts
│   │   └── latency.ts
│   ├── App.tsx                 # React Router setup
│   ├── main.tsx                # Entrypoint
│   └── index.css               # Tailwind & font imports
├── tests/                      # Vitest component test suite
├── .env.example
├── README.md
├── ARCHITECTURE.md             # Frontend-specific architecture
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## Prerequisites

- Node.js 18.x or 20.x
- npm 9.x+ or yarn

---

## Installation

Clone the repository, navigate to the `frontend` directory, and install dependencies:

```bash
cd frontend
npm install
```

Copy `.env.example` to create your local `.env` file:

```bash
cp .env.example .env
```

On Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

---

## Environment Configuration

Configure environment variables in `.env`:

```env
# Base URL of the BloomLens FastAPI backend
VITE_API_BASE_URL=http://localhost:8000

# Controls whether mock API mode with simulated network latency (1.5s-2.5s) is active
# Set to 'true' for standalone demo mode or 'false' for real backend API connection
VITE_USE_MOCK_API=true
```

> **Security**: Do not configure a shared API key in a `VITE_` variable; Vite bundles these values into public client code. The browser does not send server API keys. When backend authentication is enabled, protected actions require a trusted server-side integration. For local development only, backend authentication may be disabled.

The server enforces upload limits using `MAX_UPLOAD_SIZE_MB`, `MAX_DOCX_UNCOMPRESSED_SIZE_MB`, `MAX_DOCUMENT_PAGES`, and `MAX_EXTRACTED_QUESTIONS`. The backend also limits concurrent question classification with `MAX_PARALLEL_QUESTION_CLASSIFICATIONS`; configure these server-side values to match deployment capacity.

---

## How to Connect to the Live FastAPI Backend

To switch to the live Python FastAPI backend:

1. **Update `frontend/.env`**:
   Change `VITE_USE_MOCK_API` to `false`:

   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_MOCK_API=false
   ```

2. **Start the FastAPI Backend Server**:

   ```bash
   cd backend
   python3 -m uvicorn app.main:app --port 8000 --reload
   ```

3. **Start the Frontend Dev Server**:

   ```bash
   cd backend/../frontend
   npm run dev
   ```

Once started, the top navigation header in the frontend will automatically display:

- **`● Backend Connected`** (Green Badge) instead of `⚡ Mock Mode`.

---

## Development

Start the Vite local development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

---

## Production Build

Compile and build the static production bundle:

```bash
npm run build
```

The compiled assets will be output to the `dist/` directory.

---

## Preview Production Build

Preview the production build locally:

```bash
npm run preview
```

---

## Testing

Execute the Vitest automated test suite:

```bash
npm run test
```

Additional test commands:

```bash
# Watch mode for test-driven development
npm run test:watch

# Code coverage report
npm run test:coverage
```

The test suite verifies:
- Rendering and styling of Bloom Taxonomy badges (L1–L6)
- Search query and Bloom level pill button filtering
- Monospace formatting and low-confidence warning indicators in `QuestionTable`
- Drag-and-drop file upload format validation

---

## Code Quality & Verification

Run static type checking and linting before committing code:

```bash
# Type check TypeScript definitions
npm run type-check

# ESLint inspection
npm run lint
```

---

## Troubleshooting

### 1. Backend connection failed
- Verify `VITE_API_BASE_URL` in `.env`.
- Ensure the FastAPI backend server is running (`uvicorn app.main:app --port 8000`).

### 2. CORS Error
- Ensure the backend CORS middleware permits origins from `http://localhost:3000`.

### 3. Mock Mode not switching
- After changing `VITE_USE_MOCK_API` in `.env`, restart the Vite dev server (`npm run dev`).

---

## V1 / V2 Boundary

### Included in V1
- Question paper extraction & sub-question hierarchy visualization
- Bloom's Taxonomy L1–L6 classification & explainability
- Duplicate & semantic repeat detection
- Question-count and marks-weighted analytics
- Human-in-the-loop overrides & review workflows

### Excluded (Reserved for V2)
- Automated Course Outcome mapping and analytics (course and outcome CRUD foundations are implemented)
- CO-PO mapping matrices
- Student attainment analytics
- Automatic question generation

---

## Documentation & Contribution Reference

For guides on how to set up, run, and modify this project:
- **System Design & Architecture**: [`design.md`](../design.md)
- **Developer Contribution Guide**: [`user_contributions.md`](../user_contributions.md)
- **Technical Specification**: [`spec/spec.md`](../spec/spec.md)
- **Operational Tasks & Roadmap**: [`spec/plan.md`](../spec/plan.md) and [`spec/tasks.md`](../spec/tasks.md)
- **Skills Matrix**: [`spec/skills.md`](../spec/skills.md)

---

## License

MIT License &copy; 2026 BloomLens Team.
