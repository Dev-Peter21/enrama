# Architecture

Status: C01/C02/C03 configuration, G01 assets and G02 shared HTML rendering are
implemented on `develop`; builder, CLI, preview and theme presentation remain
intended design.

## System boundary

Enrama is one repository and one Python distribution. A build runs on the
developer's machine or in CI; only its static output goes to production.
Each client's YAML and assets live outside the generator repository.

```text
CLI (0.1)                         Local editor (0.2)
    |                                   |
    +------------ Application/Core -----+
                     |
          Load YAML -> Validate models
                     |
          Resolve theme and local assets
                     |
          Render HTML / CSS / metadata
                     |
                 dist/ files
                     |
             Any suitable static host
```

## Responsibilities

| Area | Responsibility | Boundary |
| --- | --- | --- |
| CLI | Parse commands, display errors, select paths | Calls core services; does not duplicate validation |
| Configuration | Safely load YAML, validate typed data and schema version | No rendering or terminal output |
| Core/build | Coordinate validated configuration, renderer, and asset processing | Usable without Typer or FastAPI |
| Rendering | Render trusted theme templates with validated data | Escape content; no arbitrary HTML from YAML |
| Assets | Resolve, validate, and copy local files | Enforce client-root containment; reject all internal symlinks |
| Themes | Supply templates, CSS, and controlled presentation | Keep business rules in models/core |
| Preview | Serve generated files locally | Default interface `127.0.0.1`; no required production service |
| Editor (later) | Edit YAML and invoke existing services | Local by default; preserve YAML comments on save |

Validation errors should identify the configuration field or file and explain
how to fix the problem. The CLI translates core failures into readable messages
and appropriate nonzero exit codes. The accepted
[CLI and filesystem contract](cli-contract.md) defines command behavior before
implementation, independently of framework exception defaults.
The accepted [C02 loader/diagnostics contract](yaml-loader.md) defines the safe
YAML subset, bounded reading/parsing, source positions, and structured failures.
C02 implements this core on `develop` through `parse_config` and `load_config`.
PyYAML events are bounded before plain-data construction and C01 validation;
source marks feed safe structured diagnostics. The core does not print or exit.
The accepted [C03 contract](json-schema.md) defines a model-derived structural
schema for local VS Code assistance. It does not reproduce every Python
validator or loader restriction; C01/C02 remain authoritative. Schema generation
and the checked artifact are implemented on `develop`; the internal helper
checks the artifact in CI. Actual editor evidence is recorded in
[C03 verification](verification/c03.md).

The agreed [G01 asset contract](assets.md) defines local image formats and fixed
byte/pixel limits, Pillow validation, byte-preserving staging copies, content-hash
public paths and structured failures. G01 is implemented through `prepare_assets` and
`copy_assets`, with immutable validated byte snapshots and Pillow 13.0.0; see
[G01 verification](verification/g01.md). G03 retains
publication, output ownership, staging lifecycle, cleanup and concurrency.

The agreed [G02 rendering contract](rendering.md) defines an in-memory HTML
service consuming C01 configuration and matching G01 prepared assets. Trusted
packaged Jinja2 resources use explicit HTML autoescaping and StrictUndefined.
G02 owns the shared semantic base, metadata, directory-form public URLs and
structured failures; U03/U04 own theme presentation and G03 writes output.
G02 is implemented on `develop` through `render_html` / `RenderError`, using
Jinja2 3.1.6 and the packaged shared base; see [G02 verification](verification/g02.md).

## Selected technologies

These choices come from the product brief. Tool/build versions are pinned by
F02; C01 introduces Pydantic and exactly pinned langcodes registry data.
Other runtime dependencies are introduced only when their modules use them.
The accepted [F02 setup](development-setup.md) defines Python 3.12 local
development, the target 3.12–3.15 matrix, version `0.1.0.dev0`, dependency groups,
and separate control of isolated build requirements.

| Concern | Choice |
| --- | --- |
| Runtime | Python 3.12+ |
| CLI | Typer |
| YAML loading | PyYAML, using safe loading |
| Models and generated JSON Schema | Pydantic v2 |
| Templates | Jinja2 with HTML autoescaping |
| Environment and dependency workflow | uv |
| Packaging | Hatchling |
| Tests | pytest |
| Formatting, linting, and typing | Ruff and mypy |
| Generated frontend | HTML, CSS, and minimal JavaScript |
| Future editor | FastAPI and Jinja2; evaluate ruamel.yaml for round-trip writes |

The design uses simple modules rather than a full Clean Architecture stack.
External integrations and abstractions should be introduced only for a concrete need.

## Planned source layout

This is a target layout, not a list of existing files.

```text
src/enrama/
  __init__.py
  _templates/
    base.html
  cli.py
  config/
    loader.py
    models.py
  core/
    builder.py
    renderer.py
    assets.py
  preview/
    server.py
  themes/
    minimal/
      index.html
      style.css
    bold/
      index.html
      style.css
tests/
  unit/
  integration/
  fixtures/
examples/demo/
  enrama.yaml
  assets/
```

M0 introduces `pyproject.toml`, `uv.lock`, packaging configuration, and CI.
The package must include built-in theme files in wheel and source distributions.
Version `0.2` adds `src/enrama/editor/` without another repository or engine.

## Trust and compatibility

Treat configuration and local assets as untrusted inputs. Reject unsupported
URL schemes and paths outside the client project. Icons come from a controlled
catalog; YAML cannot provide executable templates, scripts, or raw icon HTML.
Do not fetch remote assets implicitly during a build.

`schema_version` identifies the configuration contract independently of package
versions. Build output should be repeatable for the same supported configuration,
assets, theme, and generator version. F01 fixes output to the project-local
`dist/`, with ownership/integrity checks, staged replacement, protected inputs,
and exclusive output ownership. The [contract](cli-contract.md) governs these
behaviors; manifest serialization and coordination mechanics remain implementation
details for the builder tasks.

Client assets remain the client's property. Bundled theme assets need compatible
licenses and attribution. Prefer self-contained generated pages without runtime
dependencies on a third-party CDN.
