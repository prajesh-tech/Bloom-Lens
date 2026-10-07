# BloomLens System Architecture

BloomLens is an AI-powered examination question paper analysis system with a FastAPI backend and a React + TypeScript frontend.

For the full detailed frontend and backend system architecture document, see [frontend/ARCHITECTURE.md](file:///home/Prajesh/sp/frontend/ARCHITECTURE.md).

---

## 1. Core Endpoints (/api/v1)

| Method | Endpoint | Description | Auth Required |
| ------ | -------- | ----------- | ------------- |
| `GET` | `/api/v1/health` | Health check & DB status | No |
| `GET` | `/api/v1/health/deep` | Deep subsystem health check | No |
| `POST` | `/api/v1/papers/upload` | Upload & analyze paper | Yes |
| `GET` | `/api/v1/papers` | Paginated paper history list | No |
| `GET` | `/api/v1/papers/{id}` | Get paper details | No |
| `GET` | `/api/v1/papers/{id}/status` | Poll paper processing status | No |
| `GET` | `/api/v1/papers/{id}/performance-estimate` | Heuristic estimated student performance | No |
| `DELETE` | `/api/v1/papers/{id}` | Delete paper and cascade questions | Yes |
| `GET` | `/api/v1/questions` | Search, filter & paginate questions | No |
| `GET` | `/api/v1/questions/{id}` | Single question detail & sub-questions | No |
| `PATCH` | `/api/v1/questions/{id}` | Human review & classification override | Yes |
| `GET` | `/api/v1/analytics/overview` | Macro overview statistics | Yes |
| `GET` | `/api/v1/analytics/bloom` | Question-count & marks-weighted Bloom distributions | Yes |
| `GET` | `/api/v1/analytics/topics` | Topic frequency analytics | Yes |
| `GET` | `/api/v1/analytics/trends` | Historical cognitive Bloom level trends | Yes |

---

## 2. Estimated Student Performance Service

The **Performance Estimation Service** (`app/services/performance_estimation_service.py`) derives heuristic projections of student pass percentage and average marks from an analyzed question paper's marks-weighted Bloom's Taxonomy distribution (L1–L6).

> [!NOTE]
> Values are heuristic estimates derived solely from the question paper's Bloom's Taxonomy and marks distribution, not actual student statistics. This is a read-time derivation and does not pull forward V2 "Student Performance Analytics" (student marks/records/rosters).

### Heuristic Formulation
- **Scoring Units**: Uses leaf-level questions only (sub-questions or parent questions without sub-questions) to avoid double counting parent and sub-question marks.
- **Paper Difficulty ($D$)**:
  $$D = \frac{\sum_{i \in \text{valid}} (\text{marks}_i \times w(\text{level}_i))}{\sum_{i \in \text{valid}} \text{marks}_i}$$
  where default Bloom difficulty weights are: L1=0.10, L2=0.25, L3=0.45, L4=0.65, L5=0.85, L6=1.00.
- **Mappings (Clamped $[0, 100]$)**:
  - $\text{Estimated Pass \%} = \text{clamp}(95.0 - 65.0 \times D, 0, 100)$
  - $\text{Estimated Avg \%} = \text{clamp}(80.0 - 50.0 \times D, 0, 100)$
  - $\text{Estimated Average Marks} = \frac{\text{Estimated Avg \%}}{100} \times \text{maximum\_marks}$
- **Tunables in `backend/app/core/config.py`**:
  - `ESTIMATE_BLOOM_WEIGHT_L1` to `L6` (weights in $[0, 1]$, non-decreasing)
  - `ESTIMATE_PASS_PCT_INTERCEPT` (default 95.0), `ESTIMATE_PASS_PCT_SLOPE` (default 65.0)
  - `ESTIMATE_AVG_PCT_INTERCEPT` (default 80.0), `ESTIMATE_AVG_PCT_SLOPE` (default 50.0)
  - `ESTIMATE_MAX_EXCLUDED_MARKS_RATIO` (default 0.20): returns unavailable (`too_many_excluded`) if excluded marks exceed 20% of paper marks.
