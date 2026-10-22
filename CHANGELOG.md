# Changelog

Notable changes will be recorded here. Entries describe the state of this
repository; a roadmap target does not imply that a release exists.

## Unreleased

### Added

- Accepted F03 CI design: one Linux/Python 3.12 quality job, six mandatory
  test/build/install environments (Linux 3.12–3.15, macOS 3.12, Windows 3.12),
  PR/push triggers for `develop` and `main`, locked tooling, restricted
  permissions, pinned actions, and seven-day reports/artifacts. This documents
  future behavior; workflow implementation and execution remain pending.

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
