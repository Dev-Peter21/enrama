# Enrama Local Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Execute natively with TDD and one independent whole-change review. Steps use checkboxes.

**Goal:** Deliver a locally served, installable Enrama demo from existing develop foundations, without publication or modifying Peter's original checkout.

**Architecture:** G03 coordinates existing C02/G01/G02 through a guarded, manifest-verified staging/backup transaction. CLI and foreground preview call the same core. Two packaged visual themes and controlled licensed icons extend shared rendering; tests and installed consumers verify the complete workflow.

**Tech Stack:** Python3.12+, uv, existing Pydantic/PyYAML/Pillow/Jinja2, Typer, stdlib filesystem/HTTP, pytest/Ruff/mypy, browser QA.

**Spec:** [G03/demo contract](../../builder.md), [F01](../../cli-contract.md), [G02](../../rendering.md), [theme requirements](../../themes.md). The delegated continue-to-demo instruction settles reversible assumptions without routine checkpoints; no formal acceptance of G02 is inferred.

## Global Constraints

- Isolated managed worktree codex/enrama-local-demo from c377dab develop; original checkout preserved. No push/merge/GitHub mutation/PyPI/release/public deployment.
- Only fixed project dist output; .enrama workspace; deterministic manifest; manual interrupted-operation recovery; no destruction of unrecognized/recoverable data.
- Reuse loader/assets/renderer. English docs. No editor0.2, tracking, accounts or managed hosting.
- Test real preservation, stale cleanup, contention, fault paths, port reservation, no-follow serving and installed package content. Do not claim a remote matrix without running it.

## Review Focus

- Manual edits or unknown stage/backup files must survive cleanup/retry, including publication rollback failure.
- Guard inode identity and cross-process contention must cover preview's complete lifetime; validate must remain read-only.
- Output traversal/case aliases/symlink/special files and malformed manifests cannot authorize deletion or serving.
- Packaging must include actual CLI/theme/icon/license resources and installed init/build/preview must work away from checkout.
- Custom colors/long multilingual labels, keyboard and reduced motion must remain readable and responsive.

## Task 1: G03 guarded builder

**Files:** Create core/_build_errors.py, _manifest.py, _project.py, builder.py; tests/unit/test_builder.py. Update core exports and explicit distribution inventories.
**Interfaces:** ProjectSession(source) context; validate_project(source)->EnramaConfig; build_site(source,*,session=None)->BuildResult(output:Path,files:tuple[str,...],warnings:tuple[str,...]); BuildError(kind,category,message,hint).
- [x] Write failing tests for first/repeated builds, deterministic output/manifest, stale removal, config/root selection, output edits/missing/extra/empty directories/links/special entries, invalid manifest paths, workspace conflicts/incomplete transactions, cross-process contention, validate no writes, rollback and cleanup preservation.
- [x] Observe missing API failures, then implement manifest validation, safe workspace/OS guard, staging/publish/rollback/known-file cleanup and structured failures. Preserve existing services.
- [x] Run focused tests/quality and full regression suite; commit G03 independently with docs.

## Task 2: U01/U02 CLI and preview

**Files:** Create cli.py, __main__.py, project.py, preview.py; tests/unit/test_cli.py and tests/integration/test_preview.py. Add used Typer/lock/entrypoint and archive inventory expectations.
**Interfaces:** enrama init DEST; validate/build/preview [--config PATH], preview[--port PORT], root help/version. Preview uses retained ProjectSession and exact bound loopback socket before build.
- [x] Write failing CLI tests for success/help/version/errorcodes/init conflicts/no partial destruction/readonly validate and real HTTP/process tests for port busy, guard contention, shutdown/restart and traversal/symlink denial.
- [x] Implement Typer commands, starter files and source-safe HTTP allowlist; use no backend or auto/watch/browser operation.
- [x] Run focused tests/quality/full suite and isolated consumer CLI; commit independently.

## Task 3: U03/U04 packaged presentation

**Files:** Extend renderer/base; create themes.py, packaged minimal/bold CSS, controlled icons/licenses; tests/unit/test_themes.py; packaging inventories.
- [x] Write failing tests for both styles, stable content/metadata, complete controlled icons, local hashed CSS/notices, contrast fallback/warnings, disabled/empty/long content and installed resources.
- [x] Apply Frontend Design and UX Quality: editorial minimal/strong bold, local system fonts, licensed pinned icon catalogs, visible focus, 44px targets and reduced-motion treatment. No remote assets.
- [x] Run semantic/contrast/responsive/browser checks, screenshots and packaging tests; commit independently.

## Task 4: Example, installed E2E and delivery

**Files:** examples/demo assets/config, docs/local-demo.md, docs/verification/local-demo.md, README/status/changelog; extend distribution CLI E2E and safety regressions.
- [x] Verify from built wheel/sdist outside checkout: init/edit/validate/build/preview; real HTTP pages/CSS/images and invalid input/incomplete operation preservation. Run lint/format/types/schema/full suite/constrained archives.
- [x] Perform one independent whole-change review, fix important findings with RED→GREEN and green suite. No new external publication.
- [x] Start demo preview on loopback, record URL/repro commands/screenshots/commits and real remaining limits. Preserve worktree and original checkout.


## Authorized scope update

On2026-10-26, Peter additionally authorized integration of this delivery and the
single examples/demo into develop, push to origin, required checks/review and a
PR only if repository protections require it. No force push, overwriting user
work, additional implementer/worktree, release, PyPI or public deployment.
The parent owns reminders; do not create duplicate automations. This supersedes
only the earlier no-merge/push boundary for this delivery. Verify the exact final
remote revision and CI; keep the same worktree and preserve unrelated work.
