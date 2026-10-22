# Enrama

**Your links. Your hosting. Your rules.**

An open-source, self-hosted link-in-bio site generator built with Python.
One project per client. One YAML file. One command to generate a static site.
Once published, the site runs independently of Enrama.

> **Project status: documentation foundation.** No generator, CLI, installable
> package, themes, or editor has been implemented. Version `0.1.0` is a target,
> not a published release. This repository currently defines the product and
> the work needed to build it.

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
- Typed, versioned YAML configuration for profile, links, theme, and assets.
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
- [Draft YAML contract](docs/configuration.md)
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
