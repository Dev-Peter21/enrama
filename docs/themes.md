# Themes

Status: requirements only. Neither theme has been implemented.

The agreed [G02 rendering contract](rendering.md) separates a shared semantic
HTML base from U03/U04 presentation. G02 will support both accepted theme names
through the base without delivering distinct layouts, CSS or icon assets.
Metadata, same-context anchors and accessible labels remain shared behavior.

## Built-in themes for 0.1

| Theme | Intended character |
| --- | --- |
| `minimal` | Restrained layout, clear typography, generous spacing, simple links |
| `bold` | Stronger visual hierarchy and prominent link treatments |

Both themes consume the same validated configuration and preserve the same
content, link/social order, disabled-entry behavior, metadata, and accessibility.
Choosing a theme changes presentation, not the meaning of the data.
The accepted [YAML v1 contract](configuration.md) defines shared color defaults,
the two collections, optional images, and metadata behavior without `site.url`.

## Requirements

- Responsive on small mobile screens and desktop viewports.
- Semantic HTML, meaningful accessible names, and visible keyboard focus.
- Sufficient default contrast, readable text, and usable link targets.
- No horizontal overflow for normal content; handle long labels and URLs.
- CSS variables for the configured primary, background, and text colors.
- Core content and navigation work without JavaScript.
- Local CSS/assets in the build output; no required remote font or icon service.
- Plain-text content escaped by the renderer.

Custom colors can reduce contrast. The validation/warning policy for that case
must be decided before declaring the themes accessible under user customization.

## Assets and extension

Use the accepted [platform and general-icon catalogs](configuration.md#controlled-catalogs).
General icons come from Lucide; platform marks come from Bootstrap Icons.
The platform selects its icon and default accessible label without restricting
the URL's domain. Only the general catalog is valid for `links[].icon`.
U03 must pin and bundle the selected SVGs, retain applicable upstream license
notices, and test installed-package rendering without a remote icon service.
No icon assets have been bundled yet.

Package the built-in templates and styles with the Python distribution, and test
rendering from an installed wheel. Client images are separate from package assets.

Third-party themes, arbitrary template paths, and remote theme loading are not
part of the MVP. A future extension contract should be driven by actual use cases.

## Acceptance evidence

For each theme, capture mobile and desktop screenshots, check keyboard focus
and navigation, inspect semantic markup and metadata, and test long/empty/disabled
content with the agreed contract. Report both automated and manual checks.
