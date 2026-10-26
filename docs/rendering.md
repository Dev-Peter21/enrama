# HTML rendering and metadata contract

Status: **G02 implemented on develop, awaiting maintainer acceptance**, following
approval and implementation authorization on 2026-10-24 for
[issue #9](https://github.com/Dev-Peter21/enrama/issues/9). The shared renderer,
packaged base, Jinja2 dependency and rendering tests are implemented. See
[verification evidence](verification/g02.md). Issue #9 remains open;
package version is still `0.1.0.dev0`.

The local-demo branch adds U03/U04 packaged styles and decorative controlled
icons to this shared base; metadata, enabled order, same-context destinations
and escaping remain unchanged. See [themes](themes.md).

## Intent and chosen approach

Turn validated client content and prepared local asset references into one
complete static HTML document. Keep this service reusable by the future builder,
CLI and local editor, without depending on terminal or web frameworks.

| Approach considered | Tradeoff | Decision |
| --- | --- | --- |
| Implement the rendering engine and shared HTML base in G02 | Establishes content, security, metadata and semantic behavior independently of visual design | Chosen |
| Deliver both finished theme presentations in G02 | Produces styled pages earlier but absorbs U03/U04 layout, CSS and icon work | Deferred to U03/U04 |

G02 owns trusted packaged Jinja2 rendering, the shared semantic HTML base,
metadata and URL derivation. Both accepted theme names, `minimal` and `bold`,
use this shared behavior; G02 does not claim to deliver their distinct visual
presentations. Do not reference nonexistent theme styles or icon files to make
the base appear finished.

## Inputs, output and trust boundary

- Receive a validated [C01 `EnramaConfig`](configuration.md) and the
  [G01 `PreparedAssets`](assets.md) prepared for its configured images.
- Use the retained field bindings and public paths. Do not reload YAML, reopen
  images, hash or decode them again, copy assets, or inspect the client tree.
- Return the complete HTML as an in-memory string. Do not write `index.html`,
  create directories, stage output, replace `dist/`, start a server or print.
  [G03](roadmap.md#g03--coordinate-safe-repeatable-builds) owns coordination and
  [F01](cli-contract.md) governs the filesystem lifecycle.
- Load only trusted resources packaged with Enrama. No arbitrary client template
  paths, remote templates, implicit network requests or environment-dependent
  template discovery are allowed.
- Enable HTML autoescaping explicitly for the rendering path. YAML text is
  content, never HTML, Markdown or Jinja template source. Do not mark client
  strings safe or recursively interpret HTML entities or template expressions.
- Use `StrictUndefined`: an unexpectedly absent internal variable fails rather
  than becoming empty output. Optional data is handled explicitly in the context
  and template. Strict undefined handling does not make optional fields required.
- Treat the context as internal presentation data, not as a second configuration
  model. C01/C02 remain authoritative for field/URL/catalog validation, and G01
  remains authoritative for image content and filesystem safety.

Repeated rendering with the same validated content, prepared public paths and
locked generator/resources produces the same HTML string, with LF newlines.
Do not include timestamps, random IDs, machine paths, working-directory data or
live network information. Rendering does not mutate either input. G03 separately
verifies complete build repeatability, including copied files.

## Shared HTML structure and accessible content

- Emit an HTML5 doctype and one complete `html` / `head` / `body` document.
  Set `html[lang]` to the C01-normalized `site.language`.
- Include UTF-8 charset metadata and `width=device-width, initial-scale=1`
  viewport metadata without disabling user zoom.
- Use exactly one `main`. Its profile header contains exactly one `h1`, from
  `profile.name`; `site.title` supplies the document title instead.
- Render the avatar only when configured, using its G01 public path and
  `alt=""`. It is decorative beside the visible profile name; do not derive
  alternative text from a filename or introduce a new YAML field.
- Render `profile.bio` as escaped paragraph text when nonempty; omit the
  paragraph for its empty default. Do not interpret Markdown or insert raw HTML.
- Render links and socials in separate `ul` / `li` lists, links first and
  socials second. Preserve relative YAML order within each collection and omit
  every disabled entry. No sorting, interleaving or invented priority applies.
- Use `links[].title` and the effective `socials[].label` as visible text and
  accessible link names in the shared base. Do not substitute the URL, ID,
  platform identifier or icon name for the label.
- Omit a list entirely when it has no enabled entries. Both lists may be empty:
  a profile-only page is valid, with no placeholder links or empty controls.
- Do not introduce fixed English collection headings or navigation labels;
  translation fields/services are outside this contract.
- Use native anchors with their normal keyboard behavior. No required JavaScript,
  tracking, automatic redirects or click interception is introduced.

The base is readable without styles or scripts. U03/U04 own responsive layouts,
CSS variables/colors, bundled icons/fonts and visual keyboard-focus treatment.
Icon-only theme presentation must retain the same accessible names, content,
ordering and metadata. The base is not acceptance evidence for finished themes.

## Metadata

| Output | Source and condition |
| --- | --- |
| `title` | Always `site.title` |
| `meta[name="description"]` | Always `site.description` |
| `og:title` | Always `site.title` |
| `og:description` | Always `site.description` |
| `og:type` | Always `website` |
| `link[rel="canonical"]` | Directory-form public URL, only when `site.url` is set |
| `og:url` | Exactly the same public URL as canonical, only when `site.url` is set |
| `og:image` | Absolute URL of the prepared `site.og_image`, only when both that image and `site.url` are set |
| `link[rel="icon"]` | Relative G01 path for `site.favicon`, only when configured |

Escape text and attribute values through the HTML rendering path. Do not add an
avatar-to-OG-image fallback, default favicon, guessed public host, preview URL,
`og:locale`, Twitter card tags or structured data. C01 language tags do not all
map to Open Graph's locale form, so no locale is inferred. Without the URL/image
inputs the corresponding tags are omitted; a complete social-preview object or
a platform's eventual preview appearance is not guaranteed.

An optional OG image still belongs to G01's preparation/validation even when no
`site.url` is available. Omitting its HTML metadata does not bypass image checks.

## Public URL and local path rules

Interpret `site.url` as the **public directory containing `index.html`**, including
any hosting prefix. When deriving output URLs, append a trailing `/` if missing.
This is rendering-time derivation, not a change to the validated model or YAML.
Do not guess that a path ending in `.html` is a file, strip path components,
decode/re-encode path data or repair the URL. All accepted paths have directory
semantics under this contract.

For a prepared public path `assets/client/<digest>.png`:

| Configured `site.url` | Canonical / `og:url` | Absolute `og:image`, when configured |
| --- | --- | --- |
| omitted or null | Omitted | Omitted |
| `https://example.com` | `https://example.com/` | `https://example.com/assets/client/<digest>.png` |
| `https://example.com/client` | `https://example.com/client/` | `https://example.com/client/assets/client/<digest>.png` |
| `https://example.com/client/` | `https://example.com/client/` | `https://example.com/client/assets/client/<digest>.png` |

Only metadata requiring a public address uses this absolute base. Avatar and
favicon references use the G01 forward-slash relative paths, without a leading
`/`. Future local theme resources must follow the same hosting-prefix principle.
Never emit original source references, filesystem paths, `file:` URLs or an HTML
`base` element. Relative resources must keep working under local preview and
domain-root or repository-subpath hosting, independent of `site.url`.

## Destination behavior

Preserve each enabled link/social URL exactly as validated by C01, applying only
HTML attribute escaping when embedding it. Do not append tracking parameters,
rewrite domains, normalize destinations or fetch them. Contact URIs retain C01's
restricted `mailto` / `tel` behavior; the browser handles navigation.

Open links and socials in the **same browsing context by default**: no forced
`target="_blank"`. No new YAML setting, `nofollow` policy or navigation script is
introduced. Platform selects icon/default label only and does not restrict domains.

## Integration invariants and failures

The caller supplies the configuration and prepared snapshots as one matching
pair. For each configured image, its field binding must exist, retain the same
source reference and resolve to a public path present in the prepared asset set.
Bindings for absent image fields, duplicate/contradictory bindings or malformed
public paths are integration failures too. Verify these relationships in memory;
do not reopen sources to try to prove that the pair matches. This is a service
precondition, not an authenticity check on manually forged Python objects.

Do not silently drop a configured image, use its original path, or accept unsafe
paths as template-ready values when this invariant fails. Only G01's canonical
`assets/client/<64 lowercase hex characters>.<allowed extension>` paths are
eligible, with the configured role's supported extensions. Do not revalidate or
rehash snapshot image bytes in G02.

| Failure | Classification | Future F01 mapping |
| --- | --- | --- |
| Invalid YAML, model or image input found upstream | Preserve C01/C02/G01 ownership; no duplicate renderer validation stage | Existing upstream category |
| Configuration / prepared-asset mismatch or missing configured binding | Internal integration error | `70` |
| Required packaged template absent, invalid template syntax, unexpected undefined context, or renderer defect | Internal error | `70` |
| Actual permission or I/O failure while reading a packaged resource | Operational error | `3` |
| Interrupt | Propagate interruption; do not disguise as a render failure | `130` under the applicable F01 lifecycle |

Missing optional data, an absent `site.url`, empty collections and the two accepted
theme names are not errors. A missing packaged resource is a package defect,
distinct from a real permission/I/O failure reading an existing resource.

Core failures expose a structured category, safe English message and actionable
hint. Identify an internal template or configuration field when known, without
inventing YAML line/column positions. Do not include raw framework tracebacks,
full configuration/context dumps, local absolute paths or unsafe terminal control
characters in user-facing text. Do not blame valid client YAML for a packaged
template defect. Exact Python API/type names are left to implementation.

Fail at the first rendering/integration failure and return no partial HTML or
fallback empty document. Template failures can cascade, so G02 does not imitate
C02's batch-of-20 input diagnostics. The core neither prints nor exits; a future
caller/CLI owns presentation and process-code translation. Do not swallow
unexpected defects or interrupts under an invalid-input classification.

## Implementation acceptance

The implementation checks the following behaviors; actual executed counts,
environments and limitations are recorded in [G02 verification](verification/g02.md):

1. Parse generated HTML and verify doctype, language, charset, viewport, one main,
   one profile h1, optional profile elements, separate lists and label semantics.
2. Exercise markup-, quote-, entity- and Jinja-looking text in body, title and
   metadata attributes. Content remains text; no injected element/attribute or
   template execution occurs. Destination query delimiters survive HTML parsing.
3. Verify both collections' independent ordering, disabled omission, effective
   social labels and empty/profile-only cases, under both accepted theme names.
4. Check every metadata presence/omission combination, including OG image without
   public URL, optional favicon and avatar, and no invented locale/fallbacks.
5. Verify directory-form public URLs with/without a final slash, preserved encoded
   paths and hosting prefixes. Serve a synthetic rendered document and G01 copies
   at root and under a subpath using a plain static server; request relative image
   resources successfully. This test harness is not a product builder or preview.
6. Verify unchanged destinations, ordinary same-context anchors and absence of
   `base`, forced new tabs, remote resource dependencies and navigation scripts.
7. Exercise missing/mismatched bindings, unsafe prepared paths, missing/broken
   packaged templates, undefined internal variables, operational resource reads
   and interrupts. Assert classification, safe diagnostics and no partial result.
8. Render repeatedly without mutating inputs or accessing client files/network;
   compare exact HTML, excluding machine/environment-derived data.
9. Build and inspect wheel/sdist resource inventories. Install outside the source
   checkout and render the shared base from both distributions, with escaping and
   metadata intact. Run the existing F03 quality and six-environment matrix.

## Python API and implementation choices

The public API is available from `enrama.core`:

```python
from enrama.config import load_config
from enrama.core import RenderError, prepare_assets, render_html

source = "client/enrama.yaml"
config = load_config(source)
prepared = prepare_assets(config, source=source)
html = render_html(config, prepared)  # str, no filesystem output
```

`render_html(config: EnramaConfig, prepared: PreparedAssets) -> str` uses a
primitive presentation context and the fixed `enrama/_templates/base.html`
resource. It accepts no template path or environment override. Jinja2 is a used
runtime dependency (`>=3.1.6,<4`), locked at 3.1.6 with MarkupSafe 3.0.4.
A fixed FunctionLoader/importlib.resources read keeps genuine resource I/O errors
distinct from missing packaged templates, while preventing client/cwd discovery.

`RenderError` exposes `kind` (`internal` or `operational`), `category`
(`asset_mismatch`, `template_error`, `resource_error`, `internal_error`), English
`message`/`hint` and optional known `field` / `template`. Its string contains only
safe static renderer context. It has no YAML positions, retained partial HTML or
process exit side effect. The F01 mapping above remains the caller's responsibility.

Internal filenames, context representation and whitespace are implementation
choices; no second YAML model or visual theme contract is introduced.

## Scope boundary

G02 does not implement the G03 builder, filesystem lifecycle/manifest/cleanup,
CLI/preview commands, final theme CSS/icons, JSON Schema changes, editor,
analytics, package publication or deployment. No release/version increment is
implied; `0.1.0.dev0` remains the development version.

## References

- [Jinja HTML autoescaping](https://jinja.palletsprojects.com/en/stable/api/#autoescaping)
- [Jinja StrictUndefined](https://jinja.palletsprojects.com/en/stable/api/#jinja2.StrictUndefined)
- [Open Graph protocol](https://ogp.me/)
- [Theme requirements and U03/U04 boundaries](themes.md)
