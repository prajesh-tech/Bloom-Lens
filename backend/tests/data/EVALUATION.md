# Internal Bloom evaluation

`bloom_evaluation.csv` contains 150 internally authored questions across
Databases, Algorithms, and Networks, with per-question label rationale. The set
uses ten task templates across five concrete scenarios per subject and includes
the reported incidental-verb traps. It is a regression set, not an independently
reviewed or representative benchmark. It does not demonstrate general accuracy.

The frozen pre-fix baseline at `be8bf87` is 148/150 (98.67%). The initial corrected
classifier scores 150/150. The JSON artifact stores its confusion matrix and
dataset checksum; tests forbid dropping below that baseline or silently changing
the data. Run `.venv/bin/python -m scripts.evaluate_bloom` from `backend` for an
accuracy report and confusion matrix. Evaluation fixes hashing embeddings and
disables Google verification to avoid network/model variation across machines.

`confidence` is an uncalibrated score of classifier signal strength, or a
provider-reported score after Google verification. Neither is a probability of
correctness. The API retains the field name for compatibility; the drawer calls
it a classifier score. Calibration requires independently labeled held-out data.

When a Gemini API key is configured, low-score exam question text is transmitted
to Google. The model and timeout are settings, the client is reused, prompts
delimit exam text as untrusted data, and an in-memory bounded cache keys responses
by normalized text and model. Timeout returns without waiting for executor exit;
the SDK also receives the timeout. At most four calls remain in flight.

Question embeddings persist with backend/model/version metadata. Model commit
hashes identify compatible vectors; if unavailable, a process-specific version
prevents unsafe comparisons across restarts. Hashing fallback uses a versioned
configuration and is exposed in analysis metadata. Existing missing embeddings
are backfilled once for that subject; incompatible stored vectors are excluded
from semantic search, while exact text comparisons remain valid. Each upload
builds one same-subject similarity index. Scores at least 0.95 are near duplicates
unless normalized text is identical. Repeat counts include unique question IDs
participating at either end of a matching pair.

Topic rules live in `app/data/topic_rules.json`. Authenticated subject topic CRUD
manages an explicit topic vocabulary; matching uses word boundaries and then
embedding similarity against managed topic names. Text edits invalidate cached
vectors/similarities and mark analysis as needing re-analysis. Marks overrides
invalidate paper validation. Trends use exam year/month/day, with undated papers
last and paper ID as a stable tie-breaker; unknown levels are never assigned L1.

Migration `embeddings_20261109` adds cached vector metadata and managed-topic flags.
`alembic downgrade reviewers_20261109` discards vectors and flags, retaining the
questions and topic names. Apply migrations before starting the worker.
