# Python development setup

Status: **accepted F02 design**, approved on 2026-10-22 for
[issue #3](https://github.com/Dev-Peter21/enrama/issues/3).
This document defines the setup to implement later. It does not deliver a
Python project, installed dependencies, lockfile, executable tests, or build
artifacts. F02's implementation acceptance criteria remain pending.

## Branch and delivery boundary

Future source-code implementation must integrate into `develop`. Implementation
branches, when used, start from and target `develop`. The repository's default
branch remains `main`; this documentation does not authorize starting code work.

The implemented F02 scope will be an installable, importable Python package and
its developer tooling. Functional CLI commands, YAML loading/models, generation,
themes, preview, and the editor remain their existing roadmap tasks. Do not add
placeholder commands that imply the accepted CLI contract is already implemented.
F02 does not publish to PyPI or create a public release.

## Python versions

| Concern | Accepted choice |
| --- | --- |
| Minimum package requirement | Python `>=3.12` |
| Local development interpreter | Python `3.12` |
| Future `.python-version` | `3.12`, allowing compatible security/patch updates |
| Target compatibility matrix | Python `3.12`, `3.13`, `3.14`, and `3.15` |
| Tool syntax/type-checking baseline | Python `3.12` |

F02's initial setup must work locally on Python 3.12. F03 will automate the
target matrix; it must actually execute checks on each selected interpreter.
The agreed matrix is a verification target, not evidence that compatibility has
already passed. Future Python versions require validation before a support claim.

Record the actual interpreter patch version used in verification. The minor
version selector alone is not a promise of identical interpreter binaries across
machines. Raising the minimum Python version requires a later compatibility decision.

## Package metadata and layout

- One distribution named `enrama` and one import package named `enrama`.
- Use the `src/` layout, with package code under `src/enrama/`.
- Start with **`0.1.0.dev0`**, a development version. Reserve `0.1.0` for the
  completed MVP; no version is published by accepting this document.
- Keep package version and metadata in `pyproject.toml` as the single source
  of truth. Do not maintain a separate manually synchronized version constant.
- Include the English README, MIT license declaration/license file, project
  description, Python requirement, and canonical repository/documentation links
  in the eventual distribution metadata.
- Select explicit package inclusion rules for the wheel and source distribution.
  Include the package and required license/metadata, not local virtual environments,
  caches, credentials, or unrelated client data.

The intended name is not a PyPI reservation or trademark clearance. O01 remains
open: verify the namespace/ownership before public package metadata or publication.
Do not silently rename the distribution while keeping conflicting documentation.

The initial implementation is expected to introduce these files, which **do not
exist as part of this documentation delivery**:

```text
.python-version
pyproject.toml
uv.lock
src/enrama/
  __init__.py
tests/
  unit/
  integration/
```

Only introduce meaningful test files and package modules as needed. The fuller
[architecture layout](architecture.md#planned-source-layout) is a later product
target, not a requirement to create empty subsystems in F02.

## Dependency responsibilities

| Category | Policy |
| --- | --- |
| Runtime | Introduce Typer, PyYAML, Pydantic v2, and Jinja2 when the implementation starts using each dependency |
| Development | One `dev` dependency group containing pytest, Ruff, and mypy |
| Build | Hatchling declared as the build backend/build dependency, not a runtime dependency |
| Resolved development environment | A committed `uv.lock` maintained with the dependency declarations |
| Future editor | FastAPI and any round-trip YAML writer remain outside F02 and the 0.1 runtime |

Do not put test, lint, or typing tools in the published package's runtime
requirements. Add type stubs or other tooling dependencies only when required by
the implemented code, with an explicit reason and an updated lockfile.

`pyproject.toml` describes the package and its compatible dependency requirements;
`uv.lock` records resolved versions for the development/CI workflow. Package
consumers must not be required to use uv or install Enrama's developer tools.
F02's initial importable skeleton need not declare unused runtime libraries.

## Environment, locking, and updates

Use uv to manage a project-local `.venv/`. Keep the virtual environment untracked;
commit `.python-version`, `pyproject.toml`, and `uv.lock` when implementation is
authorized. No global package installation is part of the project workflow.

Use `uv sync --locked` for verification. A stale or missing lockfile must fail
that verification instead of being silently repaired. Use `uv run --locked` for
the documented quality/test commands, so normal checks cannot rewrite the lockfile.
Changing dependency declarations and regenerating the lockfile is an intentional
maintenance action, reviewed together in one change.

Select, record, and pin the uv version during implementation, and use that same
version in F03 automation. Select compatible exact resolved versions at that
time; this design does not invent unverified version numbers or a fake lockfile.
Routine dependency updates must rerun the relevant checks and preserve the
Python 3.12 baseline.

## Build reproducibility and artifacts

Use **Hatchling** as the backend and **uv** as the build frontend. Build both a
wheel and a source distribution. Their creation is separate from publishing them.

Do not claim `uv.lock` alone freezes an isolated build: the backend and its
transitive build dependencies also need explicit version control. During F02
implementation, record the selected build-tool versions and apply reviewed build
constraints; use hash verification where specified by the chosen build workflow.
Any constraint files must be maintained with the backend configuration. The
implementation must document the exact reproducible build invocation it verifies.

The baseline `uv build` command below describes the build operation, not a claim
that every isolated build input is already pinned. Record interpreter, uv,
backend/build dependency versions, and the verified source revision with results.

The repository's packaging `dist/` holds wheel/source archives. A client project's
`dist/` holds a generated static website under the [F01 contract](cli-contract.md).
These are different project contexts; packaging artifacts must not be confused
with a generated client site or deployed as one.

## Quality tools

- **Ruff:** the only formatter, with a target line length of 88 and Python 3.12
  syntax compatibility. Use it for linting as well; avoid a second formatter or
  a redundant import-formatting tool.
- **mypy:** strict mode, targeting Python 3.12, covering package code and tests.
  Address typing problems rather than globally hiding missing imports/errors.
- **pytest:** meaningful unit/integration and packaging checks. No arbitrary
  coverage percentage is established by F02. Report positive executed counts;
  zero collected tests is not passing acceptance evidence.

Put the tool configuration in `pyproject.toml`. Keep F02 focused: an additional
task runner, container workflow, or parallel environment-management stack is not
required for this setup.

## Planned developer commands

The following commands are the **future baseline**, not current installation
instructions. They must not be reported as executed successfully in this
documentation-only stage:

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests
uv run --locked pytest
uv build
```

The implementation must supply the package, configuration, lockfile, and real
tests that make those commands valid. Add the selected build constraints to the
documented build invocation as described above. Artifact installation checks
use separate clean environments rather than replacing the developer environment.

## Implementation acceptance and evidence

F02's software delivery is complete only when the implementer records evidence for:

1. A clean checkout on Python 3.12 synchronizing the locked development environment.
2. The required tools passing with the accepted configuration; ordinary checks
   leave the committed lockfile unchanged.
3. Positive pytest counts for meaningful package/installation checks.
4. Successful creation and inspection of both wheel and source distribution.
5. Installation of each artifact into its own isolated environment, using a
   working directory outside the source checkout and no editable install or
   `PYTHONPATH` workaround.
6. Importing `enrama` from the installed artifact, not from the repository's
   `src/` directory, and verifying its distribution name/version and license.
7. Distribution metadata reporting `0.1.0.dev0` and Python `>=3.12`, with no
   development tools accidentally required at runtime.
8. Reproduction of the documented commands and the selected build constraints,
   with the source revision and actual tool/interpreter versions recorded.
9. Implementation integrated into `develop`, without publishing a package/release.

F03 automates the agreed 3.12–3.15 matrix and quality/packaging checks. Its CI
workflow is a separate delivery; this design neither adds it nor claims it passed.
Full CLI and theme verification follows the later tasks in the
[testing strategy](testing.md).

## References

- [uv: dependency groups and published requirements](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- [uv: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [uv: distributions and isolated build constraints](https://docs.astral.sh/uv/concepts/projects/build/)
- [Hatchling wheel configuration](https://hatch.pypa.io/latest/plugins/builder/wheel/)
- [PyPA: src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyPA: version specifiers and development versions](https://packaging.python.org/en/latest/specifications/version-specifiers/)
