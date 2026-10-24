# Testing strategy

Status: packaging/locking, configuration/schema and G01 asset tests are
executable on `develop`. Product CLI, rendering/building, preview and themes
remain planned coverage.

The accepted [CLI/filesystem scenarios](cli-contract.md#acceptance-examples)
define future command and path-safety acceptance checks. Their documented
expected outcomes are not executed product tests.

## Core layers

| Layer | Cases to verify |
| --- | --- |
| Configuration | Safe YAML, malformed syntax, type errors, version handling, required/default/unknown fields |
| Links | Unique stable IDs, ordering, disabled behavior, protocol allowlist, normalization |
| Assets | Missing files, allowed formats, containment, symlinks, output collisions |
| Rendering | Escaping, semantic content, SEO/Open Graph, language, favicon, local paths |
| Build | Repeatable output, stale files, protected inputs, unsafe destinations, failure handling |
| CLI | Help, init/validate/build, diagnostic text, exit codes, overwrite behavior |
| Preview | Loopback binding, actual HTTP response, occupied port, shutdown |
| Themes | Both layouts, packaged templates/assets, long content, responsive and keyboard use |

Use small unit tests for model and service behavior, then integration tests for
the CLI and generated output. Keep fixtures synthetic and redistributable.
Assert behavior and observable failure modes rather than implementation details.

## JSON Schema and editor acceptance

The accepted [C03 contract](json-schema.md#implementation-acceptance)
defines deterministic generation/staleness checks, schema validation of
representative examples/structural failures, documented runtime-only rules,
exact client provenance, and actual local/offline VS Code completion/diagnostic
evidence. Execution is recorded in [C03 verification](verification/c03.md),
including actual VS Code Extension Host provider results. A schema check
does not replace C01/C02 validation or demonstrate an editor session.

## Local asset acceptance

The agreed [G01 contract](assets.md#implementation-acceptance) defines
tests for real image decoding, role-specific byte/pixel/container limits,
animation rejection, all internal symlinks, special files, exact snapshot copying,
content-path deduplication/collisions, staging protections and safe structured
errors. The asset API and Pillow dependency are implemented on `develop`;
installed wheel/sdist probes exercise each format outside the checkout. See
[G01 verification](verification/g01.md) for executed counts, environments and
remaining boundaries.

## Security regression cases

G02's agreed [implementation acceptance](rendering.md#implementation-acceptance)
adds future checks for parsed HTML semantics, body/attribute escaping, separate
enabled collections, metadata omission, directory URL derivation, same-context
destinations, root/subpath static resource requests, deterministic in-memory
output, safe failure classification and installed packaged templates. These
checks are not implemented or executed by the G02 documentation change.

C02's accepted [loader contract](yaml-loader.md#required-acceptance-cases) adds
loader tests for UTF-8/BOM, document shape, duplicate keys and related
locations, forbidden YAML constructs, explicit scalar resolution, exact parser
limit boundaries, deterministic diagnostic ordering/truncation, and safe display.
Executed evidence is recorded in [C02 verification](verification/c02.md). C01's
model evidence remains recorded separately in [C01 verification](verification/c01.md).

- Reject dangerous URL protocols, including whitespace/case/encoding boundary
  cases defined by the agreed normalization policy.
- Escape HTML/script-like content in names, descriptions, and link titles.
- Reject executable YAML constructors and unsupported schema versions.
- Prevent asset reads outside the client root through traversal or symlinks.
- Prevent output writes or cleanup from destroying source files or unrelated paths.
- Validate icons/themes from the supported catalog rather than interpreting HTML.

The future editor adds local-origin, CSRF/write authorization, path containment,
and comment-preserving save tests. These are not prerequisites for the CLI MVP
because the editor is outside version `0.1`.

## Distribution tests

F02's accepted [implementation checks](development-setup.md#implementation-acceptance-and-evidence)
cover package/tooling setup and isolated artifact installation on Python 3.12.
See the [F02 verification record](verification/f02.md) for executed evidence.
F02's five tests cover wheel/sdist installs, explicit contents/repeatability,
and missing/stale lock rejection. The accepted [F03 CI design](continuous-integration.md)
automates six required verification environments: Linux/Python 3.12–3.15,
macOS/Python 3.12, and Windows/Python 3.12. A separate Linux/3.12 job checks
Ruff, formatting, and strict mypy. See the [F03 verification record](verification/f03.md) for executed runs.
Additional subprocess tests exercise invalid/missing/empty/all-skipped JUnit
reports, interpreter mismatch and missing distributions. Software acceptance
requires positive test and isolated wheel/sdist installation evidence in every
selected environment.

Build wheel and source distributions. Inspect their content, install in clean
environments outside the source checkout. Later product tasks must additionally
invoke the CLI entry point and render both themes. Ensure templates, CSS, icons, and license files are present and that
tests do not accidentally import from the working tree.

Execute the agreed Python matrix before claiming compatibility. Run an end-to-end example with
the installed artifact. Public release verification must additionally install
the actual published package and record the resolved version.

## Output and UX verification

Build twice with identical configuration/assets/version and compare output hashes.
Serve output through a plain static server and check it under both root and
repository-subpath URLs. Confirm no Python, API, database, or Enrama service is
required to use the published site.

For both themes, record mobile/desktop screenshots, keyboard navigation/focus,
default contrast, long-content behavior, and accessible names. Automated checks
complement manual use. Define behavior for invalid customized contrast before
making accessibility claims about arbitrary user colors.

## Reporting evidence

Record checks actually executed, positive test counts, failures, and environment
limitations. A skipped suite, zero collected tests, or a failed browser startup
does not establish passing coverage. Report inherited failures explicitly.
The first executable CI is provided by [F03](continuous-integration.md).
