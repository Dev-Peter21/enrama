# Themes

Status: requirements only. Neither theme has been implemented.

## Built-in themes for 0.1

| Theme | Intended character |
| --- | --- |
| `minimal` | Restrained layout, clear typography, generous spacing, simple links |
| `bold` | Stronger visual hierarchy and prominent link treatments |

Both themes consume the same validated configuration and preserve the same
content, link order, disabled-link behavior, metadata, and accessibility.
Choosing a theme changes presentation, not the meaning of the data.

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

Use a controlled icon catalog with explicit names and licensed distributable
assets. The names in the configuration example are design targets; the catalog
and licensing must be confirmed in M1/M3.

Package the built-in templates and styles with the Python distribution, and test
rendering from an installed wheel. Client images are separate from package assets.

Third-party themes, arbitrary template paths, and remote theme loading are not
part of the MVP. A future extension contract should be driven by actual use cases.

## Acceptance evidence

For each theme, capture mobile and desktop screenshots, check keyboard focus
and navigation, inspect semantic markup and metadata, and test long/empty/disabled
content with the agreed contract. Report both automated and manual checks.
