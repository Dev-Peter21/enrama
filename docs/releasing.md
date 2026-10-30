# First release and PyPI publication contract

Status: **R03 design accepted on 2026-10-30** for
[issue #17](https://github.com/Dev-Peter21/enrama/issues/17). Documentation only:
the issue remains open. No release workflow, external publisher configuration,
version bump, tag, GitHub Release or package upload is implemented by this change.
The development version remains `0.1.0.dev0` until authorized preparation.

## Outcome and scope

R03 delivers `enrama==0.1.0` on production PyPI, a matching GitHub Release and
verified installation from the actual public distribution. Existing
[R02 validation](verification/local-demo.md) is a prerequisite, not evidence
that this future version has already shipped. Verify each candidate's own SHA
and artifacts.

The live [Pages recipe](deployment.md) belongs to **R04 / #18**; final MVP
acceptance belongs to **MVP01 / #19**. Public installation is a post-upload R03
gate. Neither it nor R04 deployment can be a pre-upload prerequisite: that would
create a circular dependency.

**TestPyPI is optional and independent**, with separate accounts, names and
publisher configuration. It does not block R03 or establish production ownership,
availability or completion. This delivery does not set up or publish to TestPyPI.

## Approaches and selected control

| Approach | Tradeoff | Decision |
| --- | --- | --- |
| Manual GitHub Actions with Trusted Publishing | Explicit maintainer action tied to reviewed content, without a permanent PyPI token | Selected |
| Publication triggered by merge, push or tag | Less manual work, but gives ordinary Git operations publication side effects | Excluded by the accepted manual-publication rule |
| TestPyPI rehearsal | Exercises another index, with independent setup | Optional separate flow |

No merge, push, tag, documentation edit or GitHub Release event publishes by
itself. Separate preparation/verification from explicit upload authorization.
Approval of this design or workflow implementation does not authorize external
access setup, integration into main, tag creation or publication.

## Identity and external prerequisites

| Item | Contract |
| --- | --- |
| Distribution, import package and CLI | `enrama` |
| Repository | `Dev-Peter21/enrama` |
| Initial PyPI owner | Maintainer's personal account `peter-dev` |
| First public version and matching tag | `0.1.0` / `v0.1.0` |
| YAML contract | `schema_version: 1` |
| Initial supported Python | 3.12, 3.13, 3.14 and 3.15 |

The account exists; its projects page showed zero active projects when reviewed.
That does not verify email/2FA readiness or reserve the name. Before publication,
check verified email, mandatory 2FA readiness, current name availability and
authority to publish. Stop for a maintainer decision on conflicts; do not rename
automatically. Naming review is not legal trademark clearance.

Use GitHub Actions OIDC Trusted Publishing and short-lived credentials. Do not
fall back automatically to a permanent PyPI token. A pending publisher can create
the project at first publication but **does not reserve the name**. Restrict trust
to the intended repository, reviewed workflow identity and production publishing
environment. Exact workflow/environment names are implementation details to settle
before separately authorized external setup. Keep build/test jobs without upload
credentials; scope OIDC/write permissions to jobs needing them, and retain reviewed
action pins and hashed build inputs. Account security, publisher registration and
GitHub access/environment configuration are separate authorized setup steps.

## Source, version and tag

Prepare changes in **develop**, then use a reviewed, separately authorized
integration into **main** as release source. Record a full SHA on main and
successful CI for that exact revision. Do not publish from develop or an arbitrary
branch, trust a version string alone, or reuse a green run from unrelated content.
The future manual workflow runs from its reviewed main definition and verifies
the selected source SHA, version and tag target.

Create `v0.1.0` only for the verified, authorized candidate. It must match package
metadata and release notes. Once published, never move/reuse the tag or replace
archive contents. Any candidate changes invalidate approval of the old files.
Tag creation does not authorize or trigger the upload.

Compatible corrections use `0.1.1`, `0.1.2`, etc.; new features or deliberate
compatibility changes need a reviewed minor release such as `0.2.0`. No automatic
version increment or alpha/RC publication is required for the first release.
Package and YAML schema versions stay independent. Patches preserve CLI and YAML
v1; incompatible YAML changes need a separately reviewed schema/migration design.

## Preparation and canonical artifacts

Before upload, prepare version/lock consistency, actual release notes/changelog,
README, metadata/documentation links and support wording. Replace outdated
initialization/demo-only text, without claiming publication before it happens.
Check licenses/notices, schema freshness and the archive inventory; exclude
private/client data and accidental development resources.

Use the agreed uv/Hatchling setup and hashed build constraints to create **one
canonical release artifact set** from the selected revision:

- One wheel and one source distribution for `enrama==0.1.0`.
- Matching `enrama-v1.schema.json` from the checked C03 artifact.
- A checksum record covering those exact files, with source SHA, version/tag
  and build/verification run provenance.

Regression-test builds are disposable, not additional publishable sets. Validate
the canonical wheel/sdist outside the checkout; publish those exact archive bytes.
Do not rebuild per platform, after approval, between PyPI/GitHub or during retry.
PyPI receives wheel/sdist; schema, checksums and provenance accompany the GitHub
Release. Record tool and dependency versions actually used.

Preserve original files and hashes for recovery. Expired CI artifacts or lost
originals must not cause a silent rebuild after partial upload; stop for manual
recovery or a new-version decision. The implementation must provide retention
sufficient for the authorized operation rather than assuming expired files exist.

The [C03 contract](json-schema.md) still governs local client schema copies and
exact version/source provenance. Client updates remain manual, committing schema
and tool reference together. There is no automatic updater, second schema version
counter or change to init's behavior.

## Pre-upload verification and authorization

Require quality/regression checks, positive counts, schema drift and content
checks for the exact candidate. Preserve Linux/Python 3.12–3.15 plus macOS and
Windows/Python 3.12 verification, and the separate Linux/3.12 quality job.

Verify canonical wheel/sdist installation in clean environments outside the
checkout, real CLI commands, both themes/resources/licenses and advertised Python
metadata. Retain URL/YAML/HTML/path/symlink/output-preservation, repeatability and
root/subpath static-output checks. Honor existing capability boundaries: POSIX
SIGINT tests do not establish Windows console SIGINT behavior. Missing evidence,
zero tests or unavailable runners are not passes; report skips honestly.

Before upload authorization, present version, full SHA, tag target, exact
files/hashes and successful verification. Explicit maintainer authorization names
that candidate and production destination; it never floats to changed content.
Make upload credentials available only to the authorized stage. The implementation
must choose a GitHub approval mechanism that works for the initial single owner,
without assuming unconfigured features or an impossible self-review requirement.

## Publication and public-install verification

Upload only the approved canonical wheel/sdist through the manual Trusted
Publishing process. Verify production name/version/metadata and downloaded file
hashes. An accepted upload request alone is not completion.

Install the exact public version in clean environments outside the checkout,
without editable installs, PYTHONPATH, local-wheel substitution or reused dev
environments. Resolve public dependencies from advertised requirements rather
than relying on the repository development lock. Exercise public wheel and sdist,
record actual interpreter/platform/resolved versions, and run help/version,
init, edited-YAML validate, build and local preview with both themes. Do not claim
post-upload environments or lifecycle behavior that were not executed.

Finalize the matching GitHub Release with the reviewed notes, source/tag identity,
same wheel/sdist, schema, checksums and provenance. Confirm asset bytes agree with
PyPI and the approved set; publish accurate installation/documentation/support
information. Only then can the public-install/release criteria be completed.

## Failures, retries and defective releases

| State | Required response |
| --- | --- |
| Verification fails before upload | Do not upload. Keep diagnostics, fix/review and verify a candidate before authorization. |
| Upload/network failure or partial/uncertain success | Inspect PyPI files/hashes. Retry only the original files and intended version, skipping identical uploaded files; stop on any mismatch. |
| PyPI complete, GitHub Release incomplete | Verify PyPI state; retry only missing finalization with original files. No rebuild or replacement upload. |
| Public installation or CLI verification fails | Record failure and keep R03 open. Review correction/new-version and possible yanking with the maintainer. |
| Published version is defective | Use a reviewed new version such as `0.1.1`; never replace archives or move the published tag. |
| Originals lost, or name/version contents conflict | Stop for manual recovery or a new version/name decision; no force, guessing or automatic rename/bump. |

Yank a seriously broken, incompatible or vulnerable release only with maintainer
authorization and a recorded reason. Yanking preserves files/history, does not
remove installed copies and does not guarantee that an exact-version request
cannot install it. No automatic deletion/yanking, unyanking or tag movement is
an upload rollback. Network retries may repeat the same approved operation;
they cannot bypass checks, change bytes or make a new release decision.

## Maintenance policy

After publication, support the **latest patch in 0.1.x until 0.2.0 is published**.
Older patches should upgrade; there is no promise to maintain all old patches or
a parallel LTS line. A subsequent minor release needs its own reviewed support
statement, without presenting historical versions as current supported software.

Support Python 3.12–3.15 initially. A permissive `requires-python` bound is not
evidence for an untested future Python release. Do not drop an advertised Python
version in a `0.1.x` patch. Compatible bug/security fixes preserve CLI/YAML v1.
Maintenance is volunteer work, without fixed cadence, guaranteed response or
remediation time, or SLA. Keep the existing private vulnerability reporting path.
Update [SECURITY.md](../SECURITY.md) and support documentation when shipping;
this contract does not declare unreleased development code supported production
software today.

## R03 acceptance and evidence

Keep R03 open until evidence establishes:

1. Verified account/project authority and publisher setup, correct public name/version.
2. Exact main SHA/tag/version, successful checks and positive counts, canonical
   contents/hashes and isolated installs.
3. Explicit authorization before upload, with no automatic merge/push/tag/release-event publication.
4. Public downloads matching hashes, and clean public wheel/sdist consumption
   through the CLI workflow and both themes, with honest environment limitations.
5. Matching GitHub Release, unchanged archives, schema, checksums/provenance,
   actual changelog and accurate README/docs/support state.
6. Reported/recovered partial failures, without hidden replacement or false success.

Design documentation completes only the contract stage. Future steps are
preparation/implementation in develop, then separately authorized main integration,
external setup, tag/publication and public verification. TestPyPI, R04 deployment
and final MVP acceptance remain distinct.

## Primary references

- [PyPI account requirements](https://docs.pypi.org/your-account/managing-your-account/)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Pending publishers do not reserve names](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [Building, publishing and retries with uv](https://docs.astral.sh/uv/guides/package/)
- [Yanking releases](https://docs.pypi.org/project-management/yanking/)
- [Independent TestPyPI accounts/index](https://packaging.python.org/en/latest/guides/using-testpypi/)
