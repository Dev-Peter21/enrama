# F02 Python setup implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution.

**Goal:** Deliver issue #3 on `develop` as an installable package and a verified
Python 3.12 development environment.
**Architecture:** One src-layout package with no runtime dependencies or entry
points. Hatchling builds explicitly selected files; uv locks development tools
and a separate hashed constraints file freezes isolated build dependencies.
**Tech stack:** Python 3.12, uv, Hatchling, pytest, Ruff, strict mypy.
**Spec:** [Accepted setup](../../development-setup.md).

## Global constraints

No CLI, configuration engine, generator, themes, CI workflow, editor, PyPI
publication, GitHub release, or merge to `main`. Version: `0.1.0.dev0`.
The 3.12–3.15 matrix is a future F03 verification target.

## Review focus

- Missing package files: imports must work from each installed archive outside
  the checkout, with isolated Python invocation.
- Developer dependency leakage: installed metadata and environment must have no
  runtime dependency or CLI entry point.
- Accidental client/secret inclusion: build a synthetic checkout with decoy files
  and inspect both archives against explicit inclusion rules.
- Unrepeatable builds: compare both archive hashes across independent builds
  using exact hashed build constraints.
- Stale locks: verify locked synchronization rejects missing/changed locks
  without regenerating them.

### Task 1: Package, tools, and distribution acceptance

1. Bootstrap pinned uv and Python 3.12 in temporary directories.
2. Add real integration tests in `tests/integration/test_distribution.py` and
   `tests/integration/test_locking.py`; observe a failing package build before
   introducing package configuration.
3. Add `.python-version`, `pyproject.toml`, `src/enrama/__init__.py`,
   `build-constraints.txt`, and a real generated `uv.lock`.
4. Run locked sync, Ruff lint/format, strict mypy, and pytest. Inspect wheel and
   source archives and install each into its own external environment.
5. Update README, CONTRIBUTING, development/testing documentation, changelog,
   and verification evidence; repeat the documented workflow from a clean copy.
6. Commit scoped implementation on `develop`.

### Task 2: Review and delivery

1. Obtain one independent review of the complete diff against the approved spec.
2. Resolve in-scope findings, rerun relevant checks, record evidence.
3. Push `develop` and update issue #3 with implementation evidence, leaving the
   issue open for maintainer acceptance. Do not publish to PyPI.
