# R03 manual publication implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh whole-branch reviewer. Implement the accepted contract without dispatching publication.

**Goal:** Implement and review `publish.yml` on develop, preserving separately authorized main integration, tags and actual publication.

**Architecture:** A stdlib-only release controller verifies the exact main revision, successful preparation run, artifact identity/digest and immutable bundle. Read-only inspection precedes environment-gated OIDC upload; public wheel/sdist consumers precede separately environment-gated, idempotent tag/release finalization. No stage rebuilds Enrama archives.

**Tech Stack:** Python 3.12+, uv 0.13.5, GitHub Actions/CLI, production PyPI JSON/simple APIs, pytest, Ruff, mypy and actionlint.

**Spec:** `docs/releasing.md`, `docs/release-preparation.md`, accepted setup: dedicated `publish.yml`, environment `pypi-production`.

## Global constraints

- Target develop; no main integration, tag creation, token exchange, workflow dispatch or publication during implementation.
- First distribution `enrama==0.1.0`; tag `v0.1.0`; retain original wheel/sdist/schema/provenance/checksums.
- Workflow dispatch only; require explicit source/run/artifact/digest-bound authorization and exact main workflow/source identity.
- OIDC only in the environment-approved upload job; contents write only in approved finalization; no permanent tokens.
- Linux Python 3.12–3.15; macOS/Windows Python 3.12; preserve POSIX-only preview boundary.
- Stop on unavailable originals, conflicting remote bytes, unsupported source or ambiguous network results. Retry only missing identical-version files/assets; no overwrite, rename, bump, yank or deletion.
- Repository docs stay in English under docs, including the review; user-requested develop delivery supersedes generic GitFlow/Windows documentation paths in the review skill.

## Review focus

- An artifact from the wrong/failed/expired run or modified ZIP cannot reach upload.
- A stale main SHA or floating authorization cannot survive an approval wait.
- Partial PyPI state, unknown files, yanked files and HTTP errors fail closed; identical files are skipped without OIDC if complete.
- Failed public consumption blocks tag/release finalization; public installation never substitutes the local candidate.
- Existing tags/releases/assets are checked without moving tags, clobbering assets or recreating original bytes.

### Task 1: Candidate and remote-state gates

**Files:** create `scripts/publish.py`, `scripts/_publish_remote.py`, `tests/integration/test_publish.py`.
**Interfaces:** `publish.py` CLI commands `candidate`, `stage`, `public-files`, `finalize`; environment inputs carry exact source SHA, preparation run ID, artifact ID, artifact ZIP SHA-256 and authorization phrase. Reuse `release.verify`; network boundaries are separately testable functions.

- [ ] Write offline tests for exact identity/context, successful preparation/CI/jobs, ZIP confinement, provenance, public missing/partial/complete/conflicting state and idempotent tag/release recovery; observe RED.
- [ ] Implement bounded transport and deterministic state transitions; reject conflicts before any mutation; test GREEN.
- [ ] Commit the gates and tests.

### Task 2: Manual orchestration and actual public consumers

**Files:** create `.github/workflows/publish.yml`; modify `tests/integration/test_distribution.py`; extend `tests/integration/test_publish.py`.
**Interfaces:** `candidate` writes verified `reports/candidate`; `stage` writes only missing archives to `reports/upload` and positive evidence; public consumers explicitly resolve `enrama==0.1.0` from production PyPI without cache/local substitution; `finalize` requires successful current-run public jobs.

- [ ] Write failing workflow permission/trigger/gate tests and public-install command tests.
- [ ] Add read-only inspect, environment-approved upload, six public verification jobs and environment-approved finalization; all actions pinned to reviewed existing SHAs.
- [ ] Verify actionlint, offline orchestration tests, quality/schema and full regression; commit.

### Task 3: Documentation, independent review and develop delivery

**Files:** create `docs/publication.md`, `docs/release-notes/0.1.0.md`, `docs/verification/r03-publication.md`, English timestamped `docs/reviews/*`; update release/setup/index/changelog wording accurately.

- [ ] Document exact future dispatch/approval/retry commands, evidence, retention and limitations; no publication claim or private account security data.
- [ ] Review the complete implementation once with a fresh reviewer; fix material findings with RED/GREEN tests and rerun regression.
- [ ] Fetch/reconcile develop, integrate/push only develop, verify exact delivered CI and report evidence; main/tag/publication remain untouched.
