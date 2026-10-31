# Release preparation without publishing

R03 technical preparation implements the [accepted contract](releasing.md),
with version `0.1.0`/Beta metadata and Python 3.12–3.15 classifiers. **This version
is not yet published.** The helper/workflow has no upload command, publisher,
environment, OIDC/write permission, tag creation or GitHub Release creation.
R03 stays open until separately authorized setup, publication and public checks.

## Manual GitHub workflow

`.github/workflows/release.yml` responds only to `workflow_dispatch`, taking
`source_sha`, a full lowercase 40-character SHA. It requires the reviewed workflow
to execute from main in Dev-Peter21/enrama, at that exact SHA, on a clean checkout
with the matching package version. It reads the latest CI main-push run for that
SHA and requires completed success before canonical construction. CI remains
responsible for the full regression/quality matrix; it is not replaced by a
three-test packaging smoke result.

The preparation job checks quality/schema, builds one canonical wheel/sdist,
adds the checked schema and provenance, and retains one candidate artifact.
Six jobs download that same artifact with digest mismatch treated as an error:
Linux/Python 3.12–3.15, macOS/3.12 and Windows/3.12. Each verifies the complete
bundle before the existing isolated wheel, sdist and PyYAML-source consumers run.
An explicit invalid bundle fails instead of falling back to rebuilding Enrama.
The PyYAML-source case rebuilds a dependency, never the canonical Enrama archives.

Reports contain actual interpreter/environment, JUnit results and positive
consumer counts. Candidate/report retention is 90 days, without overwrite or
automatic cancellation of an active preparation for the same SHA. Retention
is finite: preserve files needed for later authorization/recovery; a missing or
expired original set is not permission to reconstruct a partially uploaded release.
Provenance records preparation/run identity and always
`publication_authorized: false`; future authorization must be a separate record,
not a rewrite of the immutable preparation bundle.

### Current dispatch boundary

GitHub requires a workflow_dispatch workflow to be present on the default branch.
Main integration is not part of this delivery. Therefore the manual workflow is
prepared on develop but has **not been dispatched remotely**. Do not change
default branches or add automatic triggers merely to bypass this gate. After
separately authorized main integration and a successful exact-revision push CI,
a maintainer may run the preparation workflow manually with that main SHA.
Even a successful run cannot publish: there is no publishing job in this slice.

## Bundle and verification commands

Use Python 3.12 and uv 0.13.5, with a clean committed checkout and fresh output
paths. From the repository root:

```console
uv sync --locked
git rev-parse HEAD
# Copy the full SHA printed above in place of <FULL_SHA> below.
uv run --locked python scripts/release.py check-source --expected-sha <FULL_SHA> --expected-version 0.1.0
uv build --out-dir reports/r03-archives --no-create-gitignore --build-constraint build-constraints.txt --require-build-hashes
uv run --locked python scripts/release.py bundle --archives reports/r03-archives --output reports/r03-candidate --expected-sha <FULL_SHA> --expected-version 0.1.0
uv run --locked python scripts/release.py verify --bundle reports/r03-candidate --expected-sha <FULL_SHA> --expected-version 0.1.0
```

The placeholder is documentation, not a shell argument to execute literally.
These commands are a **local develop rehearsal**, not verification that main
CI/publisher readiness or publication approval exists. `--require-main` is for
the guarded Actions context; never fabricate its environment locally as evidence.
In the workflow, `--ci-report` additionally checks the exact successful main
push CI run; missing/failed/wrong-source CI evidence blocks preparation.

`reports/r03-archives` must contain only the matching wheel/sdist. The output
directory must not exist, even if empty. The bundle consists of:

- `enrama-0.1.0-py3-none-any.whl` and `enrama-0.1.0.tar.gz`.
- `enrama-v1.schema.json`, equal to the checked C03 artifact and sdist copy.
- `release.json`: source SHA, intended version/tag, source ref, optional exact
  CI record, repository/run identity and payload sizes/SHA-256 digests.
- `SHA256SUMS`: hashes of those three payloads and release.json.

The verifier checks the exact inventory, regular non-linked files, canonical
record, metadata, schema, expected SHA/version and all checksums. Digests provide
integrity, not a signature, production ownership or publication authorization.
On failure preserve existing/partial output and inspect it; no force overwrite or
automatic cleanup is provided. Use a fresh path only after inspecting prior data.
As with other local tools, this is not a hostile continuous-filesystem-mutation
sandbox or a promise about untrusted/network filesystems.

### Consume the same archives locally

On macOS/Linux, from the same source revision:

```console
ENRAMA_RELEASE_BUNDLE=reports/r03-candidate uv run --locked pytest tests/integration/test_distribution.py::test_install_outside_checkout --junitxml=reports/r03-consumers.xml
```

On PowerShell set `$env:ENRAMA_RELEASE_BUNDLE = 'reports/r03-candidate'`, run the
same uv/pytest command, then remove that process environment variable. The
consumer fixture revalidates the supplied bundle against the checkout SHA;
source changes require a new reviewed candidate, not silently reusing old files.
Ordinary CI without this variable retains its disposable distribution tests.
Installed POSIX preview lifecycle coverage does not establish Windows console
SIGINT behavior; consumer records state the actual checks performed.

## Remaining release work

Separately authorize reviewed integration into main and then execute/inspect the
manual preparation on that exact revision. Verify PyPI account readiness and name
authority, choose/configure the restricted publisher/environment and implement
the separately reviewed upload/finalization stage. Only later authorize the exact
candidate's tag/publication. Download the actual public files, verify their hashes,
install in clean environments and finalize GitHub notes/assets/support state.
The current helper's 0.1.0 result is not a successful public install.

Keep TestPyPI optional/separate, deployment under R04 and final acceptance under
MVP01. See [GitHub's dispatch requirement](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
and [the action download contract](https://github.com/actions/download-artifact/tree/9000827ccba6bdab643e8b6fd33ac0654aef8333).
