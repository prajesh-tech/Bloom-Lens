# Remediation status — 2026-11-09

Numbering below follows the original issues attachment. “Fixed” describes the
implemented behavior and local regression evidence; it does not claim a deployed
security assessment or remotely passing CI. No V2 automatic outcome mapping,
deployment, push, or force-push was performed.

## Phase 1 — extraction (`1a9644e`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Printed labels and standalone subparts | fixed | `test_extraction_regressions.py`: exact labels and parents, five full fixtures |
| 2. Numbered nonverbs/instructions | fixed | instruction/nonverb regressions |
| 3. Adjacent OR boundaries | fixed | exact choice-group fixtures |
| 4. Continuation fallback | fixed | numbered continuation and inline-marks regressions |
| 5. Explicit last marks and section reset | fixed | marks regressions; allocation heading retained, bare equations excluded |
| 6. Leaf scoring and analytics | fixed | shared `extract_leaf_questions`, analytics leaf tests |
| 7. Optional section rules | fixed | metadata stores section/N/M; equivalent unambiguous totals only; distributions expose uncertainty |
| 8. DOCX order/pages | fixed | interleaved table test; available page count or null |

Five exact multi-section fixtures are under `backend/tests/data/extraction`.
Arbitrary choices are never selected to manufacture Bloom/topic distributions.

## Phase 2 — contracts (`6287930`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Exam type source | fixed | authenticated canonical endpoint, React Query and contract tests |
| 2. Mock defaults | fixed | literal-true helper, real API default and tests |
| 3. Threshold examples | fixed | example/config regression, defaults 0.60/0.70 |

## Phase 3 — uploads (`a25aded`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Async dispatch/short transactions | fixed | committed 202/status URL, background dispatcher, session-boundary/failure/restart tests |
| 2. UI polling | fixed | status hook and upload-page completion/failure/retry tests; terminal polling stops |
| 3. Commit before file deletion | fixed | failed-commit file preservation test |
| 4. Same-subject duplicates | fixed | SHA256 unique constraint, duplicate and concurrent-winner tests |
| 5. Streaming/body/rate limits | fixed | bounded-read, chunked 413, principal 429 tests |
| 6. Retention | fixed | deletion default and retention-enabled tests |

BackgroundTasks is intentionally in-process, not a durable queue. Restarted jobs
are marked failed. Hash/error migration upgrade and rollback are tested; operational
rollback notes are in `CONTRIBUTING.md`.

## Phase 4 — auth (`be8bf87`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Private routes and public minimal health | fixed | parametrized private-router rejection tests, minimal health test |
| 2. Production/staging startup guard | fixed | disabled-auth and secure-cookie config validation |
| 3. Browser credential isolation | fixed | integrated same-origin backend session gateway, provisioning CLI, scrypt, revocation, CSRF, login limits; browser has no shared service key |
| 4. Attributed revisions | fixed | immutable snapshots, actor/time endpoint, drawer view and attribution tests |
| 5. Literal search/request IDs/metadata | fixed | escaped ILIKE, sanitized request IDs, protected metrics/deep health tests |

The user selected server-side browser auth with local reviewer accounts and later
explicitly authorized restoring the committed async upload flow and route auth
after a concurrent editor reverted it. Account/session/revision migrations and
rollback are tested. No public registration exists.

## Phase 5 — classification (`f157467`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Leading verbs/boundaries/examples | fixed | classifier regression examples and incidental-noun tests |
| 2. Evaluation baseline | fixed | 150 internally authored CSV questions, 3 subjects, rationales, checksum-frozen baseline, accuracy/confusion script and gate |
| 3. Confidence meaning | fixed | explicitly uncalibrated classifier score in docs/UI/metadata |
| 4. Gemini | fixed | lazy cached client, bounded SDK/executor call, 4-call cap, model/timeout settings, delimited input and Google transmission documentation |
| 5. Persisted compatible embeddings | fixed | vector/backend/model/version persistence, logged hashing fallback, incompatible comparison test, migration round trip |
| 6. Similarity/index/analytics/UI | fixed | one index per upload, same-subject scope, exact vs near duplicate, unique counts, endpoint and drawer tests |
| 7. Topics/units | fixed | JSON word-boundary rules, authenticated subject topic CRUD, embedding fallback, primary associations, ID grouping and Bloom breakdown tests |
| 8. Edit behavior | fixed | normalized text, stale analysis/vector invalidation, supplied CO/choice fields, topic validation tests |
| 9. Trends and unknowns | fixed | parsed exam chronology test; explicit unknown count, no L1 substitution |

Frozen unchanged-classifier baseline: **148/150 (98.6667%)**. Corrected result:
**150/150 (100%)**, deterministic offline hashing/no Gemini. These internally
authored, templated regression labels are not independent validation or a claim
about real-world accuracy. See `backend/tests/data/EVALUATION.md`.
Historical missing embeddings are backfilled once; incompatible versions are not
compared semantically. FAISS has a NumPy fallback. Explanation signals are
heuristics, not causal proof. Automated CO mapping remains V2.

## Phase 6 — operations (`3b24d48`)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Structured/redacted logs | fixed | JSON context and known-secret-only redaction regressions |
| 2. Bounded metrics | fixed | route-template cardinality test, max 100 labels plus overflow |
| 3. OCR DPI/portable per-page handling | partly fixed | implementation and controlled-engine tests pass; real native Paddle/model execution across platforms remains unverified |
| 4. Locked dependencies/asyncmy | fixed | hashed CPU lock, asyncio/greenlet, corrected docs, pip check and audits |
| 5. Containers/MySQL/PR CI | partly fixed | artifacts and YAML parsed; Docker is unavailable and remote workflow has not run |

Dependency audit: backend **121 packages, zero known vulnerabilities, zero
skipped**; frontend **zero vulnerabilities**. Exact audit commands and Docker
failure are in `spec/dependency-audit.md`. A machine with Docker must build images,
smoke-test MySQL and run the PR workflow before release approval.

## Phase 7 — frontend (this commit)

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Lazy routes/chart chunk/budget | fixed | lazy routes, dedicated Recharts chunk, build enforces entry plus static imports below 400,000 bytes |
| 2. Similar/topic/subject/history views | fixed | drawer results/revisions, Analytics topics/repetition/trends, dashboard/analytics subject filters |
| 3. Page/hook/API/upload tests | fixed | Analytics, revisions, auth guard/API, mocked Axios contracts, polling, upload failure and retry |
| 4. Mock copying | fixed | private cloned store and mutation/snapshot-isolation regression |

README claims now describe the implemented weighted classifier, heuristic
explanations, optional FAISS path, fallback metadata and evaluation limitations.

## Verification record

Every phase preserved existing tests and reproduced its reported regressions
before fixes. Exact full-suite results are recorded in each phase commit:

| Phase | Backend, both commands | Frontend tests | Other frontend gates |
| --- | --- | --- | --- |
| 1 | 88 passed | 24 passed | type-check, lint, build passed |
| 2 | 90 passed | 27 passed | type-check, lint, build passed |
| 3 | 101 passed; concurrency test additionally passed | 29 passed | type-check, lint, build passed |
| 4 | 117 passed | 33 passed | type-check, lint, build passed |
| 5 | 136 passed | 35 passed | type-check, lint, build passed |
| 6 | 146 passed | 35 passed | type-check, lint, build passed |
| 7 | 149 passed | 46 passed | type-check, lint, build passed; entry plus static imports 347.62 kB |

Backend SQLite test execution requires an unsandboxed process in this workspace;
the sandbox blocks test database progress. Bare system pytest lacks project
packages, so `pytest tests -q` runs after activating `.venv`. Neither limitation
was hidden by substituting weaker checks. Migration tests exercise upgrade and
rollback on SQLite; MySQL container execution remains outstanding.

An unrelated concurrent DOCX formatting change is preserved in the working tree
and excluded from remediation commits. No numbered implementation item was
skipped. The two partial items above identify remaining external runtime checks.

The final upload-page integration test keeps real polling and exact call-count
assertions. Its per-test budget allows constrained CI scheduling after the default
five-second harness limit expired; query clients are always cleared on teardown.
The full final frontend run passed all 46 tests.
