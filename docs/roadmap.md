# Roadmap

This is the implementation backlog specification. Task IDs below are stable
documentation identifiers, **not GitHub issue numbers**. The M0–M4 work is now
published as [GitHub issues](backlog.md) and tracked in the
[EnRama Project Kanban](https://github.com/users/Dev-Peter21/projects/5).
The issue index maps task IDs to issue numbers. Preserve these dependencies,
scope boundaries, and acceptance criteria when updating the backlog.

`0.1.0` is unreleased. F00 documentation, the F01 contract, and the F02 Python
package/tooling foundation are delivered on `develop`; the CLI and generator
remain planned. See [F02 verification](verification/f02.md). M5 remains a future
0.2 proposal and is outside the published MVP backlog.

## Milestones

| Milestone | Target | Verifiable outcome | Depends on |
| --- | --- | --- | --- |
| M0 — Foundation | 0.1 | Installable development skeleton, agreed CLI contract, initial CI | Documentation foundation |
| M1 — Configuration | 0.1 | Validated YAML and generated JSON Schema | M0 |
| M2 — Static Generator | 0.1 | Safe, repeatable static output through the reusable core | M1 |
| M3 — CLI & Themes | 0.1 | Complete local workflow and two usable themes | M2 |
| M4 — Public Release | 0.1.0 | Installable public package and tested hosting recipe | M3 |
| M5 — Local Visual Editor | 0.2 | Local editor reusing the same engine and YAML contract | M4 |

M0 does not deliver the user-facing MVP. M4 is complete only when every
[product acceptance criterion](product.md#release-acceptance-criteria) has evidence.
The milestone order is the default sequence; explicit task dependencies allow
independent documentation/design work to happen sooner.

## M0 — Foundation

### F01 — Define the CLI and filesystem contract

- **Design artifact:** [Accepted CLI and filesystem contract](cli-contract.md),
  agreed on 2026-10-22. This specification does not implement the commands.
- **Scope:** Agree on config discovery, command syntax, flags/defaults, exit
  codes, project/output paths, overwrite and cleanup rules, and preview lifecycle.
- **Dependencies:** Product and architecture documents; O02 is resolved by the
  accepted contract and recorded in the [decision log](decisions.md).
- **Acceptance:** Document valid and failing invocations of all four commands,
  including missing configuration, existing destination, unsafe output paths,
  occupied preview port, and clean shutdown. No generator implementation.

### F02 — Establish Python packaging and development tooling

- **Design artifact:** [Accepted Python development setup](development-setup.md),
  agreed on 2026-10-22; implemented on `develop` with
  [local verification evidence](verification/f02.md).
- **Scope:** Introduce the `src/` package, Python 3.12+ metadata, Hatchling, uv
  lockfile, pytest, Ruff, mypy, and documented developer commands.
- **Dependencies:** Completed F01; intended name `enrama` and target Python
  3.12–3.15 matrix are recorded in the setup. Namespace checks remain under O01.
- **Acceptance:** A fresh checkout can sync a locked environment, build wheel
  and source distributions, and import the package from an installed wheel.
  No functional generator or public PyPI release is required.

### F03 — Add foundation CI

- **Design artifact:** [Accepted foundation CI design](continuous-integration.md),
  agreed on 2026-10-22 and implemented on `develop` after authorization on
  2026-10-23; see [actual verification](verification/f03.md).
- **Scope:** GitHub Actions for lint, formatting, typing, tests, and packaging.
- **Dependencies:** F02.
- **Acceptance:** CI executes on PRs targeting `develop`/`main` and pushes to
  both branches. One Linux/Python 3.12 quality job and six mandatory verification
  environments cover Linux/Python 3.12–3.15 plus macOS and Windows/Python 3.12.
  Each environment reports positive test counts and isolated installation of
  wheel and sdist. Use read-only permissions and reviewed action pins; keep
  reports/artifacts for seven days. No release/deployment credentials.
  Execution results and trigger limitations are recorded in F03 verification.

## M1 — Configuration

### C01 — Freeze version 1 models and field policy

- **Scope:** Define Pydantic v2 models for the configuration and resolve O03,
  including fields for the promised social, favicon, and Open Graph support.
- **Contract:** The [YAML v1 field policy](configuration.md) was accepted on
  2026-10-23 and resolves O03. Models and tests were subsequently implemented on
  `develop`; the maintainer accepted [verification evidence](verification/c01.md)
  and requested issue #5 closure/Done on 2026-10-23.
- **Dependencies:** F02; maintainer review of the public contract.
- **Acceptance:** Valid examples and invalid types/defaults/unknown fields have
  tests. Stable unique link IDs, list order, enabled flags, and schema-version
  rejection are specified and tested. Documentation matches the models.

### C02 — Load YAML safely with actionable errors

- **Scope:** Safe YAML loading, model validation, file/field error context.
- **Contract:** The [safe loader and diagnostics design](yaml-loader.md) was
  accepted on 2026-10-23: controlled YAML without anchors/aliases/merges,
  explicit scalar resolution, 1 MiB/32-container/10,000-node limits, and at most
  20 diagnostics with honest source context. Implementation and
  [verification evidence](verification/c02.md) on `develop` were accepted by the
  maintainer on 2026-10-23; issue #6 is closed/completed and its existing Kanban
  card is Done.
- **Dependencies:** C01.
- **Acceptance:** Test malformed YAML, unsupported versions, invalid/duplicate
  IDs, missing files, unsafe YAML tags, and the URL protocol policy including
  obfuscated dangerous schemes. No rendering or filesystem output.

### C03 — Publish generated schema and editor instructions

- **Scope:** Derive JSON Schema from the models and document VS Code use.
- **Contract:** The accepted [C03 design](json-schema.md), agreed on 2026-10-23,
  defines validation-mode Draft 2020-12 generation, structural editor assistance,
  a local copy per client, stable v1 artifact naming, exact tool/source provenance,
  and manual updates committed with the client tool reference. Implementation
  and [verification evidence](verification/c03.md) are delivered on `develop`,
  awaiting maintainer acceptance; issue #7 stays open.
- **Dependencies:** C01, C02.
- **Acceptance:** The checked/generated artifact reflects model-expressed
  structural constraints, accepts representative valid examples, rejects
  representative structural errors, and works with the documented editor
  configuration. Complete C01/C02 validation remains authoritative; document
  schema gaps. No handwritten second contract.

## M2 — Static Generator

### G01 — Implement safe asset resolution and copying

- **Scope:** Resolve client-owned files inside the client root and copy only
  supported assets. Settle O04's asset and collision policies.
- **Dependencies:** C02; relevant F01 filesystem rules.
- **Acceptance:** Valid images copy correctly. Tests reject traversal, absolute
  external paths, symlink escapes, unsupported assets, and collisions according
  to the agreed policy. Original client files remain intact.

### G02 — Implement template rendering and metadata

- **Scope:** Trusted Jinja2 rendering with autoescaping, ordered enabled links,
  semantic HTML, SEO, canonical/Open Graph data, favicon, and local asset paths.
- **Dependencies:** C01, G01.
- **Acceptance:** Rendering tests verify escaping of malicious text, disabled-link
  omission, order, language/metadata, and paths suitable for domain-root and
  repository-subpath hosting. No remote theme loader or client editor.

### G03 — Coordinate safe, repeatable builds

- **Scope:** A core build service independent of CLI and web frameworks, with
  defined output/cleanup behavior and actionable failures.
- **Dependencies:** G01, G02, F01.
- **Acceptance:** The same inputs/version produce identical output hashes in
  clean and repeated builds. Failure/cleanup tests preserve protected inputs,
  enforce output-path safety, and handle stale files according to the contract.
  The generated fixture is serveable by a plain static server.

## M3 — CLI & Themes

### U01 — Implement init, validate, and build commands

- **Scope:** Connect Typer commands to shared models and core services, with
  a starter client project and helpful terminal errors.
- **Dependencies:** F01, C02, G03.
- **Acceptance:** CLI integration tests cover help, success, invalid input,
  missing files, and nonzero exit codes. Init/build obey overwrite rules and
  never silently destroy existing source content.

### U02 — Implement local preview

- **Scope:** Serve generated output locally with the agreed port, rebuild, and
  shutdown semantics.
- **Dependencies:** U01, G03.
- **Acceptance:** A test starts preview, requests a page and asset, and shuts it
  down cleanly. Default bind is `127.0.0.1`; occupied ports and build errors
  produce useful messages. No public hosted preview service.

### U03 — Deliver the minimal theme and controlled icon catalog

- **Scope:** Implement `minimal`, CSS variables, and licensed bundled icons;
  resolve O05 for assets and contrast policy.
- **Dependencies:** G02, C01.
- **Acceptance:** Rendering works from an installed wheel with bundled files.
  Mobile/desktop screenshots, keyboard checks, contrast checks, and long-label
  cases satisfy the [theme requirements](themes.md). Record asset licenses.

### U04 — Deliver the bold theme

- **Scope:** Implement a distinct `bold` presentation using the same contract.
- **Dependencies:** U03.
- **Acceptance:** Repeat the theme verification for `bold`; changing themes
  preserves content, order, accessibility semantics, and metadata. No separate
  data model or theme-specific business rules.

## M4 — Public Release

### R01 — Complete the example and end-to-end documentation

- **Scope:** Add redistributable demo assets and a client example covering the
  complete CLI workflow, customization, and common errors.
- **Dependencies:** U01, U02, U03, U04, C03.
- **Acceptance:** A clean environment follows the documentation from an
  installed built distribution through init/validate/preview/build. No private
  client data or unlicensed assets; all example paths resolve.

### R02 — Harden release validation

- **Scope:** Complete security regression, output portability, distribution,
  and repeatability tests using the [testing strategy](testing.md).
- **Dependencies:** R01, F03.
- **Acceptance:** Positive passing counts for the required suites; wheel and
  source-distribution install checks; both packaged themes render; hostile
  inputs fail safely; published files work without a Python runtime.

### R03 — Prepare and publish the first Python release

- **Scope:** Confirm namespace ownership and O06, add reviewed release automation,
  and prepare version `0.1.0`, changelog, artifacts, and GitHub release.
- **Dependencies:** R02 and explicit authorization to publish a package/release.
- **Acceptance:** Inspect artifacts and their included files before publication.
  After authorized publication, verify a clean install and CLI workflow from
  the actual public distribution. Record artifact/version provenance and update
  support policy. Do not claim PyPI availability before verification.

### R04 — Validate the GitHub Pages client recipe

- **Scope:** Publish a recipe using a pinned Enrama release, Pages artifact
  upload/deploy actions, and an independently maintained client repository.
- **Dependencies:** R03; explicit authorization for any test repository or deployment.
- **Acceptance:** The documented recipe builds and deploys to a reviewed test
  destination. Verify assets, metadata, links, and repository-subpath behavior
  at the live URL. Deploy only static output, with no production Python service.

## M5 — Local Visual Editor

### E01 — Design editor safety and round-trip editing

- **Scope:** Resolve O08: YAML preservation, local write protections, binding,
  origin/host/CSRF rules, file boundaries, conflict handling, and dependency impact.
- **Dependencies:** M4.
- **Acceptance:** Review a concrete design and round-trip library evaluation
  using files with comments, ordering, and unknown/unsupported content. Decide
  how CLI-only users avoid unnecessary editor dependencies before implementation.

### E02 — Implement the local editor using the shared core

- **Scope:** FastAPI + Jinja2/forms for the reviewed editing flow in
  `src/enrama/editor/`, reusing validation, rendering, and build services.
- **Dependencies:** E01.
- **Acceptance:** Users can edit, validate, preview, and save through the agreed
  flow without losing YAML comments. Test local write protections, default
  `127.0.0.1` binding, keyboard/mobile use, and interoperability with the CLI.
  No accounts, cloud backend, or independent generator implementation.

## Completion evidence

For every task, record the commit/PR, criteria verified, actual commands/checks,
positive test counts where applicable, and any remaining limitations. A blocked
external operation is pending work, not successful completion. Publishing,
releasing, or deploying is a separate action from local implementation.
