# Decisions

This log separates choices supplied by the project brief from details that still
need review. It does not imply any implementation is present.

## Accepted foundation

| ID | Decision | Reason |
| --- | --- | --- |
| D01 | Product name: Enrama, provisionally | Short name associated with branches and connections |
| D02 | Public repository: `Dev-Peter21/enrama` | Owner requested the personal GitHub account rather than the organization in the original proposal |
| D03 | MIT license | Permissive open-source distribution |
| D04 | English documentation | Explicit maintainer preference during initialization |
| D05 | Python 3.12+, uv, Hatchling | Python learning goal and a single distributable package |
| D06 | Typer, PyYAML, Pydantic v2, Jinja2 | Modular CLI, safe loading, typed validation, and rendering |
| D07 | One repository and one Python package | Keep the initial system small |
| D08 | Versioned YAML and CLI first | Reviewable source of truth shared with later interfaces |
| D09 | Static output and no mandatory production backend/database | Independent hosting with no central service to operate |
| D10 | Two built-in themes: `minimal` and `bold` | Useful initial presentation choices |
| D11 | FastAPI local editor in 0.2 | Reuse Python core without a separate frontend stack |
| D12 | pytest, Ruff, mypy, and GitHub Actions | Test behavior, typing, style, and eventual packaging |
| D13 | Documentation-only initialization | Initial scope only; F02 package/tooling implementation was subsequently authorized |
| D14 | Accepted [CLI and filesystem contract](cli-contract.md) for F01 | Explicit config selection, fixed project-local `dist/`, protected replacement, manual loopback preview, and documented exit codes |
| D15 | Future source-code implementation integrates into `develop` | Explicit maintainer instruction on 2026-10-22; F02 implementation subsequently authorized on develop |
| D16 | Accepted [F02 development setup](development-setup.md): Python 3.12 local, target matrix 3.12–3.15, initial version `0.1.0.dev0`, src layout, uv/Hatchling, and a pytest/Ruff/mypy dev group | Maintainer-approved setup design; implemented on develop with local Python 3.12 verification; full matrix awaits F03 |
| D17 | Accepted [F03 CI design](continuous-integration.md): PRs/pushes for `develop` and `main`, one Linux/3.12 quality job, Linux/3.12–3.15 plus macOS/3.12 and Windows/3.12 verification, all required, uv 0.13.5, hashed build constraints, read-only token, SHA-pinned actions, and seven-day artifacts | Maintainer-approved design; implemented on develop after authorization on 2026-10-23; actual runs recorded in F03 verification |
| D18 | Accepted [YAML v1 contract](configuration.md): separate ordered links/socials, optional public HTTPS URL, strict types/defaults/limits, globally unique IDs, local registry-backed language validation, explicit URL allowlists, local image references, and stable platform/icon catalogs | Maintainer approved design, implementation, and delivery on 2026-10-23; C01 is closed/completed and its existing Project card is Done |
| D19 | Accepted [C02 loader/diagnostics contract](yaml-loader.md): controlled safe YAML, no anchors/aliases/merges, explicit scalar resolution, fixed 1 MiB/32-container/10,000-node limits, and up to 20 structured diagnostics with source context and F01 exit mapping | Maintainer approved design, implementation and delivery on 2026-10-23; C02 is closed/completed and its existing Project card is Done, see [C02 verification](verification/c02.md) |
| D20 | Accepted [C03 JSON Schema/VS Code contract](json-schema.md): validation-mode Draft 2020-12 from C01, structural editor assistance with C01/C02 authority, stable v1 artifact name, local client copy, exact version/source provenance, and manual tool/schema updates in one client commit | Maintainer approved the contract and authorized implementation on develop on 2026-10-23; implementation accepted on 2026-10-24; issue #7 is closed/completed and its existing Kanban card is Done, see [C03 verification](verification/c03.md) |
| D21 | Accepted [G01 local asset contract](assets.md): per-role PNG/JPEG/WebP/ICO, bounded Pillow decoding, all internal symlinks rejected, byte-preserving snapshots, full-SHA-256 paths, protected staging/deduplication and structured failures | Design and implementation accepted on 2026-10-24; issue #8 is closed/completed and its existing Kanban card is Done, see [G01 verification](verification/g01.md) |
| D22 | Agreed [G02 rendering contract](rendering.md): in-memory shared HTML base, trusted packaged Jinja2 with autoescape/StrictUndefined, matching G01 bindings, optional metadata, directory-form public URLs, same-context links and structured operational/internal failures | Maintainer settled behavior and requested English documentation/issue #9 update on 2026-10-24; documentation only, future implementation on develop; no builder, CLI or final theme presentation |

The GitHub repository uses `main`. Version `0.1.0` is the first release target,
not an existing release. The PyPI name and CLI command are intended to be `enrama`.
`main` remains the default branch; source-code implementation must target
`develop`. F02 supplies the importable development package `0.1.0.dev0`; it is
not a public PyPI distribution or a completed product release.

## Open decisions and when to resolve them

| ID | Decision needed | Resolve before |
| --- | --- | --- |
| O01 | Confirm PyPI availability/ownership and review potential name conflicts; naming is not legally cleared | Reserving/publishing the distribution (PyPI returned 404 on 2026-10-22; ownership and trademark clearance remain unresolved) |
| O05 | Font source/license and contrast policy for customized colors; icon providers are accepted by C01, while pinned SVG revisions and retained license notices must be verified when bundling | Theme implementation and M3 acceptance |
| O06 | Release credentials/trusted publisher ownership, release-versioning policy beyond the accepted initial `0.1.0.dev0`, and maintenance policy; the 3.12–3.15 target matrix is settled by F02 | Packaging setup as relevant, then M4 release automation |
| O07 | Dedicated private community conduct contact | Expanding community operations |
| O08 | Round-trip YAML writer and editor protections against unauthorized local writes | M5 editor implementation |

These decisions do not block creating a documentation foundation. A contributor
must raise the relevant question before implementing dependent behavior rather
than silently choosing a public contract.

## Resolved decisions

| ID | Resolution | Evidence |
| --- | --- | --- |
| O02 | Accepted on 2026-10-22: current-directory YAML discovery or explicit `--config`; output only in project-local `dist/`; no init overwrite or destructive bypass; ownership/integrity checks and staged replacement; manual preview at `127.0.0.1:8000` with optional port; exclusive output ownership; exit codes `0`, `1`, `2`, `3`, `70`, and `130` | [CLI/filesystem contract](cli-contract.md) and [F01 #2](https://github.com/Dev-Peter21/enrama/issues/2) |
| O03 | Accepted on 2026-10-23: required/default fields and null policy; strict types/unknown keys; text/list limits; cross-collection IDs/order/enabled rules; per-field URL schemes and restricted mailto/tel forms; registry-backed language subset; six-digit colors; social, favicon, and OG image fields; nine platforms and twelve general icons. Platform controls presentation only and never restricts destination domains. Lucide/Bootstrap Icons sources accepted; C01 models implement this policy. | [YAML v1 contract](configuration.md), [C01 verification](verification/c01.md), and [C01 #5](https://github.com/Dev-Peter21/enrama/issues/5) |
| O04 | Agreed on 2026-10-24: per-role PNG/JPEG/static WebP and PNG/ICO; 5 MiB image/1 MiB favicon/10 MiB unique total; fixed pixel/ICO limits; Pillow structure/decode validation; reject every internal symlink; preserve validated bytes; full SHA-256 canonical paths, exact-byte reuse and explicit collisions; English structured errors with F01 exit mapping. Output replacement, stale cleanup and publication remain F01/G03. | [G01 contract](assets.md) and [G01 #8](https://github.com/Dev-Peter21/enrama/issues/8); implementation accepted and issue completed on 2026-10-24, see [G01 verification](verification/g01.md) |
