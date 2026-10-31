# R03 Technical Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prepare the unreleased 0.1.0 package and a manual, credential-free artifact preparation/verification workflow on develop.

**Architecture:** Preserve the generator/CLI behavior. A stdlib release helper validates source identity and creates/verifies one immutable archive/schema/hash/provenance bundle. The manual workflow builds once and reuses that bundle in the agreed compatibility matrix via the existing installed-consumer tests.

**Tech Stack:** Python 3.12+, uv 0.13.5, Hatchling, pytest, Ruff/mypy, SHA-pinned GitHub Actions.

**Spec:** [Accepted R03 contract](../../releasing.md); maintainer request on 2026-10-31 authorizes technical preparation only.

## Global Constraints

- First version 0.1.0; intended future tag v0.1.0; YAML schema_version 1.
- Python verification: Linux 3.12–3.15; macOS/Windows 3.12; Linux 3.12 quality.
- Integration into develop only. No main integration, tags, releases, external publisher/environment setup, uploads or public deployment.
- workflow_dispatch only; read permissions; no publisher step, environment or id-token permission.
- Main-source requirement applies to the future manual release-preparation run. Local develop rehearsals must explicitly report publication_authorized false and never claim main/production readiness.
- Canonical wheel/sdist bytes are reused; test builds may remain disposable. TestPyPI stays separate and optional.

## Review Focus

- Wrong SHA, dirty checkout or non-main dispatch must fail before preparing a remotely releasable candidate (Task 2 source-gate subprocess tests).
- Mixed versions, missing/extra archives, unsafe links and existing output must fail without overwriting source/evidence (Task 2 real fixture tests).
- Altered payload, schema, provenance or checksum file must fail downloaded-bundle verification (Task 2 tamper tests).
- Platform consumers must install the supplied canonical archives, not silently rebuild or fall back when the bundle is invalid (Task 2 fixture integration).
- An unreleased 0.1.0 must not be presented as available on PyPI or supported production software; dispatch cannot be exercised before workflow reaches default main (Task 3 docs and final review).

## Task 1: Prepare package version and metadata

**Files:** pyproject.toml, uv.lock, tests/integration/test_distribution.py, tests/integration/test_locking.py.

**Interfaces:** Installed metadata/CLI report 0.1.0; existing archive inventory and lock-failure tests keep their behavior.

- [x] Change the installed-consumer expected version to 0.1.0 and run its wheel case; observe old metadata failure.
- [x] Set version 0.1.0, appropriate Beta maturity and Python 3.12–3.15 classifiers; refresh only the project's lock entry using pinned uv.
- [x] Update exact dist-info inventory and stale-lock mutation for the prepared version. Preserve intentional historical-format fixture cases.
- [x] Run installed consumers and lock tests; commit the independently verified metadata change.

## Task 2: Canonical release preparation and verification

**Files:** scripts/release.py, tests/integration/test_release.py, tests/integration/test_distribution.py.

**Interfaces:** release.py subcommands check-source/bundle/verify take expected full source SHA and version; bundle receives archive/source/output paths, verify receives the downloaded bundle. Existing archives fixture optionally consumes ENRAMA_RELEASE_BUNDLE, verifying it before installation.

- [x] Write subprocess tests using real temporary Git repositories and tiny wheel/sdist fixtures: identity/dirty/main gates; exact metadata; unchanged payload copy; protected existing output; wrong/missing/extra/linked inputs; manifest/checksum/payload tampering.
- [x] Run and observe missing-helper failures. Implement a stdlib helper with strict expected names/version/SHA, content metadata checks, exclusive fresh output and no cleanup of uncertain data.
- [x] Write release.json with exact source/run/version/file hashes and publication_authorized false, plus schema and SHA256SUMS. Verify complete inventory and matching metadata/digests on download.
- [x] Extend the installed-consumer fixture to verify and consume an explicit bundle, failing rather than falling back. Run actual built wheel/sdist/PyYAML-source consumers with that bundle.
- [x] Run focused helper tests, quality checks and full suite. Commit the verified deliverable.

## Task 3: Manual workflow, documentation and delivery

**Files:** .github/workflows/release.yml; README.md; CHANGELOG.md; SECURITY.md; SUPPORT.md; docs/releasing.md; docs/release-preparation.md; docs/verification/r03-preparation.md; related current documentation links/examples.

**Interfaces:** Manual main dispatch takes expected SHA; requires exact main push CI success, builds one canonical set and uploads it for six consumer jobs. Reports retain actual environment/JUnit evidence. No publication-capable job is included.

- [ ] Add workflow_dispatch-only preparation/verification using read permissions and reviewed full action pins. Require main, expected SHA and successful exact-source CI; run quality/schema, build once, bundle, then verify/install the same bytes in all six environments.
- [ ] Validate with actionlint, parse inputs/permissions, run the actual helper/build/consumer commands locally. Do not fabricate a main dispatch or alter default branch/trigger to test it.
- [ ] Document developer rehearsal commands, immutable provenance, retention/manual recovery, version 0.1.0 still unpublished, future support policy and deferred external/main/publication gates. Keep historical verification records historical.
- [ ] Run locked quality/schema/full tests, Markdown checks and constrained build. Request one fresh read-only whole-change review; fix concrete important findings with regression tests.
- [ ] Integrate verified changes to develop, push as authorized delivery, retain evidence and leave issue #17 open. Report actual CI/dispatch boundaries and recommend separately authorized main integration and external setup next.
