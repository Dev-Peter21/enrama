# Run the local demo

The local demo implements G03, U01–U04 and the single synthetic example
`examples/demo`. It does not formally accept or close any GitHub issue. No package is
published to PyPI, no release/deployment is performed, and the visual editor stays
outside this scope. Integration/push to develop was subsequently authorized;
see the verification record for the exact final revision and CI.

## Environment and basic workflow

Use the repository's Python 3.12 / uv 0.13.5 setup:

```console
uv sync --locked
uv run --locked enrama --help
uv run --locked enrama --version
uv run --locked enrama init my-client
cd my-client
# Edit enrama.yaml. The current generator remains a local development package.
enrama validate
enrama build
enrama preview --port 8000
```

Inside a separate client directory, use the absolute executable from the Enrama
checkout's `.venv/bin/enrama` (Windows: `.venv/Scripts/enrama.exe`), or activate
that environment first. Do not assume `uv run` in a client directory discovers
the generator repository or that `uvx enrama` works before a package is published.
Help/version are available without configuration. Output is always client-local
`dist/`; there is no --force, --output, watch or automatic browser launch.

From the generator checkout, use an explicit source instead:

```console
uv run --locked enrama validate --config examples/demo/enrama.yaml
uv run --locked enrama build --config examples/demo/enrama.yaml
uv run --locked enrama preview --config examples/demo/enrama.yaml --port 8765
```

Open [the minimal demo](http://127.0.0.1:8765/). Preview runs in the foreground.
Ctrl+C stops it with code 0 and keeps dist. Stop, edit, restart and refresh to see
changes. A second build/preview fails while the project is being served; validate
remains read-only. An occupied port fails before changing output.

## Compare both themes

The example uses `theme.name: minimal`. To compare without modifying that client,
copy `examples/demo` to a new local client directory **excluding dist and .enrama**,
change only its YAML theme.name to `bold`, optionally choose other six-digit
colors, and run preview for the copy with an explicit different port.

The delivered local session uses `reports/demo-bold/enrama.yaml` at
[the bold demo](http://127.0.0.1:8766/). `reports/` is ignored local evidence,
so recreate that copy if starting from a clean clone. Both copies have independent
output ownership. The CLI never silently chooses a different port.

Minimal uses an editorial serif/system type stack and quiet rows; bold uses
strong system typography and solid accent buttons. No fonts, analytics, scripts
or CDN are required in production. Controlled Lucide/Bootstrap SVGs are bundled,
with exact source commits/hashes in `src/enrama/_icons/provenance.json` and full
ISC/MIT notices copied into `assets/theme/THIRD_PARTY_NOTICES.txt`.

Text/background contrast below 4.5:1 gets an accessible black/white text fallback;
accent button text and focus colors are derived separately. Build/preview report
warnings for an insufficient configured body contrast. YAML stays unchanged.
Links keep visible accessible labels and normal same-tab navigation. Decorative
icons and CSS arrow geometry do not add accessible-name noise. Touch targets are
at least 44px tall, long labels wrap and motion honors reduced-motion preferences.

## Safe build and manual recovery

The [builder contract](builder.md) describes `.enrama/`, guarded publication and
`dist/.enrama-manifest.json`. Enrama replaces only a complete, recognized, unedited
output. Extra/changed/missing files, unknown empty directories, links and malformed
manifests block replacement with code 3; there is no destructive bypass.

If a build is terminated abruptly, the OS releases its lock, but the transaction,
staging and backup remain. A later build fails with `incomplete_operation` instead
of guessing which copy to delete or restore. To recover:

1. Stop every build/preview for this project.
2. Inspect dist, `.enrama/staging`, `.enrama/backup` and the transaction record.
   Keep copies of anything valuable; a backup may be the last complete old site.
3. Deliberately move recoverable/unrecognized transaction data to a safe location
   outside the reserved working paths. Restore a chosen complete site only after
   inspecting it. Do not delete data just to clear the blocker.
4. Leave only the recognized workspace marker and guard before retrying. If dist
   is not intact owned output, move it aside deliberately before a fresh build.

There is no recovery/clean command or automatic stale-data deletion. Expected
errors print safe diagnostics to stderr, while success/help/version/URL go to
stdout. Codes follow F01: input1, invocation2, operational3, internal70,
interrupted preparation130. Post-publication cleanup failure can leave the complete
new site and recoverable backup with an error; it is not reported as success.

## Example assets and distribution

The Amapola Estudio demo is synthetic. example.com destinations and email are
placeholders, not a live business. Flower PNG artwork is original geometric
artwork under the repository MIT license; no client data or third-party photos.
The existing C03 schema-copy/update workflow stays manual; init does not silently
install a schema/editor or change a client tool reference.

Build/install locally without publishing:

```console
uv build --build-constraint build-constraints.txt --require-build-hashes
uv venv /tmp/enrama-consumer --python 3.12
uv pip install --python /tmp/enrama-consumer/bin/python dist/enrama-0.1.0.dev0-py3-none-any.whl --build-constraint build-constraints.txt --require-build-hashes
/tmp/enrama-consumer/bin/enrama init /tmp/enrama-client
/tmp/enrama-consumer/bin/enrama preview --config /tmp/enrama-client/enrama.yaml --port 8001
```

Use absent /tmp destinations or choose new names. Windows uses Scripts paths and
an appropriate writable temporary directory. Inspect local verification evidence
before claiming platform compatibility; no remote matrix was triggered by this
unpublished branch.
