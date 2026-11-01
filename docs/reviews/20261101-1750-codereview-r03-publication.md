# Code review — R03 publication — 2026-11-01 17:50 ART

## Metadata

- Repository: `Dev-Peter21/enrama`.
- Reviewed branch: `codex/enrama-local-demo`, delivery target develop.
- Base: `395f56d278b0752fd21d685e9537e4e5e15041ad`.
- Reviewed implementation: `ceb0794ebe4ba928205fe5137605287278713f80`.
- Reviewer: one fresh, read-only GPT-6-astra review, using the
  `code-review-fullstack`/requesting-code-review process.
- Method: complete publication controller, transports, workflow, public consumer
  path, contract/runbook and tests. No .NET/frontend/SQL stack applies.
- No uncommitted changes were part of the independent reviewed range. Corrections
  below were verified by the author with RED/GREEN tests; no second review claimed.

## Executive summary

No Critical/High defect was found in candidate identity, approval revalidation,
immutable-byte checks or missing-only recovery. Three Important/Medium gaps in
public verification were identified and corrected. No minor findings were deferred.
The independent reviewer ran 56 offline publication tests (all passed) and checked
diff whitespace; broader results are the implementer's executed evidence.

Original counts: Critical 0, High 0, Medium 3, Low 0, Info 0.
Corrections are recorded at `f58711b`; the author's post-fix full suite passed
**850 tests**, with zero failures/errors/skips. Ruff, format, strict mypy (58
files), schema and actionlint checks passed. Open material findings: **0**.
The implementation is suitable for develop after the corrections below. This is
not approval to integrate main, dispatch publication or claim live upload success.

## Findings and disposition

### M-1 — Public consumers omitted edited YAML and the bold CLI workflow

- Reviewed anchors: `.github/workflows/publish.yml:174`,
  `tests/integration/test_distribution.py:289` at the reviewed SHA above.
- Evidence:

  ```python
  assert cli("init", "cli-client").returncode == 0
  cli_source = "cli-client/enrama.yaml"
  assert cli("validate", "--config", cli_source).returncode == 0
  ```

- Impact/severity: all public jobs could pass and allow finalization without the
  contract's valid edited-YAML flow or bold CLI/build/preview path. Existing
  direct `render_html` tests did not establish the actual installed CLI behavior.
- Corrected: every installed consumer now writes valid client YAML for minimal
  and bold, validates/builds it, checks edited text/link and exact installed theme
  CSS, and previews both on POSIX. Windows explicitly reports no preview themes.
- RED: wheel consumer failed with missing `cli_themes` evidence. GREEN: actual
  installed wheel traversed both edited configurations and previews; parent
  assertions require both themes and `edited_yaml: true`.

### M-2 — Public dependency resolution retained a development-only PyYAML pin

- Reviewed anchor: `tests/integration/test_distribution.py:422`.
- Evidence:

  ```python
  assert metadata["pyyaml"] == "6.0.3"
  ```

- Impact/severity: a resolver-selected compatible newer version could block
  finalization after upload, despite satisfying the advertised `>=6.0.3,<7`.
- Corrected: public consumers validate that advertised range; ordinary locked
  consumers retain the development-version check. No package/dependency pin changed.
- RED/GREEN: dedicated tests accept synthetic 6.0.4/6.1.0 and reject out-of-range
  values; a newer version is not asserted to exist on PyPI. Real behavior checks
  and actual selected-version evidence remain required.

### M-3 — Consumer evidence omitted resolved versions for several dependencies

- Reviewed anchor: `tests/integration/test_distribution.py:169`.
- Evidence:

  ```python
  "installed": sorted(x.metadata["Name"] for x in m.distributions()),
  ```

- Impact/severity: names alone cannot reproduce/debug resolution changes in a
  clean public consumer; outer development-environment evidence is insufficient.
- Corrected: captured consumer JSON now records every installed distribution's
  name/version. Assertions require the complete name inventory and nonempty
  versions; JUnit system-out retains the actual isolated consumer evidence.
- Verified together with the installed wheel and full regression; no public
  dependency resolution was substituted with local archives or the dev lock.

## Scope decisions and declined-to-judge dispositions

The parent accepts the following boundaries; none is hidden live-release proof.

1. Live OIDC exchange/upload acceptance was explicitly unauthorized; test it only
   during separately approved production execution. Cost if assumptions fail:
   upload stops and R03 remains open.
2. Actual public wheel/sdist consumption in hosted environments is unavailable
   before publication; commands/test branches are reviewed, not called public
   success. Cost: public incompatibility can block finalization after upload.
3. Live tag/Release mutations/recovery were unauthorized; offline fake transports
   cover behavior. Cost: an API/platform difference can leave a recoverable draft.
4. Account/publisher/environment configuration is separate setup evidence; no
   private account information was queried or published in this review.
5. Main integration, dispatch, approvals, tags and publishing execution are excluded;
   authorized develop delivery is not a generic GitFlow process defect.
6. Changed main, missing/expired originals and failed-only reruns deliberately
   fail closed. Cost: maintainer recovery/fresh exact-identity dispatch is needed.
7. Windows SIGINT preview remains outside supported lifecycle coverage; the new
   theme evidence explicitly reports that limit.
8. Continuous changes by another privileged actor are outside the workflow's
   trust/concurrency model; no cross-service atomic transaction is promised.
9. Unchanged generator/UI/runtime code beyond the activated installed consumers
   is covered by regression, not a fresh complete runtime audit.
10. Post-publication documentation/support updates, R03 acceptance/closure, R04
    deployment and MVP acceptance remain later work and are never auto-completed.
11. Repository English documentation/develop-delivery instructions supersede the
    skill's unrelated Windows-global paths and generic branching preferences.
12. Ruff/mypy/schema/actionlint/full-suite results are executed author evidence;
    the fresh reviewer independently reran only publication tests and whitespace.

## Verification and limits

See [the verification record](../verification/r03-publication.md) for final local
and delivered CI counts. No second independent review was dispatched after the
single material-fix pass. No real publishing credentials, tokens, tags, releases
or public uploads were exercised by this implementation/review.
