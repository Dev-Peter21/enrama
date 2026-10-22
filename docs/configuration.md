# Configuration contract

Status: initial public-contract **draft**, to be reviewed and implemented in M1.
No loader, models, JSON Schema, editor integration, or migration command exists yet.

The intended configuration filename is `enrama.yaml`, located at the root of a
client project. The following example illustrates the agreed shape, not a
currently runnable project. Its avatar must be supplied by the client.

```yaml
schema_version: 1
site:
  title: "Amapola Deco"
  description: "Flores, plantas y regalos"
  language: "es-AR"
  url: "https://example.com"
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
  - id: whatsapp
    title: "Escribinos por WhatsApp"
    url: "https://wa.me/5491100000000"
    icon: "message-circle"
    enabled: true
  - id: instagram
    title: "Instagram"
    url: "https://www.instagram.com/example/"
    icon: "instagram"
    enabled: true
  - id: catalogo
    title: "Nuestro catálogo"
    url: "https://example.com/catalogo"
    icon: "shopping-bag"
    enabled: true
```

Names and destinations above are illustrative, not verified client information.

## Fields and meaning

| Field | Meaning |
| --- | --- |
| `schema_version` | Configuration format version; initial target is integer `1` |
| `site.title` | Page title and metadata title |
| `site.description` | Page description for metadata |
| `site.language` | Document language tag, such as `es-AR` |
| `site.url` | Intended public page URL for canonical/social metadata |
| `profile.name` | Visible profile or business name |
| `profile.bio` | Visible plain-text profile description |
| `profile.avatar` | Path to a local image in the client project |
| `theme.name` | Built-in theme, initially `minimal` or `bold` |
| `theme.primary_color` | Primary accent color |
| `theme.background_color` | Page background color |
| `theme.text_color` | Text color |
| `links` | Ordered sequence of link objects |
| `links[].id` | Stable, unique identity independent of title or position |
| `links[].title` | Visible, accessible link label |
| `links[].url` | Destination validated against the supported protocol policy |
| `links[].icon` | Name from the controlled icon catalog |
| `links[].enabled` | Whether the link is rendered; hiding keeps its identity |

The list order is the visual order. Link IDs must remain stable when titles or
positions change. A duplicate ID is invalid. Profile text and link titles are
content, never raw HTML or executable template expressions.

## Validation and safe loading

The loader must parse YAML safely and give useful file/field diagnostics for
malformed syntax, unsupported versions, invalid types, unknown themes/icons,
duplicate IDs, invalid colors/URLs, and missing or unsafe local assets.
Unsafe YAML object constructors must never execute.

Use an explicit URL scheme allowlist. Dangerous schemes such as `javascript:`
and `data:` must be rejected, including obfuscated input that normalizes to a
disallowed scheme. The exact permitted schemes and normalization rules remain
an M1 decision; the example uses HTTPS destinations.

Asset resolution must not read outside the client root, including via `..`,
absolute paths, or symlinks. Assets belong to the client project and are copied
into the output; Enrama must not depend on its own hosted image service.

## Compatibility

- Keep configuration versioning separate from package versioning.
- Reject unsupported schema versions with an actionable error.
- Do not silently reinterpret an older version using new semantics.
- Document a migration strategy before introducing an incompatible version.
- Generate JSON Schema from the implemented Pydantic models, rather than
  maintaining a second handwritten definition that can drift.

Future VS Code completion should use that generated schema. No schema URL or
editor setup is published until the artifact exists.

## Decisions before freezing version 1

M1 must settle required fields, defaults, unknown-key handling, field length
limits, URL protocols, color formats, and the precise icon catalog. It must also
define favicon/Open Graph image and social-profile representation, which are
in the MVP scope but are not fully represented by the initial example.
Do not introduce speculative YAML keys for those features without review.
See [the decision log](decisions.md).
