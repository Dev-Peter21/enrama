# R03 technical preparation verification

Scope authorized on 2026-10-31: version/metadata, release documentation and a
manual preparation workflow on develop. External publisher/access setup,
integration into main, tags, releases, uploads and deployment remain outside
this delivery. Issue #17 is not complete merely because preparation works.

## Delivered behavior

- Metadata/lock target **0.1.0**, with Beta maturity and Python 3.12–3.15
  classifiers; dependencies/build inputs and generator behavior are unchanged.
  The version is **prepared, not published**.
- Stdlib `scripts/release.py` checks clean source identity/version, optional
  exact main dispatch/CI, archive metadata and matching schema. It creates a
  fresh bundle exclusively and verifies inventory, canonical record and hashes.
  Partial/unknown data is preserved, never overwritten or automatically cleaned.
- Explicit `ENRAMA_RELEASE_BUNDLE` selects the supplied canonical archives in
  installed-consumer tests. Invalid input fails without a rebuild fallback.
  Both hash verification and exact reviewed archive inventories are required.
- `release.yml` is workflow_dispatch-only, read-only, source/CI-gated, with one
  canonical construction and six downloaded-bundle consumers. It includes no
  publishing job, environment, OIDC permission, permanent token or release/tag
  mutation. Uploading Actions evidence is not publishing a Python distribution.
- Reports distinguish local rehearsal, future main execution and production
  authorization. Provenance always says `publication_authorized: false`.

## Executed local verification

Environment: macOS arm64, CPython **3.12.15**, uv **0.13.5**. The old temporary
tool installation had lost uv and Python stdlib files; pinned tools and locked
dependencies were restored before the clean **761-test** baseline.

Final full suite: **788 passed**, zero failures/errors/skips. The **27 added
cases** include 26 release/helper/fixture cases and one canonical archive-inventory
regression. Strict mypy passes **55 source files**; Ruff lint/format, generated
schema drift, constrained build and `git diff --check` pass.

Test-first evidence:

- Installed-wheel consumer failed expecting 0.1.0 while the package still
  reported 0.1.0.dev0; passed after metadata/lock preparation.
- 23 initial helper cases failed without the release helper, then passed.
- An explicit invalid bundle initially fell back to rebuilding and passed an
  inner consumer. The regression failed, then passed when the fixture verified
  and consumed the explicit set without fallback.
- Failed source-CI evidence was initially ignored by check-source; a two-case
  success/failure probe reproduced it, then passed after gating before build.
- A wheel with a coherent updated checksum but an extra unreviewed module
  initially passed the installed consumer. The regression failed first, then
  passed after exact inventory checks were shared with canonical consumers.

A real canonical set for implementation revision **5d32a28** was built with
hashed constraints, bundled/verified, and consumed by **three isolated installed
consumers**: wheel, sdist and wheel with PyYAML compiled from source. All passed.
They exercised the actual CLI, both themes, renderer I/O restrictions and POSIX
installed-preview lifecycle, with no canonical Enrama rebuild in those consumers.
Final delivery evidence and source/CI links are recorded on
[issue #17](https://github.com/Dev-Peter21/enrama/issues/17) after verification.

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests scripts
uv run --locked python scripts/schema.py --check
uv run --locked pytest --junitxml=reports/r03-preparation/pytest.xml -q
uv build --out-dir reports/r03-preparation/task2-archives --no-create-gitignore --build-constraint build-constraints.txt --require-build-hashes
```

Bundle/rehearsal commands are documented in
[release preparation](../release-preparation.md). Local machine evidence stays
ignored under reports/r03-preparation; no credentials are included.

## Workflow validation and execution boundary

Independent read-only whole-change review of `691bf1d..bc387dc` found **no
Critical, Important or Minor findings**. The reviewer freshly ran all **26
release-helper tests**, read the 788-pass suite output and checked the source,
canonical fixture, workflow and documentation. No deferred minor remains.

Review rulings preserve the authorized boundary: live dispatch/transfer needs
main integration; PyPI security/publisher setup, tagging, public installation and
post-publication recovery are future validation; digests are not cryptographic
authenticity against coordinated replacement or a hostile-filesystem sandbox;
Windows console SIGINT is outside existing POSIX probes. Earlier issue acceptance
and unchanged generator code were not re-audited as new work. These limitations
must not be promoted into successful hosted/public-release claims.

**actionlint 1.7.12** validated both CI and release-preparation YAML. Its official
download checksum was verified. Checkout/setup/upload pins reuse reviewed CI
versions. Download uses **actions/download-artifact v8.0.2**, full commit
`9000827ccba6bdab643e8b6fd33ac0654aef8333`; reviewed inputs include extraction and
digest mismatch failure. Source-CI query fields were checked against a real CI run.

The new manual workflow has **not run on GitHub**: workflow_dispatch requires its
definition on the default branch, and main integration is not authorized here.
Static validation, local commands and ordinary develop CI do not establish that
the new cross-job download/matrix orchestration has executed. That live check is
the next gate after separately authorized main integration.

Ordinary CI still runs the full six-environment regression/installed-artifact
matrix on develop; its run/result is separate from the manual workflow. Do not
claim unexecuted public PyPI installs, production ownership or Windows console
SIGINT behavior. No PyPI/GitHub release, tag, publisher setup or deployment is
performed by this verification.
