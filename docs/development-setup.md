# Python development setup

Status: **implemented F02 foundation on `develop`**, following the design
approved on 2026-10-22 for [issue #3](https://github.com/Dev-Peter21/enrama/issues/3).
This repository supplies an importable package, locked developer tools, real
packaging tests, and local build commands. See the [verification record](verification/f02.md).

## Branch and delivery boundary

Source-code implementation must integrate into `develop`. Implementation
branches, when used, start from and target `develop`. The repository's default
branch remains `main`; F02 is delivered on `develop`.

The implemented F02 scope is an installable, importable Python package and
its developer tooling. Functional CLI commands, YAML loading/models, generation,
themes, preview, and the editor remain their existing roadmap tasks. Do not add
placeholder commands that imply the accepted CLI contract is already implemented.
F02 does not publish to PyPI or create a public release.

C01 subsequently adds the [configuration models](configuration.md), using
`pydantic>=2.14.1,<3` and `langcodes==3.5.1` at runtime. The lock resolves
Pydantic 2.14.1; the exact langcodes pin fixes its bundled IANA registry snapshot.
The source still has no YAML loader, CLI, or generator. F02-only statements
below about the original initializer-only package describe that foundation
snapshot; current inclusion and installation checks also cover C01's modules
and `py.typed` marker. See [C01 verification](verification/c01.md).

## Python versions

| Concern | Accepted choice |
| --- | --- |
| Minimum package requirement | Python `>=3.12` |
| Local development interpreter | Python `3.12` |
| Committed `.python-version` | `3.12`, allowing compatible security/patch updates |
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
  in the distribution metadata.
- Select explicit package inclusion rules for the wheel and source distribution.
  Include the package and required license/metadata, not local virtual environments,
  caches, credentials, or unrelated client data.

The intended name is not a PyPI reservation or trademark clearance. O01 remains
open: namespace availability was checked (PyPI returned 404 on 2026-10-22),
but ownership/name clearance must be settled before reservation or publication.
Do not silently rename the distribution while keeping conflicting documentation.

The initial implementation supplies these files (only meaningful tests are created):

```text
.python-version
pyproject.toml
uv.lock
src/enrama/
  __init__.py
build-constraints.txt
tests/
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
commit `.python-version`, `pyproject.toml`, and `uv.lock`. No global package
installation is part of the project workflow.

Use `uv sync --locked` for verification. A stale or missing lockfile must fail
that verification instead of being silently repaired. Use `uv run --locked` for
the documented quality/test commands, so normal checks cannot rewrite the lockfile.
Changing dependency declarations and regenerating the lockfile is an intentional
maintenance action, reviewed together in one change.

The selected uv version is **0.13.5**, enforced by `tool.uv.required-version`.
F03 must use this same version. Install it with the official standalone installer
([installation guide](https://docs.astral.sh/uv/getting-started/installation/)):

```console
curl -LsSf https://astral.sh/uv/0.13.5/install.sh | sh
uv --version
uv python install 3.12
```

The installer creates a user-local uv executable; it does not install packages
into system Python. Follow its PATH instructions. Then run the project commands
below; `.python-version` selects Python 3.12 for the local `.venv/`.

Routine dependency updates are intentional maintenance: edit declarations, run
`uv lock`, review `uv.lock`, and repeat all checks on Python 3.12. Normal checks
use `--locked` and cannot silently refresh the lock. No global Python package
installation is required.

## Build reproducibility and artifacts

Use **Hatchling** as the backend and **uv** as the build frontend. Build both a
wheel and a source distribution. Their creation is separate from publishing them.

`uv.lock` freezes the development graph, not the isolated backend environment.
`build-constraints.txt` pins Hatchling **1.32.4** and all five transitive build
dependencies with SHA-256 hashes. The verified build invocation is:

```console
uv build --python 3.12 --build-constraint build-constraints.txt --require-build-hashes
```

This builds the sdist and then the wheel from that sdist. Both archives are
written to `dist/`. The constraints file is included in the sdist. Plain
`uv build` works, but does not apply all the reviewed transitive constraints;
use the invocation above for verification. Build hash verification is marked
experimental by uv 0.13.5; the uv pin makes that choice explicit.

Build constraints can be intentionally regenerated after updating the backend
pin in `pyproject.toml`:

```console
uv pip compile - --python-version 3.12 --universal --generate-hashes --no-annotate --no-header --output-file build-constraints.txt <<'EOF'
hatchling==1.32.4
EOF
```

Keep the input backend version equal to `build-system.requires`.
Review every changed version/hash and rerun artifact installation and repeatable
build tests. The development editable install from `uv sync` is not the evidence
for archive installation: pytest builds and installs each archive separately.

The wheel explicitly includes the initializer, C01 modules, `py.typed`, and generated
metadata; the sdist includes these sources, `pyproject.toml`, README, license, and
build constraints. Hatchling also includes `.gitignore` and `PKG-INFO`. Tests, client
files, environments, caches, and credentials are not distributed. Extend the
inclusion lists and content tests together when future tasks add package files.

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

## Developer commands

Run from a clean `develop` checkout with uv 0.13.5 on PATH:

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests scripts
uv run --locked pytest
uv build --python 3.12 --build-constraint build-constraints.txt --require-build-hashes
```

The tests create temporary builds and two consumer environments outside the
checkout. Each consumer uses isolated Python (`-I`) and verifies the installed
import location, metadata, MIT license, declared runtime dependencies without
developer tools, and absence of CLI entry points. C01 also validates models from
each installed archive. Further tests compare archive hashes, reject synthetic private
files, and exercise missing/stale lock rejection without changing the inputs.
uv must remain on PATH. Downloads from PyPI may be needed for pinned tools;
no test uploads artifacts or requires publishing credentials.

## Implementation acceptance and evidence

The [verification record](verification/f02.md) records local Python 3.12 evidence for:

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

The accepted [F03 CI design](continuous-integration.md) adds Linux/Python
3.12–3.15 plus macOS and Windows/Python 3.12 verification, and one Linux/3.12
quality job. Its workflow is implemented on `develop`; actual runs are
recorded in the [F03 verification record](verification/f03.md).
Full CLI and theme verification follows the later tasks in the
[testing strategy](testing.md).

## References

- [uv: dependency groups and published requirements](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- [uv: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [uv: distributions and isolated build constraints](https://docs.astral.sh/uv/concepts/projects/build/)
- [Hatchling wheel configuration](https://hatch.pypa.io/latest/plugins/builder/wheel/)
- [PyPA: src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyPA: version specifiers and development versions](https://packaging.python.org/en/latest/specifications/version-specifiers/)
