# Frontend Architecture

This document covers frontend-specific composition and data flow. The system-wide architecture, API endpoints, and document-processing pipeline are documented in the root [System Design](../design.md).

## Application Layers

```text
Route pages
    ↓
Feature components and shared UI
    ↓
React Query hooks
    ↓
Axios API services or mock data
    ↓
FastAPI /api/v1/
```

- **Pages** compose the dashboard, upload, history, and paper-analysis views.
- **Feature components** implement question tables, review drawers, upload controls, and Bloom charts.
- **Shared components** provide buttons, badges, cards, drawers, skeletons, error boundaries, and notifications.
- **React Query** owns server-state caching and mutation invalidation; component state is reserved for transient UI state.
- **Service modules** isolate HTTP calls, mock responses, and response types.

## Routes and Key Components

| Page | Responsibility |
| --- | --- |
| `Home` | Overview dashboard and aggregate Bloom distribution |
| `Analyze` | Paper selection, upload, and analysis submission |
| `AnalysisResults` | Paper questions, filters, review drawer, and paper-specific charts |
| `History` | Search and manage uploaded papers |
| `Settings` | Frontend settings view |

Components are organized under `src/components/analysis`, `charts`, `common`, `history`, `layout`, and `upload`. Domain types and Bloom taxonomy presentation configuration live under `src/types` and `src/config`.

## API Modes and Authentication

Set `VITE_USE_MOCK_API=true` for local demo data or `false` to use the configured FastAPI base URL. The browser intentionally does not contain a shared backend API key: values prefixed with `VITE_` are public in built assets. When backend authentication is enabled, protected operations must be mediated by a trusted server-side integration. Never disable backend authentication in production to make the browser work.

## Verification

Run the frontend checks from `frontend/`:

```bash
npm run type-check
npm run lint
npm run test
npm run build
```
