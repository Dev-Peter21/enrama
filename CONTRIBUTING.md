# Contributing to Enrama

Thank you for helping make independently hosted link pages easier to maintain.
The Python package foundation and developer tooling are implemented on
`develop`. The product CLI and generator remain planned.

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

## Python development workflow

Install uv **0.13.5** using the [setup instructions](docs/development-setup.md),
then start from `develop` with Python 3.12. Follow the documented locked sync,
Ruff, strict mypy, pytest, and constrained build commands before submitting a PR.
The intended compatibility matrix is 3.12–3.15; F03 will automate it. Local
Python 3.12 evidence alone does not establish the full matrix. The accepted
[F03 design](docs/continuous-integration.md) also requires macOS and Windows
checks on Python 3.12; its workflow is not implemented yet.

Commit dependency declarations and `uv.lock` together. Review updates to
`build-constraints.txt` alongside the backend pin; the development lock does
not freeze isolated build dependencies. Keep `.venv/` and `dist/` untracked.
When adding package modules or data, update explicit wheel/sdist inclusion and
archive-content tests in the same change. Do not add unused runtime libraries.

Tests should demonstrate acceptance criteria and meaningful failure cases;
see the [testing strategy](docs/testing.md). The current packaging suite installs
each archive into its own environment outside the checkout. It requires uv on
PATH and may download pinned build inputs from PyPI; it never publishes a package.
No tests executed means no test evidence. Report inherited failures as failures.

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
