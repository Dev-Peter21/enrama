# Changelog

Notable changes will be recorded here. Entries describe the state of this
repository; a roadmap target does not imply that a release exists.

## Unreleased

### Added

- C03 implementation on `develop`: deterministic validation-mode Draft 2020-12
  artifact, pure model-derived generation, an internal generation/check helper,
  CI staleness gate and dev-only schema validation tests. Includes source-archive
  artifact delivery, unchanged runtime dependencies, manual client/provenance
  documentation and actual VS Code/Red Hat YAML provider/offline verification.
  No product CLI, site generator, updater, package publication or deployment.

- Accepted C03 JSON Schema/VS Code design: model-derived validation-mode Draft
  2020-12, structural editor assistance with C01/C02 authority, a local schema
  copy per client, stable v1 naming/exact revision provenance, and manual
  tool/schema updates in the same client commit. Documentation only; no schema
  artifact, generation tooling, dependencies or editor settings are delivered.

- C02 implementation on `develop`: bounded UTF-8/YAML parsing, isolated scalar
  policy, duplicate/unsafe-construct rejection, C01 validation with source-aware
  safe diagnostics capped at 20, and read-only file loading. Adds used PyYAML
  and dev-only stubs, hashed source-build inputs, unit/installed-consumer tests,
  and verification evidence. Accepted by the maintainer on 2026-10-23; issue #6
  is closed/completed and its existing Kanban card is Done. No CLI, generator,
  generated JSON Schema, or PyPI upload.

- Accepted C02 safe YAML loader/diagnostics design: explicit plain-data subset,
  no anchors/aliases/merges, bounded 1 MiB/32-container/10,000-node processing,
  up to 20 diagnostics with honest source locations, safe English messages,
  and acceptance cases. This records the original design; implementation and
  evidence are recorded above.

- C01 implementation on `develop`: six strict Pydantic YAML v1 data models,
  URL/language/lexical-path validators, stable presentation catalogs, model tests,
  and isolated wheel/sdist model validation. Adds used Pydantic and pinned
  langcodes registry-data dependencies, without YAML loading or CLI/generation.

- Accepted C01 YAML v1 contract: strict models/field policy, defaults and limits,
  separate links/socials with shared ID uniqueness, optional public site URL,
  URL and language validation, local image references, platform/icon catalogs,
  examples, and future acceptance cases. This is documentation only; no models,
  loader, schema, assets, or CLI/generator behavior are implemented by this change.

- F03 implementation on `develop`: SHA-pinned read-only CI, Linux/Python
  3.12–3.15 plus macOS and Windows/3.12 verification, explicit managed Python
  patches, quality checks, isolated distribution tests, seven-day reports and
  artifacts, and fail-closed interpreter/JUnit/archive evidence gates.

- Accepted F03 CI design: one Linux/Python 3.12 quality job, six mandatory
  test/build/install environments (Linux 3.12–3.15, macOS 3.12, Windows 3.12),
  PR/push triggers for `develop` and `main`, locked tooling, restricted
  permissions, pinned actions, and seven-day reports/artifacts. This documents
  the original design; implementation and actual run evidence are recorded above.

- F02 implementation on `develop`: importable `enrama` `0.1.0.dev0`, Python 3.12
  selector, uv lock, Hatchling metadata, hashed isolated-build constraints,
  Ruff/strict mypy/pytest tooling, and artifact/locking integration tests.

- Accepted F02 setup design: Python 3.12 local, target 3.12–3.15 matrix,
  `0.1.0.dev0`, src-layout packaging, dependency/build constraints, quality tools,
  and artifact-verification requirements.
- Accepted F01 CLI/filesystem specification: fixed `dist/` output, explicit
  configuration paths, safe overwrite/cleanup and concurrency rules, manual
  local preview, exit codes, and acceptance examples for all four commands.
- Initial product definition, architecture, draft YAML contract, theme and
  deployment documentation.
- Roadmap for the `0.1.0` CLI and static generator, followed by the `0.2` local
  editor, with task dependencies and acceptance criteria.
- Contribution, conduct, support, security, and governance policies.
- MIT license, repository housekeeping files, and issue/PR templates.
- Published MVP backlog: five milestones (M0–M4), a completed foundation record,
  17 planned implementation tasks, and a final acceptance issue, tracked in the
  existing EnRama Project Kanban with priorities and native dependencies.

The CLI, generator, themes, and editor remain planned. No package or release
has been published.

### Fixed

- Restored visibility of all 19 original MVP issues in the EnRama Project
  Kanban, preserving saved fields, milestones, and native dependencies without
  duplicate issues or Project associations.
