# Dependency verification — 2026-11-09

The initial npm audit reported 18 affected frontend dependencies (3 critical,
6 high, 9 moderate). The initial OSV backend audit reported 96 advisory matches
across nine packages (some advisory aliases were duplicated by the service).
Neither audit was suppressed.

Backend fixes: aiohttp 3.14.4, certifi 2026.10.18, filelock 4.2.1, Mako 1.4.2,
multidict 6.9.1, Pillow 13.0.0, pyasn1 0.6.5, setuptools 84.1.0, urllib3 2.8.0,
and yarl 1.25.1 as required by aiohttp. The hashed lock includes all transitive
dependencies, SQLAlchemy asyncio/greenlet, and CPU Torch artifacts. NumPy 2.3.5
aligns the declaration with the environment used for the passing test suites.

Frontend fixes upgrade Vite, Vitest/coverage, the React build plugin, and the
TypeScript ESLint packages, plus compatible npm patch updates. A scoped
`@typescript-eslint/typescript-estree` override selects minimatch 11.0.1. Its
exported matcher API matches the consumer and supports the tested Node 20 runtime;
this avoids downgrading the parser to the old version suggested by npm.
Vitest workers are capped at two to avoid resource contention in constrained
development and CI environments; all test files and assertions remain enabled.

Final backend audit: **121 packages, zero known vulnerabilities, zero skipped**.
Command (from backend):
`uvx --from pip-audit pip-audit -r requirements.lock --disable-pip --no-deps --vulnerability-service osv --timeout 60 --format json`.
`--no-deps` audits the complete compiled lock directly; no transitive package is
omitted. The first PyPI advisory request timed out, so OSV supplied the completed
audit. Final npm install audit: **zero vulnerabilities**. TLS verification was
enabled for registry requests. `pip check` reported no broken requirements.

Docker and Compose YAML syntax was parsed successfully, but container validation
could not run. Exact command and output:

```text
$ docker compose config
/bin/bash: line 1: docker: command not found
```

The added PR workflow has not been run remotely from this workspace. These
results do not establish production readiness or replace a container/MySQL smoke
test on a machine with Docker. Native OCR model execution also depends on the
Paddle runtime and model availability; regression tests validate page selection,
configured rendering DPI, and pixel-array handling with a controlled OCR engine.
