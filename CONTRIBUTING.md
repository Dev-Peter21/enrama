# Contributing to Enrama

Thank you for helping make independently hosted link pages easier to maintain.
Enrama is currently a documentation-only project. Product implementation has
not started; there are no setup, build, or test commands to run yet.

## Before you start

1. Read the [product definition](docs/product.md),
   [architecture](docs/architecture.md), and [roadmap](docs/roadmap.md).
2. Search existing [issues](https://github.com/Dev-Peter21/enrama/issues) and PRs.
3. For a product or public-contract change, open an issue describing the use
   case, scope, acceptance criteria, and relevant roadmap task.
4. Check the [decision log](docs/decisions.md). Ask the maintainer to resolve
   an open decision before implementing behavior that depends on it.

Documentation corrections can go directly to a small pull request. For
implementation, agree on a task's scope first. Avoid combining unrelated work.
The [Code of Conduct](CODE_OF_CONDUCT.md) applies to all participation.

## Local documentation workflow

```console
git clone https://github.com/Dev-Peter21/enrama.git
cd enrama
git switch -c docs/describe-your-change
```

Edit Markdown using relative links for files in this repository. Preview the
rendered result, check link targets and code fences, then run `git diff --check`.
Do not include real client data, secrets, personal contact details, or assets
you do not have permission to redistribute.

## Pull requests

- Explain the problem and the resulting behavior or documentation change.
- Reference the issue or roadmap task and list the checks you actually ran.
- Add a changelog entry when the change affects users or the public contract.
- Update related documentation in the same PR.
- Keep planned functionality clearly labeled until it is implemented.

Use a descriptive branch and commit name, such as `docs: clarify YAML versioning`.
The default branch is `main`. Future source-code implementation must integrate
into `develop`; implementation branches, when used, should start from and target
`develop`. Do not publish application code directly to `main`. This branch policy
does not authorize starting implementation during a documentation/design-only task.
A maintainer reviews and merges contributions; the project currently has no
automated product checks or release workflow.

## Future implementation workflow

The accepted [F02 setup](docs/development-setup.md) selects Python 3.12 for local
development, a target 3.12–3.15 matrix, initial package version `0.1.0.dev0`, uv,
Hatchling, pytest, Ruff, and mypy. Its planned commands are design examples,
not executable setup instructions for the current repository.

M0 implementation will introduce `pyproject.toml`, `.python-version`, `uv.lock`,
the `src/` layout, and real tests on `develop` after implementation is authorized.
Update dependency declarations and their lockfile together; isolated build
dependencies require their own reviewed constraints. Do not claim this design
delivery installed tools, built artifacts, or passed product tests.

Tests should demonstrate acceptance criteria and meaningful failure cases;
see the [testing strategy](docs/testing.md). No tests executed means no test
evidence. An inherited failing suite must be reported as failing.

## Learning and automation

The maintainer intends to learn Python through models, YAML loading, CLI
commands, rendering, and later FastAPI. Coordinate before taking over those
learning tasks. Automation can help with repository preparation, documentation,
fixtures, repetitive tests, themes, and release tooling within an agreed scope.

Agents must use the same product definition and acceptance criteria as human
contributors. They must not expand scope, silently settle open product
decisions, publish packages, or deploy client sites without authorization.

Contributions are provided under the repository's [MIT License](LICENSE).
By contributing, you confirm that you have the right to submit the material.
