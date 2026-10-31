# Enrama

**Your links. Your hosting. Your rules.**

An open-source, self-hosted link-in-bio site generator built with Python.
One project per client. One YAML file. One command to generate a static site.
Once published, the site runs independently of Enrama.

> **0.1.0 prepared, not published.** The generator, CLI, preview and both themes
> are implemented. Version metadata is prepared for the first release; this does
> not mean that `enrama==0.1.0` is available on PyPI. Try [the example](examples/demo/README.md)
> or [local workflow](docs/local-demo.md). The [manual preparation workflow](docs/release-preparation.md)
> only builds and verifies files; publisher setup, tags and public release remain
> separate authorized steps.

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

The generator runs locally or in CI and produces plain HTML, CSS and images
that a static host can serve. Generated pages require no Enrama account,
production backend, database or Python runtime.

## Prepared first release

- Python 3.12–3.15 verified in CI; PyPI/GitHub publication is still pending.
- `enrama init`, `validate`, `build`, and `preview` commands.
- Typed, versioned YAML configuration for profile, links, socials, theme, and assets.
- Two responsive themes: `minimal` and `bold`.
- Semantic HTML, accessible links, SEO metadata, Open Graph, and favicon support.
- Static output in `dist/`; the live GitHub Pages recipe remains R04 work.

The local visual editor is planned for `0.2`. Login, managed hosting, click
analytics, subscriptions, and URL shortening are outside the MVP.

## Local workflow

```console
uv sync --locked
uv run --locked enrama init my-client
uv run --locked enrama validate --config my-client/enrama.yaml
uv run --locked enrama build --config my-client/enrama.yaml
uv run --locked enrama preview --config my-client/enrama.yaml --port 8000
```

Open the printed loopback URL. Stop/restart to rebuild after edits. Publish only
`dist/` when deployment is explicitly authorized; production needs no Python or
Enrama service. See [safe build/recovery](docs/builder.md) and
[local demo instructions](docs/local-demo.md). `uvx enrama` is not available from
an unpublished local package.

## Documentation

Start with the [documentation index](docs/README.md), or go directly to:

- [Product definition](docs/product.md)
- [Architecture](docs/architecture.md)
- [Local demo](docs/local-demo.md)
- [Safe builder contract](docs/builder.md)
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
- [Release preparation commands and workflow](docs/release-preparation.md)
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
