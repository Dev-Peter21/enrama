# Manual production publication

Status: **0.1.0 published and verified on 2026-11-02**, from source
`73602dd85aca2cb02df607d9e815a1c76218b733`, after separately authorized main
integration, preparation, publication and maintainer approvals. See the
[execution record](verification/r03-release.md). This runbook describes the
implemented controls; it is not permission to dispatch again or replace 0.1.0.
[R03](releasing.md) remains open for maintainer acceptance.

## Identity and controls

The production publisher is restricted to `Dev-Peter21/enrama`, workflow
filename `publish.yml`, environment `pypi-production`. That environment allows
only branch `main`, requires approval by `Dev-Peter21`, disables administrator
bypass, and has no permanent upload secret. Self-review is allowed for the
personal-maintainer flow: this is a manual approval, not a two-person control.
No private account security details are included in this public document.

`.github/workflows/publish.yml` responds only to `workflow_dispatch`. It serializes
attempts for `enrama==0.1.0` without cancelling an active upload. There are no
push/tag/release-event triggers, TestPyPI destination or automatic version bumps.
The helper rejects other repositories, branches, workflow identities and sources.

| Stage | Authority | Behavior |
| --- | --- | --- |
| Inspect | Contents/actions read | Check exact main/source, successful preparation/CI, artifact ID/run/ZIP digest, original provenance, accessible tag/release state and production bytes; present checksums in the run summary. |
| Upload | `pypi-production` approval; OIDC write; contents/actions read | Repeat source/artifact and production checks after approval; stage only missing original archives; call uv with Trusted Publishing required. If both files already match, skip uv and token exchange. |
| Public verification | Contents/actions read | Six environments compare actual public downloads with the originals, then install `enrama==0.1.0` from production PyPI into clean consumers: wheel and source distribution, both themes and actual CLI behavior. |
| Finalize | A second `pypi-production` approval; contents write; actions read; no OIDC | Repeat source/bundle/public checks, require all six current-attempt public jobs successful, preserve/create exact tag, upload only missing identical assets to a draft, verify asset bytes and finalize the matching GitHub Release. |

Only the upload job has `id-token: write`; only finalization has contents write.
Checkout never persists credentials. Tokens are supplied only to the steps that
need them. Do not approve either environment gate on behalf of the maintainer.
The first approval authorizes uploading the named candidate; the second authorizes
the matching tag/GitHub Release. Entering the dispatch phrase alone cannot bypass
the environment approvals.

## Execution prerequisites and frozen first release

The requirements below governed 0.1.0 and remain authorization boundaries.
The current controller is fixed to version 0.1.0: a future package version needs
reviewed version/controller changes and a new candidate. Do not run it on a new
documentation SHA to republish 0.1.0, move its tag or substitute rebuilt files.

1. Separately review/authorize develop integration into main. Do not dispatch from
   develop. The workflow must exist on main and run from that reviewed definition.
2. Wait for successful exact-source main push CI. Run the preparation-only workflow
   for that **same main SHA** and inspect its original artifact and all six jobs.
3. Preserve its five files and ZIP digest outside finite Actions retention. Review
   notes in `docs/release-notes/0.1.0.md`, metadata, namespace authority and current
   external setup; a pending publisher does not reserve the PyPI name.
4. Obtain explicit authorization naming the production candidate, version/source,
   original preparation run, artifact ID and ZIP SHA-256. No prior design,
   implementation or preparation approval authorizes this upload/tag/release.

The controller requires dispatch SHA, candidate SHA and current main SHA to agree.
Consequently the historical preparation of `395f56d` cannot publish through a
newer workflow revision. **Before any upload**, prepare/review a new candidate
after authorized main integration. Preserve the historical candidate untouched;
never relabel its provenance. During upload/recovery keep main at the authorized
source. An intervening main change fails closed and needs manual recovery, not
automatic rebuilding or silently accepting an older candidate under newer code.

## Dispatch inputs

Every input is required; IDs are positive decimal integers and hashes are full
lowercase hex. These are public identities, not credentials.

| Input | Value |
| --- | --- |
| `source_sha` | Reviewed 40-character main SHA |
| `preparation_run_id` | Successful `Release preparation` run for that source |
| `candidate_artifact_id` | Original `r03-candidate-SOURCE_SHA` artifact from that run |
| `candidate_zip_sha256` | Reviewed 64-character ZIP digest reported by GitHub, without `sha256:` prefix |
| `authorization` | `publish enrama==0.1.0 SOURCE_SHA RUN_ID ARTIFACT_ID ZIP_SHA256` with all four identities substituted |

After the separate authorization, dispatch `publish.yml` from **main** in the
GitHub Actions UI using those exact values. Inspect the run summary before
approving upload. The helper checks the original preparation attempt, all seven
successful preparation jobs, nonexpired artifact ownership/digest, complete safe
ZIP inventory and canonical bundle hashes/provenance. It also re-reads the source
CI run and requires successful exact-source main push CI. It never builds Enrama.
No arbitrary bundle URL, local replacement path, destination or version is accepted.

Review the public consumer reports before approving finalization. Six jobs each
require two passed tests: Linux/Python 3.12–3.15, macOS/Python 3.12 and
Windows/Python 3.12. POSIX preview shutdown is not executed on Windows. These
tests resolve public runtime dependencies instead of installing the development
lock; source builds retain the reviewed hashed build constraints. The original
bundle is only the hash/inventory reference, never an installation substitute.

Final notes include the source, original preparation URL and ZIP digest. The
GitHub Release receives the **same five original bundle files**; `release.json`
keeps `publication_authorized: false`. Authorization is recorded by the dispatch
and environment approval events, not by rewriting preparation provenance.

## Partial states and retries

- Before any upload, inspect production's version JSON. Existing public wheel
  or sdist must have the exact original name, size, digest, actual downloaded
  bytes and no yank flag. Unknown/duplicate files, mismatches, unexpected
  metadata and non-404 HTTP/network failures stop the workflow.
- If the intended version is absent but the project name already exists, stop
  for a maintainer ownership decision. Never assume an unreserved name is yours.
- On a partial/uncertain upload, inspect PyPI, keep originals and dispatch again
  with the same approved source/run/artifact/digest. Only missing files are staged;
  uv checks production for matching files if another upload completed meanwhile.
  There is no permanent-token fallback or automatic alternate version/destination.
- When PyPI is complete but GitHub finalization failed, the upload job skips uv
  entirely. Public checks run again; finalization resumes only missing assets or
  publishing an existing matching draft. Draft lookup uses the release listing,
  because GitHub's by-tag endpoint describes published releases. Ambiguous lists
  or multiple matching drafts stop for manual inspection.
- Prefer a **fresh manual dispatch** for recovery, rather than “re-run failed
  jobs”: finalization requires all six public jobs in the current run attempt.
  After failed-only reruns, jobs from a prior attempt do not satisfy that gate.
- Existing tags must resolve to the exact source commit; annotated tags are
  followed at most five levels. Existing notes/assets must match; no tag movement,
  asset clobber, deletion, replacement, yank or hidden rollback is implemented.
- If an upload reports success but the asset cannot yet be confirmed, stop and
  retain the draft. Retry after inspecting propagation; never loop upload until
  something changes. Lost/expired originals or changed main require manual
  recovery, even when some public bytes already match.

Inspection, upload, public-consumer and finalization diagnostics are retained for
90 days. Preserve the original candidate before it expires. A failed or zero-test
public result blocks finalization and leaves R03 open. A defective public package
needs a separately reviewed patch/version and possible authorized yanking.

After actual publication, update README/changelog/security/support to the observed
shipped state, inspect PyPI/GitHub bytes and public-consumer evidence, and obtain
maintainer acceptance before closing R03. This workflow does not auto-close issues,
mark the MVP complete or deploy a client site; R04/MVP01 remain separate work.

## Verification limits

See [implementation verification](verification/r03-publication.md). Offline tests
exercise identity, recovery and conflict handling through fake remote boundaries;
they do not establish that OIDC/upload/tag/Release mutation works live. Ordinary
CI on develop runs regression and static workflow checks. Actual 0.1.0 public
consumption is recorded in the [publication evidence](verification/r03-release.md);
it is not evidence for a future candidate. The implementation-only record retains
its historical limits.

References: [uv publishing/retries](https://docs.astral.sh/uv/guides/package/),
[GitHub release API](https://docs.github.com/en/rest/releases/releases),
[PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
