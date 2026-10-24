# YAML v1 configuration contract

Status: **implemented C01 models on `develop`**, following the contract agreed on 2026-10-23 for
[C01 / issue #5](https://github.com/Dev-Peter21/enrama/issues/5).
This is the normative field contract for `schema_version: 1`. The six pure data
models, validators, and presentation catalogs are implemented. YAML loading,
generated JSON Schema, CLI, rendering, and icon assets remain separate tasks.
See the [C01 verification record](verification/c01.md) for actual evidence.

## Purpose and approach

One client project supplies one `enrama.yaml` and its local assets. YAML is the
source of truth shared by the future CLI and local editor. Validation is strict,
local, and deterministic: it must not require Enrama services or network access.
The accepted [CLI and filesystem contract](cli-contract.md) defines configuration
selection and the project root; this document does not change those rules.

The reviewed choices are:

| Area | Accepted approach | Alternative and tradeoff |
| --- | --- | --- |
| Content collections | Ordered `links` and `socials` with distinct models | One collection mixes ordinary calls to action and platform-specific presentation |
| Public site address | Optional `site.url` | Requiring it would block validation and local preview before hosting is selected |
| Social platforms | Platform selects icon and default label only | Domain allowlists would require maintained aliases and could reject legitimate destinations |
| Input policy | Strict types, forbidden unknown keys, explicit defaults | Silent coercion and ignored keys can hide mistakes in client configuration |
| Language | A documented BCP 47 subset checked against local registry data | Full extension/private-use support adds scope; a shape-only regex misses unknown subtags |
| Icons | Small, stable Enrama catalogs backed by bundled SVG assets | Arbitrary SVG/HTML and remote icon loading add an untrusted execution or network boundary |

## Model boundaries

The Pydantic v2 models are `EnramaConfig`, `SiteConfig`, `ProfileConfig`,
`ThemeConfig`, `LinkConfig`, and `SocialConfig`. The models validate data without
opening client files, rendering templates, making network requests, or printing errors.
Cross-collection ID uniqueness belongs to the root model.

Import models from `enrama.config` and pass already-parsed Python data:

```python
from enrama.config import EnramaConfig

config = EnramaConfig.model_validate(
    {
        "schema_version": 1,
        "site": {"title": "My page", "description": "My links", "language": "en"},
        "profile": {"name": "My profile"},
    }
)
assert config.site.url is None
```

Invalid data raises Pydantic `ValidationError` with structured field locations.
`SocialConfig.icon` is a derived read-only Python property, not an accepted input
field or an extra serialized field. No YAML parsing is performed by these APIs.

### Root fields

| Field | Type | Presence/default |
| --- | --- | --- |
| `schema_version` | Integer, exactly `1` | Required; no inferred version |
| `site` | `SiteConfig` mapping | Required |
| `profile` | `ProfileConfig` mapping | Required |
| `theme` | `ThemeConfig` mapping | Omitted means the default theme configuration |
| `links` | List of `LinkConfig` mappings | Default `[]`; at most 100 entries |
| `socials` | List of `SocialConfig` mappings | Default `[]`; at most 20 entries |

Both collections may be empty. Each collection retains its own YAML order;
there is no combined ordering field or inferred reordering.

### Site fields

| Field | Type | Presence/default and meaning |
| --- | --- | --- |
| `title` | String | Required; 1–100 characters; page and metadata title |
| `description` | String | Required; 1–300 characters; metadata description |
| `language` | String | Required; supported language tag; no automatic detection/default |
| `url` | String or null | Default `null`; intended public HTTPS page address |
| `favicon` | String or null | Default `null`; local asset reference |
| `og_image` | String or null | Default `null`; local Open Graph image reference |

Omitting `site.url` must not prevent validation, preview, or build. The renderer
must omit canonical URL, `og:url`, and absolute Open Graph image metadata that
cannot be derived without a public base. It must not guess a production URL
from the preview address or substitute a placeholder. Text metadata, document
language, and local favicon support do not depend on `site.url`.

`site.url` may include a hosting path prefix, such as
`https://example.com/clients/amapola/`. Query and fragment components are not
allowed. Rendering/asset tasks must preserve that deployment prefix when
constructing public asset URLs; it is not a configurable output directory.

### Profile fields

| Field | Type | Presence/default |
| --- | --- | --- |
| `name` | String | Required; 1–100 characters |
| `bio` | String | Default `""`; 0–300 characters |
| `avatar` | String or null | Default `null`; local asset reference |

### Theme fields

| Field | Type | Default and constraint |
| --- | --- | --- |
| `name` | String | `minimal`; exactly `minimal` or `bold` |
| `primary_color` | String | `#2563EB` |
| `background_color` | String | `#FFFFFF` |
| `text_color` | String | `#252525` |

Omitting `theme` and supplying `theme: {}` produce the same effective defaults.
Partial theme mappings default only their missing fields. Both themes use these
same defaults. Color values must match `#[0-9A-Fa-f]{6}` exactly: no shorthand,
alpha channel, named color, CSS expression, or surrounding whitespace. Hex digits
are case-insensitive; the contract does not require a particular output casing.
Contrast warnings/policy remain a theme acceptance decision, not a C01 rule.

### Link fields

| Field | Type | Presence/default |
| --- | --- | --- |
| `id` | String | Required; stable identity governed by the ID policy below |
| `title` | String | Required; 1–100 characters; visible and accessible label |
| `url` | String | Required; destination governed by the URL policy below |
| `icon` | String or null | Default `null`; exact general-icon catalog identifier |
| `enabled` | Boolean | Default `true` |

### Social fields

| Field | Type | Presence/default |
| --- | --- | --- |
| `id` | String | Required; stable identity governed by the ID policy below |
| `platform` | String | Required; exact platform catalog identifier |
| `url` | String | Required; HTTPS destination |
| `label` | String | If omitted, the platform display name; otherwise 1–100 characters |
| `enabled` | Boolean | Default `true` |

The social icon is derived from `platform`. There is no social `icon` override.
`platform` does **not** constrain the destination's domain, path, account name,
or ownership; it provides presentation metadata only. Multiple entries may use
the same platform if their IDs differ. The effective label supplies an accessible
name even when a theme presents the social entry as an icon.

## Shared validation policy

- Enforce strict scalar/container types and forbid unknown keys at every model
  level. Do not coerce numbers to strings, strings to booleans, or mappings to
  lists. In particular, `schema_version: true`, `schema_version: "1"`, and
  `enabled: "false"` are invalid.
- Only explicitly nullable fields accept `null`: `site.url`, `site.favicon`,
  `site.og_image`, `profile.avatar`, and `links[].icon`. Defaults apply to
  omission, not to explicit null. Thus `theme: null`, `links: null`, `bio: null`,
  and `socials[].label: null` are invalid.
- Trim surrounding whitespace from `site.title`, `site.description`,
  `profile.name`, `profile.bio`, `links[].title`, and `socials[].label` before
  checking their lengths. Count Unicode characters, not encoded bytes. Required
  text must remain nonempty; a whitespace-only bio becomes `""`.
- These text fields are plain content, not HTML, Markdown, or template source.
  Rendering must escape them. A markup-looking string is not permission to
  execute it and need not be rejected merely for containing `<` or `>`.
- Do not trim, slugify, or silently repair IDs, catalog identifiers, URLs, or
  language tags. Language case normalization is the explicit exception below.
- Validate disabled entries fully. `enabled: false` affects rendering only;
  it does not bypass limits, catalog checks, URL rules, or ID uniqueness.

### IDs, order, and enabled state

IDs must match `[a-z][a-z0-9-]{0,63}` exactly: 1–64 ASCII characters, beginning
with a lowercase letter. They must be unique **across both** `links` and `socials`,
including disabled entries. Do not generate IDs from titles or list positions.
Changing a title, URL, platform, enabled state, or position does not automatically
change the entry's ID.

List limits include disabled entries. Rendering omits disabled entries and retains
the relative order of the remaining entries within each collection. Empty lists
are valid; themes must handle them without adding placeholder links.

## URL policy

| Field | Allowed schemes |
| --- | --- |
| `site.url`, when present | `https` |
| `links[].url` | `https`, `http`, `mailto`, `tel` |
| `socials[].url` | `https` |

Apply the following rules to every non-null URL:

1. Require a nonempty string of at most 2048 characters. Compare schemes
   case-insensitively, but do not add a missing scheme or rewrite the destination.
2. Reject literal whitespace, control characters, and backslashes. Encoded spaces
   in an otherwise valid URL are not literal whitespace.
3. For HTTP(S), require an absolute URL with a valid host/authority and no user
   information: neither username nor password is allowed. Reject malformed URL
   syntax rather than accepting it merely because its scheme is allowed.
4. Reject relative paths, protocol-relative URLs (`//example.com`), and all
   schemes outside the field's allowlist, including `javascript`, `data`, `file`,
   `ftp`, `vbscript`, and custom application schemes. Use HTTPS destinations
   such as `https://wa.me/...` and `https://t.me/...` for supported web flows.
5. Preserve path, query, and fragment content where the field allows them.
   Do not recursively percent-decode or HTML-unescape input to make a scheme
   acceptable. Encoded/entity-based scheme disguises are invalid; ordinary
   percent-encoded path/query data remains usable.
6. Perform no DNS, HTTP, redirect, account-existence, or reachability checks.
   An accepted destination is structurally valid, not certified safe or live.

The MVP intentionally supports narrower contact URI forms than the full RFCs:

- `mailto`: one address using the `addr-spec` form from
  [RFC 6068](https://www.rfc-editor.org/rfc/rfc6068.html), without a display name,
  multiple recipients, query/header parameters, or a fragment. For example,
  `mailto:hello@example.com` is supported; adding `?subject=Hello` is not.
  Encoded control characters must not bypass address validation.
- `tel`: a leading `+` followed by one or more ASCII digits, with no visual
  separators, extension, parameters, query, or fragment; for example,
  `tel:+5491100000000`. This is Enrama's restricted international-number form,
  not support for every form in [RFC 3966](https://www.rfc-editor.org/rfc/rfc3966.html)
  or a check that a number has been allocated.

The no-query/no-fragment restriction on `site.url` does not restrict query strings
and fragments in HTTP(S) link and social destinations.

## Language policy

`site.language` uses a documented subset of
[BCP 47 / RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html): a registered
primary language, optional script, optional region, and registered variants in
that order. Extlang sequences, extension sequences, private-use tags/subtags,
and legacy grandfathered forms outside this shape are not supported by YAML v1.

- Validate syntax and registered subtags using local, versioned registry data;
  a regular expression alone cannot establish that a subtag is registered.
- Reject unknown components, repeated variants, underscores, whitespace, and
  human-readable language names. Do not infer a language or region.
- Accept case-insensitive input and normalize only casing: lowercase language
  and variants, title-case script, uppercase alphabetic region, unchanged numeric
  region. For example, `ES-ar` becomes `es-AR`.
- Do not silently replace deprecated identifiers/aliases, repair typos, or
  convert underscores. A registered deprecated identifier is not automatically
  rewritten to its preferred replacement.
- C01 uses the IANA registry snapshot dated **2021-08-06**, included in the
  exactly pinned `langcodes==3.5.1` dependency. It reads the trusted installed
  registry resource once at module import and validates from in-memory sets by
  subtag type. It does not use langcodes' alias-repair or CLDR validity helpers.
  The fixed snapshot means newer registrations are not automatically accepted;
  a registry update is an intentional dependency/data change with tests.

Accepted examples: `es`, `es-AR`, `es-419`, `zh-Hant-TW`, and `sl-rozaj`.
Rejected examples: `es_AR`, `Español`, `es-AB` (unregistered region),
`sl-rozaj-rozaj` (repeated variant), `en-u-ca-gregory` (extension), and
`x-client` (private use).

## Controlled catalogs

Catalog identifiers are exact, lowercase, case-sensitive values, with no aliases
or fallback for misspellings. Public identifiers belong to Enrama, independently
of future upstream asset renames.

### Social platforms

| `platform` | Default `label` | Planned Bootstrap Icons asset |
| --- | --- | --- |
| `instagram` | Instagram | `instagram` |
| `facebook` | Facebook | `facebook` |
| `whatsapp` | WhatsApp | `whatsapp` |
| `youtube` | YouTube | `youtube` |
| `tiktok` | TikTok | `tiktok` |
| `linkedin` | LinkedIn | `linkedin` |
| `github` | GitHub | `github` |
| `x` | X | `twitter-x` |
| `telegram` | Telegram | `telegram` |

A custom nonempty `label` replaces the display name without changing the icon.
An HTTPS URL on another domain is valid for any of these platforms; this is an
intentional presentation-only policy, not a missing domain validator.

### General link icons

The complete initial `links[].icon` catalog is:

`link`, `external-link`, `message-circle`, `mail`, `phone`, `shopping-bag`,
`calendar`, `map-pin`, `file-text`, `download`, `globe`, `play`.

Omission or null means no icon. Brand identifiers such as `instagram` are not
members of this general catalog; use `socials` for a platform icon. A link may
still point to any allowed destination without an icon or with a general icon.
Raw SVG/HTML, URLs, file paths, remote packs, and arbitrary icon names are invalid.

### Sources and distribution boundary

Use [Lucide](https://lucide.dev/license) for general icons and
[Bootstrap Icons](https://icons.getbootstrap.com/) for platform marks. Lucide
[does not include brand logos](https://lucide.dev/brand-logo-statement).
Lucide carries ISC terms and MIT notices for applicable Feather-derived icons;
[Bootstrap Icons uses MIT](https://github.com/twbs/icons/blob/main/LICENSE).

U03 must select and pin the actual upstream revisions, bundle only the required
trusted SVGs, retain all applicable copyright/license notices in distributions
and generated copies, and verify installed-package rendering without a CDN.
No icon assets, new frontend dependencies, or third-party notice files are
introduced before those assets are actually bundled. Font selection and custom
color contrast policy remain open under O05.

## Local image references

`profile.avatar`, `site.favicon`, and `site.og_image` are nullable, nonempty
relative path strings when provided. Resolve them against the client project
root, not the shell working directory. `./assets/logo.png` is an intended form.
These fields are never remote URLs, embedded data, or requests to download files.

C01 validates their lexical path shape: reject absolute/drive/UNC paths, parent
traversal components, and references into the reserved project `dist/` tree,
including its case variants and Windows trailing-dot alias `dist.`.
Do not expand environment variables or the user's home directory. G01 must check
actual existence, supported file types, containment, internal-symlink rejection
and safe copying. The agreed [G01 asset contract](assets.md) resolves O04 with
role-specific formats/limits, Pillow decoding, unchanged snapshots, deterministic
content paths and collision/error policy. G01 implements those checks on
`develop`, separately from C01/C02; CLI `validate` will eventually include them,
as required by F01.

Missing optional references mean no corresponding configured image. There is
no implicit avatar-to-Open-Graph fallback or remote default image in YAML v1.

## Examples

### Minimal valid input

This uses no local image and needs no production URL:

```yaml
schema_version: 1
site:
  title: "Amapola Deco"
  description: "Flores, plantas y regalos"
  language: "es-AR"
profile:
  name: "Amapola Deco"
```

Its effective defaults are empty `links`/`socials`, `profile.bio: ""`, null
optional image/URL fields, and the `minimal` theme with the three default colors.
Defaults exist in the validated model; validation does not rewrite the YAML file.

### Expanded input

This illustrates the accepted shape, not a currently runnable project. Client
image files must be supplied before eventual filesystem validation can succeed.

```yaml
schema_version: 1
site:
  title: "Amapola Deco"
  description: "Flores, plantas y regalos"
  language: "es-AR"
  url: "https://example.com/amapola/"
  favicon: "./assets/favicon.png"
  og_image: "./assets/social-card.png"
profile:
  name: "Amapola Deco"
  bio: "Flores y detalles para cada ocasión"
  avatar: "./assets/logo.png"
theme:
  name: "minimal"
  primary_color: "#D97A98"
  background_color: "#FFF8F7"
  text_color: "#252525"
links:
  - id: contact-whatsapp
    title: "Escribinos por WhatsApp"
    url: "https://wa.me/5491100000000"
    icon: "message-circle"
    enabled: true
  - id: catalog
    title: "Nuestro catálogo"
    url: "https://example.com/catalogo"
    icon: "shopping-bag"
  - id: contact-email
    title: "Escribinos por email"
    url: "mailto:hello@example.com"
  - id: seasonal-offer
    title: "Promoción de temporada"
    url: "https://example.com/promocion"
    enabled: false
socials:
  - id: social-instagram
    platform: "instagram"
    url: "https://www.instagram.com/example/"
  - id: social-whatsapp
    platform: "whatsapp"
    label: "WhatsApp de Amapola"
    url: "https://wa.me/5491100000000"
```

Names and destinations are illustrative, not verified client information. The
PNG filenames illustrate path fields, not a final supported-format decision.

## Required acceptance cases

These cases define the model test requirements. Executed counts and the
remaining downstream rendering/asset boundaries are recorded in
[C01 verification](verification/c01.md).

| Case | Expected result |
| --- | --- |
| Minimal example; omitted `site.url`; empty collections | Accept with documented defaults |
| Explicit null in each nullable field | Accept |
| Explicit null in required/defaulted non-nullable fields | Reject |
| Missing required field; wrong type; unknown key at any nesting level | Reject with field context |
| `schema_version: "1"`, `true`, `0`, or `2` | Reject without version inference/coercion |
| Text at/over each limit; required whitespace-only text; empty bio | Apply trim and documented boundaries |
| IDs at 1/64 characters; invalid case/characters; 65 characters | Enforce exact grammar and length |
| Same ID in both collections, including a disabled entry | Reject |
| Reordered/disabled entries; repeated platform with distinct IDs | Preserve IDs/order; validate all; allow repeated platform |
| Exactly 100/101 links or 20/21 socials, including disabled entries | Accept at limit; reject above it |
| Omitted/empty/partial theme mapping and both theme names | Apply shared defaults; accept supported names |
| Six-digit mixed-case hex vs shorthand/alpha/CSS expression | Accept only the documented hex grammar |
| `site.url` with HTTPS path prefix vs HTTP/query/fragment | Accept prefix; reject restricted forms |
| HTTP link vs HTTP social; HTTPS social on a different domain | Accept link; reject HTTP social; accept different HTTPS domain |
| Single-address mailto and digit-only international tel vs parameters/multiple recipients/extensions | Enforce the MVP subsets |
| Missing host, credentials, relative URL, controls, backslashes, forbidden or disguised scheme | Reject |
| Valid encoded path/query and uppercase allowed scheme | Accept without rewriting destination data |
| Supported language/script/region/variant vs unknown/repeated/unsupported components | Enforce registry-backed subset and casing policy |
| Every platform and general icon; unknown/case-mismatched identifier | Accept exact catalog values only |
| Omitted social label, custom label, null label, social icon override | Derive/customize label; reject null and override |
| Local relative image reference vs remote/absolute/traversal/output path | Apply lexical policy without opening files in C01 |
| Plain text containing HTML/template-looking content | Treat as content; rendering escape checks belong to G02 |

## Compatibility and delivery boundaries

Keep schema versioning independent of package versioning. Reject unsupported
versions with an actionable error; do not reinterpret them as version 1. Public
IDs and existing field semantics must remain stable. An incompatible schema
change requires an explicit version/migration decision before implementation.
Future additions to controlled catalogs must be documented; they do not make old
generator versions accept identifiers those versions do not know.

- **C01:** implements pure Pydantic models, local validation/catalog data,
  defaults, and model tests against this contract on `develop`, following
  implementation authorization on 2026-10-23.
- **C02:** safe YAML parsing, rejection of unsafe constructors, and useful file/
  field diagnostics under the accepted [loader contract](yaml-loader.md), with
  fixed resource limits and at most 20 returned diagnostics. Implemented on
  `develop`; see [C02 verification](verification/c02.md).
- **C03:** generate JSON Schema from implemented models and document editor use
  under the accepted [JSON Schema/VS Code contract](json-schema.md): structural
  assistance, local client copy, exact revision matching, and manual updates.
  The artifact/helper are implemented on `develop`; see
  [C03 verification](verification/c03.md). C01/C02 retain complete validation authority.
- **G01:** actual asset resolution, file-format/size checks, and copying.
- **G02:** HTML escaping, metadata omission/base-path handling, and rendering.
- **U03/U04:** bundled icons, licenses, themes, layout, and accessibility evidence.

The accepted contract resolves O03. The maintainer accepted C01's implementation
and evidence on 2026-10-23; issue #5 is closed/completed. C01 adds only its used runtime
dependencies, Pydantic and the pinned registry-data provider. CLI/generator work,
PyPI publication, and deployment are not delivered or authorized by this issue.
