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
| D13 | Documentation-only initialization | Product programming remains future work |

The GitHub repository uses `main`. Version `0.1.0` is the first release target,
not an existing release. The PyPI name and CLI command are intended to be `enrama`.

## Open decisions and when to resolve them

| ID | Decision needed | Resolve before |
| --- | --- | --- |
| O01 | Confirm PyPI availability/ownership and review potential name conflicts; naming is not legally cleared | Publishing package metadata or reserving/publishing the distribution |
| O02 | CLI flags, defaults, exit codes, config discovery, init overwrite behavior, output cleanup, and preview lifecycle | M0's CLI contract and dependent implementation |
| O03 | Required/default YAML fields, unknown keys, limits, URL schemes, color grammar, social-profile fields, favicon/OG image fields, and icon catalog | Freezing schema version 1 in M1 |
| O04 | Supported asset formats, size limits, output collision policy, and stale-output handling | Asset/build implementation in M2 |
| O05 | License/source of bundled icons/fonts and contrast policy for customized colors | Theme implementation and M3 acceptance |
| O06 | Release credentials/trusted publisher ownership, versioning policy, supported Python CI matrix, and maintenance policy | Packaging setup as relevant, then M4 release automation |
| O07 | Dedicated private community conduct contact | Expanding community operations |
| O08 | Round-trip YAML writer and editor protections against unauthorized local writes | M5 editor implementation |

These decisions do not block creating a documentation foundation. A contributor
must raise the relevant question before implementing dependent behavior rather
than silently choosing a public contract.
