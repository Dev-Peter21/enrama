# Amapola Estudio — local Enrama example

A complete, synthetic link page demonstrating Enrama's **minimal** and **bold**
themes. No private client data is included. Every example.com destination and
hello@example.com is a placeholder; replace them before publishing a real page.
The flower PNGs are original geometric artwork under the repository MIT license.
Icons retain their bundled ISC/MIT notices. No remote font, script or CDN is needed.

## Run this example

From the Enrama repository root, using Python 3.12 and uv 0.13.5:

```console
uv sync --locked
uv run --locked enrama --help
uv run --locked enrama validate --config examples/demo/enrama.yaml
uv run --locked enrama build --config examples/demo/enrama.yaml
uv run --locked enrama preview --config examples/demo/enrama.yaml --port 8000
```

Open **http://127.0.0.1:8000/**. Preview builds first and then serves only the
complete generated `examples/demo/dist/`. Ctrl+C stops serving and keeps output.
Stop preview before editing/rebuilding; restart and refresh to see source changes.
There is no automatic watch/reload or silent port fallback. Choose an explicit
other `--port` if 8000 is occupied. A second build cannot replace an active preview.

## Switch themes

Stop preview and edit `enrama.yaml`:

```yaml
theme:
  name: "bold" # use "minimal" for the editorial presentation
  primary_color: "#D96B44"
  background_color: "#F3F0DB"
  text_color: "#1D3028"
```

These warm colors reproduce the bold demo; the committed minimal palette uses
primary `#294D3C`, background `#F7F4EB`, text `#23362E`. Both themes share exactly
the same profile, link/social order, metadata and same-tab destinations. Colors
are optional six-digit values; insufficient body-text contrast produces a warning
and accessible derived text without rewriting YAML.

Rerun the same validate/build/preview commands. Obsolete generated CSS/images are
removed only through a verified owned-output replacement. Local source PNGs and
YAML are kept. System fonts, visible focus, 44 px minimum link targets, decorative
controlled icons, wrapping labels and reduced-motion styles are included.

## Create your own client from scratch

Keep working from the generator repository so `uv run` uses its environment:

```console
uv run --locked enrama init my-client
# Edit my-client/enrama.yaml; add your own PNG/JPEG/static WebP assets if desired.
uv run --locked enrama validate --config my-client/enrama.yaml
uv run --locked enrama build --config my-client/enrama.yaml
uv run --locked enrama preview --config my-client/enrama.yaml --port 8001
```

The init destination must not already exist and its parent must exist. The client
gets YAML, assets/ and a .gitignore for dist/ and .enrama/. C03 schema/VS Code setup
remains an explicit manual copy/update; init installs no editor or schema silently.
There is no published PyPI package required for this local workflow; do not use
`uvx enrama` until a reviewed public distribution exists.

## Files and safe recovery

- `enrama.yaml`: all page content, theme and metadata; site.url is a public folder
  URL for canonical/OG metadata, not a local output path or preview redirect.
- `assets/flower.png`: original avatar/favicon, copied without transformations.
- `assets/social.png`: original OG artwork, published when configured.
- `dist/` (ignored): HTML, hashed local assets, notices and ownership manifest.
- `.enrama/` (ignored): coordination and transient staging/backup/transaction data.

Never hand-edit dist and expect Enrama to overwrite it: missing/changed/extra
files, unknown directories or unsafe elements block replacement with code 3.
Inspect and deliberately move conflicting output aside. There is no --force.
After an abrupt termination, preserve `.enrama/transaction.json`, staging and
backup and inspect/move recoverable data manually before retrying. Enrama does
not silently delete old transactions or guess which copy to restore.

The sample links are deliberately placeholders. The local preview is not a public
hosting service; only generated dist files would be deployed after separate
explicit authorization. No release, PyPI upload or public deployment is part of
running this example.
