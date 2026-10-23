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

The GitHub repository uses `main`. Version `0.1.0` is the first release target,
not an existing release. The PyPI name and CLI command are intended to be `enrama`.
`main` remains the default branch; source-code implementation must target
`develop`. F02 supplies the importable development package `0.1.0.dev0`; it is
not a public PyPI distribution or a completed product release.

## Open decisions and when to resolve them

| ID | Decision needed | Resolve before |
| --- | --- | --- |
| O01 | Confirm PyPI availability/ownership and review potential name conflicts; naming is not legally cleared | Reserving/publishing the distribution (PyPI returned 404 on 2026-10-22; ownership and trademark clearance remain unresolved) |
| O03 | Required/default YAML fields, unknown keys, limits, URL schemes, color grammar, social-profile fields, favicon/OG image fields, and icon catalog | Freezing schema version 1 in M1 |
| O04 | Supported asset formats, size limits, and collisions between generated asset names; output replacement and stale-output behavior are settled by F01 | Asset/build implementation in M2 |
| O05 | License/source of bundled icons/fonts and contrast policy for customized colors | Theme implementation and M3 acceptance |
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
