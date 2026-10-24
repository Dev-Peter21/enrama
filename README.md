# Enrama

**Your links. Your hosting. Your rules.**

An open-source, self-hosted link-in-bio site generator built with Python.
One project per client. One YAML file. One command to generate a static site.
Once published, the site runs independently of Enrama.

> **Project status: configuration, assets and shared HTML rendering on `develop`.** The importable
> package `0.1.0.dev0`, strict YAML v1 models, bounded loader, structured diagnostics,
> generated editor schema, safe asset preparation/staging copying, development tools,
> shared HTML renderer, and tests are available.
> The coordinated builder, CLI, theme presentation, and editor are still planned. No package has been
> published to PyPI; `0.1.0` remains the MVP target.

## Developer setup

Use Python 3.12 and uv **0.13.5**. Start from `develop`:

```console
git clone --branch develop https://github.com/Dev-Peter21/enrama.git
cd enrama
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests scripts
uv run --locked python scripts/schema.py --check
uv run --locked pytest
uv build --python 3.12 --build-constraint build-constraints.txt --require-build-hashes
```

See the [development setup](docs/development-setup.md) for installation,
dependency updates, isolated artifact tests, and build constraints.
The [configuration contract](docs/configuration.md) documents the implemented
Python model API. The [safe YAML loader contract](docs/yaml-loader.md) documents
`parse_config`, `load_config`, input restrictions, resource limits, and diagnostics.
See [C02 verification](docs/verification/c02.md) for loader evidence.
The [JSON Schema/VS Code contract](docs/json-schema.md) documents the checked
artifact and manual local client setup; [C03 verification](docs/verification/c03.md)
records schema tests and actual editor-provider evidence.
The [asset contract](docs/assets.md) documents G01's `prepare_assets`/`copy_assets`
API; [G01 verification](docs/verification/g01.md) records image, filesystem and
installed-distribution evidence.
The [rendering contract](docs/rendering.md) defines G02's shared HTML base,
metadata, public directory URLs, failures and the implemented Python API;
[G02 verification](docs/verification/g02.md) records actual checks.

## Why Enrama?

Enrama is intended for developers and small agencies who want to create and
maintain client link pages without depending on a hosted link-in-bio platform.
The first real-world validation case is replacing a client's unavailable
Linktree page with an independently hosted site.

The generator will run locally or in CI. Its output will be plain HTML, CSS,
images, and minimal JavaScript that any suitable static host can serve. No
Enrama account, production backend, or database will be required.

## Planned first release

- Python 3.12+, distributed through PyPI and GitHub.
- `enrama init`, `validate`, `build`, and `preview` commands.
- Typed, versioned YAML configuration for profile, links, socials, theme, and assets.
- Two responsive themes: `minimal` and `bold`.
- Semantic HTML, accessible links, SEO metadata, Open Graph, and favicon support.
- Static output in `dist/` and a documented GitHub Pages deployment recipe.

The local visual editor is planned for `0.2`. Login, managed hosting, click
analytics, subscriptions, and URL shortening are outside the MVP.

## Intended workflow

These commands describe the future interface. They are **not available from
this repository yet**; no PyPI package is published by this initialization.

```console
uvx enrama init my-client
cd my-client
uvx enrama validate
uvx enrama preview
uvx enrama build
```

Publish the generated `dist/` directory to a static host. Client YAML and images
belong in a separate client repository, not in Enrama's source repository.

## Documentation

Start with the [documentation index](docs/README.md), or go directly to:

- [Product definition](docs/product.md)
- [Architecture](docs/architecture.md)
- [CLI and filesystem contract](docs/cli-contract.md)
- [Python development setup](docs/development-setup.md)
- [Accepted CI and compatibility matrix design](docs/continuous-integration.md)
- [Accepted YAML v1 contract](docs/configuration.md)
- [Accepted safe YAML loader and diagnostics contract](docs/yaml-loader.md)
- [Accepted JSON Schema and VS Code contract](docs/json-schema.md)
- [Accepted local asset contract](docs/assets.md)
- [Agreed HTML rendering and metadata contract](docs/rendering.md)
- [Themes](docs/themes.md)
- [Deployment](docs/deployment.md)
- [Roadmap and implementation tasks](docs/roadmap.md)
- [Published MVP backlog and Kanban](docs/backlog.md)
- [Testing strategy](docs/testing.md)
- [Release process](docs/releasing.md)
- [Decisions and open questions](docs/decisions.md)

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing work. English is the
canonical documentation language; discussions and contributions in Spanish
are welcome. See [SUPPORT.md](SUPPORT.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and the [security policy](SECURITY.md).

The maintainer is [@Dev-Peter21](https://github.com/Dev-Peter21).
The project uses the [MIT License](LICENSE).

The Enrama name is provisional. This initialization does not reserve a PyPI
namespace or establish trademark clearance.
