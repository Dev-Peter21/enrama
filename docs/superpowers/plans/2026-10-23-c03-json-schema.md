# C03 JSON Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver issue #7's generated JSON Schema and verified local VS Code workflow on develop.

**Architecture:** A pure configuration module serializes EnramaConfig's validation-mode JSON Schema with a Draft 2020-12 declaration. An internal repository script writes/checks the fixed artifact; tests and CI enforce drift without adding Enrama CLI commands or a second validation engine. Real editor verification uses a temporary client folder and existing official VS Code installation.

**Tech Stack:** Python 3.12+, existing Pydantic/uv, dev-only jsonschema 4.26.0 and types-jsonschema 4.26.0.20261006, pytest/Ruff/strict mypy; VS Code with Red Hat YAML.

**Spec:** [Accepted C03 contract](../../json-schema.md), [C01](../../configuration.md), [C02](../../yaml-loader.md).

## Global Constraints

- Use the existing clean develop checkout; user authorized implementation directly. Version remains 0.1.0.dev0; native execution, one fresh final review. No further implementation checkpoint is needed.
- Derive from EnramaConfig validation mode; JSON Schema Draft 2020-12. No handwritten field contract or cloned URL/language/path/ID/parser logic.
- Fixed checked artifact schemas/enrama-v1.schema.json, UTF-8, deterministic bytes, internal references only; no timestamp, machine-path, live HEAD or invented dynamic defaults.
- Keep C01/C02 semantic behavior unchanged. Schema is structural assistance with documented trimming/strict-type/runtime-validator gaps; no YAML mutation/default filling.
- Local schema/client settings/provenance tracked in client Git. Exact version/source matching, full source commit for ambiguous dev snapshots; update tool reference and schema manually in the same client commit.
- Single-folder VS Code settings map ./schemas/enrama-v1.schema.json to /enrama.yaml; yaml.yamlVersion 1.2, yaml.validate true. No top-level $schema in client YAML. Test actual extension completion/hover/diagnostics and offline local schema use.
- No product CLI, generator, updater, visual editor/service, client deployment, package release or PyPI upload. Only development helper arguments are introduced.
- Preserve seven-job existing CI matrix, positive test counts, isolated archives/runtime dependencies, build constraints and lock discipline. Issue stays open pending maintainer acceptance.

## Review Focus

- Generation/check must work independent of cwd, detect missing/stale bytes without mutating in check mode, and surface operational failures honestly.
- Schema must follow model constraints/default factories without adding runtime policy or external references; editor help may not pretend equivalent URL/language/ID validation.
- Artifact copies must remain useful offline; source provenance must not create a self-referential HEAD/timestamp or floating-version mismatch.
- New dev validation libraries must not enter installed runtime; explicit archive inventories must retain all new used modules and the reviewed artifact where distributed.
- Real VS Code association must target the client's config only, give genuine completion/hover/errors, and exercise the approved local relative path without touching user projects/settings.

## Task 1: Pure schema generation and checked artifact

**Files:** Create src/enrama/config/schema.py, schemas/enrama-v1.schema.json, tests/unit/test_schema.py; modify pyproject.toml/uv.lock and tests/integration/test_distribution.py.

**Interfaces:** generate_schema() -> bytes in enrama.config.schema returns deterministic UTF-8 JSON with a trailing newline, two-space indent, sorted keys and $schema https://json-schema.org/draft/2020-12/schema. Internal type/metadata generation delegates entirely to EnramaConfig.model_json_schema(mode='validation').

- [x] Add used development-only jsonschema==4.26.0 and types-jsonschema==4.26.0.20261006; sync the reviewed lock.
- [x] Write tests first for valid Draft 2020-12, local refs, independent minimal/expanded inputs, required/null/unknown/type/version/catalog/pattern/list/length failures and immutable input/default behavior. Tests call the missing generate_schema API; observe missing-feature failures.
- [x] Implement pure generation, create the checked artifact from that function, and test byte-for-byte drift agreement, repeatability, model-described hover text, omitted social-label dynamic default and no derived social icon input.
- [x] Add characterization cases showing JSON Schema accepts runtime-only invalid URL/language/path/global IDs and differs on trimmed-length/strict numeric cases; C01/C02 must retain their existing outcomes.
- [x] Extend exact wheel/sdist module inventories, include the schema artifact in the source distribution (ordinary client consumption remains the repository copy), and verify jsonschema/stubs stay absent in isolated installed runtime. No duplicate artifact is added to wheel; the pure generator remains importable there.
- [x] Run focused tests, full suite and quality checks; commit this independently testable generation/artifact delivery.

## Task 2: Developer generation/check tool and CI gate

**Files:** Create scripts/schema.py, tests/integration/test_schema_tool.py; modify .github/workflows/ci.yml and developer/schema docs.

**Interfaces:** uv run --locked python scripts/schema.py writes the fixed repository artifact. --check returns0 for current bytes,1 for missing/stale/operational failure; usage errors2. It resolves the repository from its own file, never cwd; check mode performs no writes. This is not an enrama CLI command.

- [x] Write failing subprocess tests using copied helper paths/temporary roots: missing output/write/repeatable output, current/stale/missing checks with unchanged bytes, invocation from unrelated cwd, and unreadable/unwritable/nonregular output. Expected failures must be bounded readable messages with no successful result on failure.
- [x] Implement the minimal internal helper and run tests. Use the pure generate_schema bytes; no duplicated field serialization. Reject symlink output directory/file to avoid accidental replacement outside the developer checkout.
- [x] Add a quality job check step invoking --check; all existing six verification environments also run the artifact drift test. Document exact generation/check commands, client copy/provenance and manual update steps without claiming a published version.
- [x] Verify all tests, quality, --check, and constrained wheel/sdist build; commit.

## Task 3: Actual editor verification, evidence and delivery

**Files:** Update docs/json-schema.md, README/docs index/development/testing/architecture/configuration/roadmap/decision/changelog references as needed; create docs/verification/c03.md. Temporary client/profile/evidence lives under /private/tmp or ignored reports, never user client repositories.

- [x] Create a temporary client with the committed local schema, approved workspace settings, representative YAML and explicit provenance. Use the existing /Users/pedroivanmoauro/soft/Visual Studio Code.app, isolated user-data/extensions if feasible; record actual editor and Red Hat YAML versions. Never alter the user's existing projects/configuration.
- [x] Exercise the actual editor using official VS Code Extension Host/provider APIs (see ledger ruling): correct schema association, theme/catalog completion, model-derived hover and representative structural errors. Verify local/offline loading with remote schema requests blocked for the isolated editor process/profile, plus an alternate config mapping; record actual observation rather than treating JSON parsing as editor evidence.
- [x] Run locked sync, lint/format, strict typing, full pytest/JUnit, --check and constrained builds; record positive counts, actual versions, schema SHA-256, archive inclusion and known runtime gaps.
- [x] Commit evidence, dispatch one independent whole-change review against the base, fix important findings with RED→GREEN regressions and a full suite, then publish develop. Verify all seven CI jobs and retained reports/archives. Update issue #7 with evidence, leaving it open for maintainer acceptance. No PyPI release/deployment.

## Self-review

Task1's byte API feeds the development helper and installed archive probes. Tests cover model-derived structure and intentionally separate runtime gaps. Task2 supplies the commands used in CI/docs; Task3 supplies actual editor evidence and cannot be replaced by schema validation alone. Packaging inclusion decisions preserve one checked artifact and no new runtime dependency. Existing user instruction authorizes implementation directly on develop.
