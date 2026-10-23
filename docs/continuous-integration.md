# Foundation CI design

Status: **implemented on `develop`**, following the design approved on
2026-10-22 and implementation authorized on 2026-10-23 for
[issue #4](https://github.com/Dev-Peter21/enrama/issues/4).
The [workflow](../.github/workflows/ci.yml) and CI evidence gates are executable.
See the [verification record](verification/f03.md) for actual run results.

## Purpose and delivery boundary

Automate the quality and distribution checks established by
[F02](development-setup.md). A successful run must show that the selected Python
interpreters actually executed the tests and that both distribution formats can
be installed independently of the source checkout.

Implementation must integrate into **`develop`**. Implementation branches, when
used, start from and target `develop`. The default branch remains `main`.
The maintainer subsequently authorized F03 implementation on 2026-10-23.
Its source changes remain limited to workflow, packaging tests and CI helpers.

F03 covers foundation CI only. CLI/generator features, release workflows, PyPI
publication, client deployment, and branch-protection configuration remain
separate work. The existing F02 source/package version remains `0.1.0.dev0`.

## Events and branches

The workflow is configured to run for:

- Pull requests whose **base branch** is `develop` or `main`.
- Pushes to `develop` or `main`.

Use the ordinary `pull_request` event, including contributions from forks,
without release/deployment secrets. Do not use privileged `pull_request_target`
execution for contributor code. Keep checks active for documentation changes
as well; no path exclusions are part of this initial design.

The `main` trigger becomes effective when the workflow reaches that branch
through a separately authorized integration. Defining that trigger does not
merge `develop` into `main`.

Cancel superseded runs for the **same PR**, without canceling checks for another
PR. Branch-push concurrency must be scoped to that branch and kept distinct
from PR runs. Cancellation of an obsolete run is not passing evidence for the
current revision.

## Required jobs and matrix

Use one quality job and six verification environments: **seven required jobs**
in a complete current run.

| Job identity | Operating system | CPython | Responsibility |
| --- | --- | --- | --- |
| Quality | Linux | 3.12 | Ruff lint/format and strict mypy |
| Verify Linux 3.12 | Linux | 3.12 | Full tests, build, and isolated artifact installs |
| Verify Linux 3.13 | Linux | 3.13 | Full tests, build, and isolated artifact installs |
| Verify Linux 3.14 | Linux | 3.14 | Full tests, build, and isolated artifact installs |
| Verify Linux 3.15 | Linux | 3.15 | Full tests, build, and isolated artifact installs |
| Verify macOS 3.12 | macOS | 3.12 | Full tests, build, and isolated artifact installs |
| Verify Windows 3.12 | Windows | 3.12 | Full tests, build, and isolated artifact installs |

All six verification environments are mandatory. Do not use `continue-on-error`
or classify a selected version as experimental. Disable matrix fail-fast so a
failure in one environment does not hide results from the others. Quality and
matrix outcomes must all remain visible; a failure makes the CI run fail.

Use stable CPython releases, selecting the latest available stable patch for
each agreed minor version. Record the actual patch version used. If an
interpreter or required tool cannot be installed, fail the job: do not substitute
3.12, silently skip the environment, or report compatibility as verified.

The workflow selects `ubuntu-24.04`, `macos-15`, and `windows-2025`.
Reviewed action SHAs and their releases are recorded below. Record runner image/OS and architecture in the
evidence. This design verifies four Python versions on Linux and basic
cross-platform behavior on 3.12; it does not establish a twelve-cell matrix or
support for every CPU architecture/interpreter variant.

## Interpreter selection and locked setup

- Install **uv 0.13.5**, matching `tool.uv.required-version` and F02.
- Install the current patch explicitly with `uv python install` for each
  selected minor and set `UV_MANAGED_PYTHON=true`, so a preinstalled older patch
  cannot win interpreter discovery. Select Python explicitly for each job. The repository's `.python-version`
  remains `3.12` for local development; it must not override the matrix.
- Use the selected interpreter consistently for synchronization, `uv run`,
  builds, and both consumer-install environments. Set `UV_PYTHON` or the
  equivalent explicit action selection, and ensure subprocesses inherit it.
- Assert the running interpreter's major/minor version against the expected
  matrix entry. Log its actual version and executable location; printing a
  matrix label alone is insufficient.
- Synchronize with `uv sync --locked`. Use `uv run --locked` for quality/tests.
  Missing/stale locks must fail rather than being regenerated. Verify that the
  committed lockfile and dependency inputs remain unchanged.
- Start with an independent virtual environment in each job. If caching is
  introduced, cache uv downloads rather than sharing `.venv/` between jobs;
  correctness must also hold on a cold cache.

Keep Hatchling and the transitive isolated-build dependencies constrained by
the committed `build-constraints.txt`, with hash verification enabled. Do not
treat `uv.lock` as a lock for an isolated build environment. Dependency upgrades
are reviewed maintenance, not an automatic CI repair step.

## Quality job

Run once on Linux/Python 3.12 using the existing tool configuration:

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests scripts
```

Ruff remains the only formatter. Both Ruff's syntax target and mypy's strict
target remain Python 3.12. CI checks formatting without rewriting files.

## Verification in every matrix environment

After explicit interpreter selection and the version assertion, the baseline
operations are:

```console
uv sync --locked
uv run --locked pytest --junitxml=reports/pytest.xml
uv build --build-constraint build-constraints.txt --require-build-hashes
```

These operations execute in each verification job; see linked runs for evidence. The build
must use the selected matrix interpreter; do not copy F02's local
`--python 3.12` argument into every matrix job.

Run the complete suite, including the existing distribution and locking tests.
Require a positive executed/passed count with no test failures or collection
errors. Zero tests, an all-skipped suite, a missing test report, or a setup
failure cannot establish acceptance. Record actual counts; the current five
F02 tests are a baseline, not a permanent fixed suite size.

Each environment must verify:

1. Both wheel and sdist are built using the reviewed constraints. The wheel
   build also exercises the contents of the sdist.
2. Each archive is installed into its **own new consumer environment**, outside
   the source checkout, using that job's Python. No editable install or
   `PYTHONPATH` workaround is allowed as artifact evidence.
3. Isolated Python imports `enrama` from the consumer's `site-packages`, not
   repository `src/`. Assert the consumer interpreter version as well.
4. Name/version, Python requirement, MIT declaration/license text, and the
   absence of accidental development runtime dependencies are correct. F03
   does not introduce a CLI entry point.
5. Archive contents follow explicit inclusion rules, synthetic private files
   are excluded, and repeated builds with identical inputs have equal hashes
   **within that environment**. Cross-OS identical hashes are not required.
6. Missing/stale-lock rejection remains tested, and normal verification leaves
   committed inputs unchanged.

F03 reuses F02's distribution/locking checks and adds real subprocess tests for
CI evidence gates. `scripts/ci.py` asserts the interpreter, validates positive
JUnit results, and records both distribution hashes. Consumer interpreter
versions and import metadata are captured in the JUnit reports. No product
features are implemented to satisfy a CI placeholder.

## Permissions and action dependencies

Set the workflow token to **`contents: read`**, with other repository-token
permissions disabled unless independently justified and approved later. Checkouts
must not retain credentials for subsequent test/build commands. Fork PR checks
must work without repository secrets or a write-capable token.

Pin every external action to a reviewed full commit SHA and record the release
it corresponds to for maintainability. Pin the uv binary version separately;
an action SHA alone does not choose the uv version. The implementation uses:

| Action | Release | Full commit SHA |
| --- | --- | --- |
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `astral-sh/setup-uv` | v10.3.2 | `07a047e608db84b3d8c06cd9a7c7dcc9c355c18e` |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |

No uv download cache is enabled, so the recorded runs exercise cold setup.
Development sync retains F02's `uv sync --locked`; explicit build constraints
and hash verification apply to artifact builds and consumer source installs.
The development lock does not freeze editable-build transitive dependencies.
Do not add publishing
credentials, package uploads, deployments, or write-permission workarounds.

## Reports and artifact retention

Retain test reports and built distributions as **GitHub Actions artifacts for
seven days**. Use names that identify OS, Python version, and artifact purpose
so matrix jobs do not overwrite one another. Include the source revision,
actual interpreter/tool versions, and distribution SHA-256 hashes in the run
evidence.

Collect available diagnostics even when tests fail, preserving the original
failure status. Do not invent a success report when setup fails or waive a
missing required report/archive on an otherwise successful job. Failed jobs
need not produce distributions that could not be built. These artifacts are
CI evidence, not a PyPI publication or GitHub release.

## Implementation acceptance and evidence

F03's implementation acceptance requires:

- The workflow on `develop`, with the agreed triggers and all seven jobs.
- An actual current-revision run showing successful quality checks and all six
  verification environments, each with positive test counts and isolated
  wheel/sdist installation evidence.
- Interpreter-selection/version assertions and unchanged locked inputs.
- Reviewed action pins, read-only permissions, fork-safe operation, and the
  agreed cancellation/report-retention behavior.
- Checks showing that a failing quality/test/build command cannot yield a
  green workflow and that other matrix results are still collected.
- Links to implementing commits and actual Actions runs, plus a record of any
  environmental limitations. Configuration inspection alone is not runtime
  evidence for a trigger, operating system, or Python version.

The existing [F02 verification](verification/f02.md) covers local Python 3.12
only. F03's [verification record](verification/f03.md) reports Actions results,
intentional negative checks and remaining trigger limitations separately.
The issue remains open for maintainer acceptance after delivery.

## References

- [uv: GitHub Actions and explicit matrix Python selection](https://docs.astral.sh/uv/guides/integration/github/)
- [uv: isolated builds and hash constraints](https://docs.astral.sh/uv/concepts/projects/build/)
- [GitHub: workflow syntax, events, matrix, permissions, and concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub: immutable action pinning and token security](https://docs.github.com/en/actions/reference/security/secure-use)
