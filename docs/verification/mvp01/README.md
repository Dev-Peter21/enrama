# Enrama 0.1.0 MVP visual evidence

This record supports [MVP01 #19](https://github.com/Dev-Peter21/enrama/issues/19).
The screenshots show the synthetic Amapola Estudio demo built from the public
Enrama 0.1.0 release.

| Theme | Capture source | Mobile (375 px) | Desktop (1280 px) |
| --- | --- | --- | --- |
| bold | Local replay of the exact approved Pages artifact | [PNG](bold-375.png) | [PNG](bold-1280.png) |
| minimal | Live GitHub Pages demo | [PNG](minimal-375.png) | [PNG](minimal-1280.png) |

- **bold** was verified live at client commit `9e10b488de88aef600cbd354890f9705579ad789`.
  The archived ZIP has SHA-256 `71f055b8888c6f305c246e7bcaa15e593630e7df14d670787a95762d04ad0290`.
  The screenshots replay that static artifact at a local root.
  [Deployment run](https://github.com/Dev-Peter21/enrama-pages-demo/actions/runs/42073302021) ·
  [Artifact 13436553276](https://github.com/Dev-Peter21/enrama-pages-demo/actions/runs/42073302021/artifacts/13436553276).
- **minimal** serves the final public demo at client commit `79d1cacb0a6f34ce25c926b9bad6fcfb9c9536a7`.
  The archived ZIP has SHA-256 `176fdbf838401354814573d17b52f63362ce2d9e0d512900a34a5b08846864e5`.
  All five public files matched the approved artifact byte for byte at capture.
  [Public demo](https://dev-peter21.github.io/enrama-pages-demo/) ·
  [Deployment run](https://github.com/Dev-Peter21/enrama-pages-demo/actions/runs/42296151367) ·
  [Artifact 13542390907](https://github.com/Dev-Peter21/enrama-pages-demo/actions/runs/42296151367/artifacts/13542390907).

At 320, 375 and 1280 px, Chrome exposed six links in its accessibility tree.
Keyboard tabbing reached them in the configured order with visible focus.
The stylesheet and avatar loaded, favicon and Open Graph image references
resolved to the expected assets, and the pages showed no horizontal overflow.
Both themes also passed their original public subpath checks.
[Original Pages verification](https://github.com/Dev-Peter21/enrama/issues/18).
