# G03 safe build contract

Status: local-demo implementation design, 2026-10-26. Manual recovery after abrupt
termination is maintainer-approved. The concrete names and reversible choices
below are implementation assumptions under the delegated instruction to continue
to a local demo. They do not close or formally accept G02 or any GitHub issue.

## Pipeline and ownership

`build_site(source='enrama.yaml', *, session=None)` loads C02 configuration,
prepares G01 snapshots, renders G02 HTML, creates a complete staging tree and
publishes only `<selected source parent>/dist`. It returns a BuildResult; core
services do not print or exit. `validate_project` runs input/image checks without
creating output or coordination files. No configurable output/force/watch option.

A ProjectSession provides nonblocking exclusive ownership for one canonical
project root. Its guard covers output inspection, generation, publication and
cleanup. Preview retains the same session for reservation/build/service/shutdown;
other writers fail immediately. A local advisory OS file lock is released on
ordinary exit or process death; a persistent guard file is harmless and is not
unlinked while another process could open it. This is not an adversarial OS
filesystem sandbox or a guarantee for network-mounted filesystems.

## Reserved workspace

Reserve `.enrama/` for `workspace.json`, `guard`, `transaction.json`, `staging`
and `backup`. Require a real directory and recognized versioned workspace marker;
reject unknown existing contents, links/reparse points and nonregular records.
Only a newly created directory may be initialized. Do not adopt unknown data.
Source YAML/images must not come from dist or this workspace; G01 receives both
workspace and exact staging/backup locations as reserved paths. Init ignores
`.enrama/` and `dist/`. Project root ancestors may resolve normally; internal
working/output links are rejected.

The transaction record is created exclusively before staging. Its presence or
orphan stage/backup blocks a later invocation even when the OS lock is free.
There is no automatic crash recovery or stale-data deletion. Diagnostics identify
relative recoverable locations and instruct the user to inspect/move them before
retrying. A marker alone never authorizes recursive deletion of arbitrary data.

## Output manifest

`dist/.enrama-manifest.json` is deterministic UTF-8/LF JSON, format_version 1,
generator name/version and YAML schema version, with sorted relative paths,
byte sizes and SHA-256 digests. It excludes itself. No timestamp, absolute path,
random build ID, YAML content or source filename is published. A recognized older
generator version may be replaced if the manifest format and entire tree verify.
Require index.html; only regular files under the fixed generated namespaces are
allowed. Paths are canonical POSIX paths, no traversal/absolute paths/duplicates,
case aliases, symlinks or special files; expected directories derive from files.
Unexpected empty directories also block replacement. Bound manifest reads and
inventories. Invalid/missing/edited/extra output or an existing empty dist fails
operationally without modifying that output. Integrity is not a cryptographic
signature or authority to delete arbitrary user-selected directories.

## Publication and failure boundaries

Generate index.html as UTF-8 without BOM/LF, copy unchanged G01 bytes, and include
only actually used packaged theme resources and retained third-party notices.
Verify staging and recheck the old output immediately before replacement; manual
changes during generation cause conflict. Rename old dist to the invocation's
backup, then rename staging to dist. Do not claim a universal atomic directory
exchange or power-loss durability. A failed publication before the second rename
restores the previous output when possible; if restoration is impossible retain
all recoverable data and the transaction record and report an operational error.

After the new directory is installed, old-backup cleanup can fail or be
interrupted. Keep the complete new site and any remaining recoverable backup,
retain the transaction record and report failure, not success; do not restore a
partially deleted backup. Before publication failures/interruption preserve the
old site. Cleanup removes only this invocation's known generated paths, never
unknown data, links, inputs or unrecognized old transactions. Successful cleanup
removes staging/backup/transaction; recognized workspace/guard may persist.

Expected input errors map to F01 code1, operational/protection/cleanup conflicts
code3, unexpected defects code70, interruption130. Preserve C02/G01/G02 diagnostic
ownership. BuildError exposes safe English category/message/hint/relative context;
no raw exception dumps or success after a failed cleanup.

## Local demo scope and remaining assumptions

Implement U01 init/validate/build and U02 foreground preview on exact loopback port
8000 (explicit --port 1..65535), reserve before build, manual stop/restart only.
Serve allowlisted generated files through no-follow regular-file reads, no directory
listing, traversal, source files or symlink targets. Help/version work without YAML;
normal preview Ctrl+C returns0, startup/build interruption130. No auto-browser.

U03/U04 share semantic content/metadata. Minimal is a restrained editorial page;
bold uses strong type and solid accent treatments. System font stacks require no
font downloads/distribution. Bundle the C01 Lucide/Bootstrap catalogs from pinned
upstream revisions with licenses. Native links keep visible accessible labels,
focus/tap targets and reduced-motion support. Preserve color configuration while
deriving accessible text/focus colors where custom contrast is insufficient;
report a warning rather than reject C01-valid YAML or silently claim all arbitrary
colors are accessible. Do not mutate YAML. No analytics or remote runtime assets.

A synthetic redistributable Amapola-inspired example exercises both themes and
all CLI commands. The demo stays local; no PyPI, release, public deployment,
push, merge, credentials or formal issue acceptance is authorized by this work.
