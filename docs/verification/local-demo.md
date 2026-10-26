# Local demo verification

Status: implemented on isolated local branch `codex/enrama-local-demo` from
`c377dab` develop, 2026-10-26. Original checkout preserved during implementation. No formal issue acceptance,
release, PyPI upload or public deployment is inferred. Integration and push to
develop were subsequently authorized; final remote evidence is recorded below.

## Scope and environment

G03 guarded build, U01 CLI, U02 foreground preview, U03/U04 packaged themes/icons,
and a synthetic client example. Existing C01/C02/C03/G01/G02 remain the foundations.
CPython 3.12.15/macOS arm64, uv 0.13.5, Typer 0.27.3, Jinja2 3.1.6 / MarkupSafe 3.0.4.
The existing Python 3.12–3.15/Linux plus macOS/Windows CI target is unchanged.
The first develop run [40364334298](https://github.com/Dev-Peter21/enrama/actions/runs/40364334298)
verified Linux but exposed two Windows-only test assumptions: native backslashes
were used as manifest lookup keys, and a snapshot tried reading the actively
locked guard byte. The snapshot now uses POSIX inventory keys, checks guard
metadata while locked, and compares its bytes again after release. Product code
and the OS lock semantics are unchanged. Final remote evidence is retained with
the exact pushed revision and workflow run; a pending job is not passing evidence.

## Executed behavior and test-first record

- Clean inherited baseline **694 passed**.
- Builder: missing-feature tests first; guarded repeatable outputs, protected
  edited/missing/extra files and directories, malformed/unsafe inventories,
  source preservation, read-only validate, real cross-process exclusion,
  publication rollback, failed rollback/cleanup and unknown workspace handling.
- Two ownership races reproduced before fixes: an unowned staging collision and
  preexisting backup must never be removed/replaced. Another init collision
  regression proved an unowned newly created YAML must survive failed creation.
- CLI/preview: missing features first; actual command help/version/init/validate/
  build and codes1/2/3/70/130; real loopback process/HTTP, busy port before output,
  ownership through service, validate while serving, traversal/config/manifest/
  symlink denial and normal SIGINT0. Preview contrast warning regression failed
  first and passed after reporting the core warnings to stderr.
- Abrupt child process termination releases OS ownership but leaves the transaction
  and recoverable staging intact; the next build refuses manual-recovery state.
- A manifest with over 16 MiB combined payload was accepted before the bounded
  inventory regression; it now fails without replacing output.
- Theme tests: both packaged styles, complete 21-icon controlled catalog, exact
  immutable-upstream provenance hashes and retained ISC/MIT notices; independent
  module import; midpoint contrast regression RED→GREEN. Config/models unchanged.
- Installed wheel, sdist and inherited PyYAML-source consumers execute the actual
  console entry point, init/validate/build, repeatability and failed-input/output
  preservation. POSIX consumers also start installed preview, request the page
  and CSS, test writer contention and stop cleanly. Windows console SIGINT is
  not claimed by that POSIX-specific process probe.
- Plain-static-server root/subpath probes request both CSS and local images,
  independently of production site.url and with no runtime Enrama service.

The full local suite passed **761 tests**, zero failures/errors/skips, including
**67 new cases** beyond the inherited 694: 31 builder, 19 CLI, 3 real preview and 12
theme/resource/contrast cases plus two tracked-example E2E cases. Existing distribution consumers and static-hosting
probes were extended too. Executed locked sync, Ruff lint/format, strict mypy,
schema drift check and a full JUnit run. All three installed consumers completed
the actual CLI workflow and POSIX installed preview successfully.

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests scripts
uv run --locked python scripts/schema.py --check
uv run --locked pytest --junitxml=reports/local-demo/pytest.xml -q
uv build --build-constraint build-constraints.txt --require-build-hashes
```

An independent read-only whole-change review covered c377dab..6742a48. It found
one Important ownership defect and no Critical/Minor findings: cleanup used the
planned inventory as proof of ownership. Four regressions failed first (foreign
index/asset at a planned path, edited staging content and replaced staging root).
The fix records only successfully created/verified files, checks staging identity
and unchanged owned bytes, and preserves uncertain data with the transaction.
All four then passed, as did the complete 761-case suite and quality checks.
No deferred minor remains. No automatic issue acceptance is inferred.

The review's excluded guarantees stay excluded: universal hostile/network
filesystem or power-loss guarantees, automatic recovery/editor/release/deployment.
Remote CI/Windows behavior is judged from actual execution, and the local browser
and pinned-license evidence remain separately recorded rather than claiming the
reviewer repeated them. Final remote revision/CI is recorded after publication.

## Browser evidence

Actual in-app browser sessions at 127.0.0.1:8765 (minimal) and :8766 (bold).
Desktop and mobile screenshots, keyboard focus and actual DOM layout inspected.
Images loaded, native destinations/accessibility names preserved and anchor
heights are at least 44 px (primary rows74–82px). The CSS arrow is decorative geometry
rather than accessible-name text. No JavaScript, remote fonts or remote runtime
resources are required. Reduced-motion CSS is included; no OS preference was changed.

Requested viewport widths 390 and320 were checked (client widths 375/305 where
scrollbars reserve 15 px). Normal demos have scrollWidth==clientWidth. An actual
maximum-length social label at 320 px reproduced overflow (scrollWidth 744 vs305);
after wrapping fixes **both themes** have scrollWidth 305 with no overflowing
anchors. Long profile names, biographies and link titles remain readable without
horizontal scrolling or truncation.

Configured demo contrast ratios (body / primary-button / focus against background):
minimal **11.65 / 9.45 / 8.60**; bold **12.15 / 6.14 / 12.15**. Low-contrast valid
customization selects black/white foregrounds, preserves YAML and warns. Numerical
checks cover midtones too; no guarantee about every untested browser/assistive
technology is inferred from this local pass.

Screenshots and local machine evidence are ignored under
`reports/local-demo/`; source example and guide are tracked. See
[reproduction steps](../local-demo.md).

## Safety and remaining boundaries

Only known invocation-owned temporary paths may be cleaned. Unknown/recoverable
transaction data is preserved; no automatic crash recovery or destructive bypass.
Publication uses staged directory renames with rollback, not a universal atomic
exchange or power-loss durability guarantee. The OS lock coordinates cooperating
processes on a local filesystem; continuous hostile filesystem mutation/network
filesystems are not a general-purpose sandbox claim.

The example uses original MIT geometric artwork and placeholder destinations,
not real client accounts. System font stacks distribute no font files. Lucide
1.61.0 commit c29c276f16590cf017126671535ad8c792be64d8 and Bootstrap Icons v1.13.2
commit afbfcbcb9bea79ea9923fa9ef82ea03d7ee6c01f are vendored with exact hashes and
complete license terms. No editor0.2 or release/deployment work is implied.
