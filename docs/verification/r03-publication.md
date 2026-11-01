# R03 publication implementation verification

Date: 2026-11-01. Scope: implement/review the separate publication workflow on
develop. Main integration, tags, release creation, token exchange and uploading
were not executed. This document is implementation evidence, not evidence of a
successful public release or installation.

## Checks executed

- **843 local tests passed**, zero failures/errors/skips, Python 3.12.15.
- **56 new offline publication tests** cover exact dispatch/source/authorization,
  successful run/job/artifact identity, expired/wrong ZIP/provenance/source CI,
  safe exclusive extraction, actual canonical bundle handling, partial/complete
  and conflicting PyPI state, immutable tag checks, missing-only release assets,
  draft discovery/recovery, unconfirmed asset preservation and failed public gates.
- Public consumer argument tests require production index/version, uncached
  wheel/sdist selection and absence of local archive substitution. The actual
  network installation branch is deliberately unexecuted until publication.
- Ruff lint/format, strict mypy (**58 source files**), checked JSON Schema and
  actionlint 1.7.12 passed for all three workflows.
- Existing wheel/sdist/PyYAML-source installed consumers passed as part of the
  full suite. Generator/runtime source and dependency lock were not changed.
- Read-only GitHub metadata checks confirmed the actual historical preparation
  run/artifact API shape used by the controller. This is not dispatching the new
  workflow or approving its candidate.
- The actual historical artifact download through the new transport matched ZIP
  SHA-256 `fc1bed647f6ed791499efd6331bf389cbfacc9f3e13e10dfc836018187e873bf`.
  A media-type regression first reproduced HTTP 415: artifact redirects use the
  JSON API media type, while release assets need octet-stream. The corrected
  real read-only download and dedicated offline test both passed.

## RED/GREEN evidence

1. Missing publication controller produced a module-not-found failure; initial
   exact identity/conflict tests passed after implementation.
2. Missing workflow and public-install argument helper produced three failures;
   scoped manual jobs and production-only arguments passed afterwards.
3. Read-only inspection and unconfirmed release assets failed (including an
   observed unbounded recursion); controls now preserve drafts and stop after one
   unconfirmed upload instead of repeatedly attempting it.
4. A draft absent from GitHub's published by-tag endpoint caused a duplicate-create
   attempt in the fake transport; listing existing drafts now resumes the draft.

## Honest boundaries

All write operations and public state tests use fake remote boundaries. No test
created a Git ref/release, uploaded files, acquired a publishing token, approved an
environment job or changed the registered publisher. No `publish.yml` dispatch
was performed, including from develop. Actual OIDC, upload propagation, hosted
approval behavior, actual PyPI consumption and live release recovery remain to be
verified during a separately authorized future production execution.

The implementation requires one reviewed main SHA across workflow, candidate and
current branch tip. Main advancement during partial publication fails closed and
needs manual recovery; it is not permission to rebuild originals. Failed-only
Actions reruns cannot use public verification jobs from another run attempt;
use a fresh dispatch of the same original identities. Private draft visibility
depends on GitHub token access; the write-authorized finalization stage rechecks
drafts and assets before mutations. A list with 100 releases or multiple matching
drafts is deliberately ambiguous and stops for manual inspection.

Post-publication README/changelog/support updates and maintainer acceptance are
still required before closing R03. Client Pages deployment and final MVP
acceptance remain R04/MVP01. See the [runbook](../publication.md).
