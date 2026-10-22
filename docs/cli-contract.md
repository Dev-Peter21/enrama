# CLI and filesystem contract

Status: **accepted design for the 0.1 MVP**, agreed on 2026-10-22 for
[F01 / issue #2](https://github.com/Dev-Peter21/enrama/issues/2).
This document specifies future behavior. No CLI, generator, preview server,
ownership manifest, or locking implementation is delivered by F01.

## Command surface

```text
enrama init DESTINATION
enrama validate [--config PATH]
enrama build [--config PATH]
enrama preview [--config PATH] [--port PORT]
```

Each command supports `--help`. Root-level `enrama --help` describes the commands;
`enrama --version` reports the installed package version. Help and version return
`0` without requiring configuration or modifying the filesystem. Invoking
`enrama` without a command displays root help and returns `0`.

Options shown above belong after the subcommand. Unknown commands, unsupported
options, missing required arguments, and invalid option values return `2`.
Argument parsing precedes configuration validation and filesystem writes.

The MVP has no `--output`, `--force`, `clean` command, `--host`, watch/reload
option, or automatic browser-opening option. These are not implicit aliases.

## Configuration discovery and path resolution

- Without `--config`, look for exactly `enrama.yaml` in the current working
  directory. Do not search parent directories or silently select another file.
- `--config PATH` selects a YAML file, not a directory. Resolve a relative PATH
  against the current working directory; an absolute PATH is also supported.
- The directory containing the selected configuration is the client project root.
  Resolve local asset references against that root, not the caller's working
  directory. Configuration loading does not change the process working directory.
- A missing configuration file or invalid configuration returns `1`. A file that
  exists but cannot be read because of permissions or another I/O failure returns `3`.
- The published output is always `<project root>/dist/`. There is no configurable
  output location in the MVP, including through YAML or environment overrides.
- YAML field/default rules, allowed asset formats, and URL policies remain the
  responsibility of M1 and the asset tasks. They cannot override these path rules.

For example, running `enrama build --config clients/shop/enrama.yaml` from a
workspace uses `clients/shop/` as the project root and writes
`clients/shop/dist/`, regardless of the caller's location.

## Init

`enrama init DESTINATION` creates a new client directory containing
`enrama.yaml`, an `assets/` directory, and a client `.gitignore` that excludes
generated output. The starter configuration must validate using the eventual
version-1 model; its detailed fields and sample assets belong to later tasks.

DESTINATION is required and is resolved against the working directory if relative.
Its parent must already exist and be a writable directory. A missing/unusable
parent is an operational error (`3`).

Any existing destination is rejected with `3`, including an empty directory,
a file, or a symbolic link. There is no prompt, merge, overwrite, or force mode.
Init never creates `dist/` or initializes a Git repository automatically.

If creation fails or is interrupted, preserve all pre-existing content. Remove
only partial files/directories created by this invocation when safe; report any
temporary residue that could not be removed. Do not recursively delete an
existing destination as a recovery action.

## Validate

`enrama validate` loads and validates the selected configuration and referenced
local assets. It performs no rendering or generation and does not create or
modify project files, `dist/`, an ownership manifest, or persistent lock files.

Report malformed YAML with file/location context when available. Model errors
identify the field, such as `links[0].url`, and explain the expected correction.
Missing assets and invalid configuration return `1`; filesystem access failures
return `3`. Validate can run while preview is serving, because it does not write
the output. It does not certify that a later build will have write permission.

## Build ownership and overwrite rules

`enrama build` validates its input before publishing output. An absent `dist/`
is created only as part of a successful build. A failed first build must not
leave a partial published site at that path.

An existing `dist/` can be replaced only when it is a recognized, intact Enrama
output. An internal ownership manifest records the generated file inventory
and integrity information sufficient to detect manual edits.

The manifest is generated metadata, not user configuration. Its serialization
and implementation mechanism are internal; future implementation must validate
it before using it to authorize replacement. A marker's mere presence is not
permission to delete arbitrary contents.

Before replacing an existing output, verify all of the following:

1. `dist/` is a real directory in the selected project, not a file or symlink.
2. Its ownership manifest is recognized and valid.
3. Every path in the inventory is relative, normalized, and contained in `dist/`.
4. Generated files match their recorded integrity information; missing or
   manually changed generated files are treated as a modified output.
5. No unrecognized files are present. No symlink is present in the output tree
   or in the output path components within the project.

Failure of these checks returns `3` and leaves the existing output untouched.
This includes an existing empty `dist/` with no ownership manifest. Explain the
conflict so the user can inspect and deliberately move or remove that directory
outside Enrama; the CLI does not offer a destructive bypass.

Configuration and source assets must never be taken from `dist/` or temporary
build/backup locations, even if they are otherwise inside the project. Treat
such references as invalid input (`1`): replacing output must not destroy inputs.
Reject source asset traversal and symlink escapes under the configuration policy.

## Staging, cleanup, and failure preservation

Generate and verify the next complete site in a temporary working directory
before replacing the published output. Transient staging/backup/coordination
paths are internal implementation details, not alternative output destinations.
They must not overwrite unrelated paths or be copied into the published site.

Recheck the output protections before replacement. If validation or generation
fails, or the operation is interrupted before publication, preserve the previous
valid `dist/`. A reported filesystem publication failure must preserve or restore
the previous valid output rather than leave a mixture of old and new files.
Do not claim successful publication until replacement and required cleanup finish.

A successful build contains only the newly generated site and its ownership
metadata. This removes obsolete generated files, including images no longer
referenced by the configuration. Cleanup never reaches the YAML, original assets,
project root, or any path outside the allowed output/transient working locations.

Release coordination resources and safely remove this invocation's temporary
files on success, failure, and normal interruption. Never delete unknown staging
or backup directories just because their names resemble Enrama artifacts.
If safe recovery/cleanup is impossible, preserve recoverable data and report the
remaining location as an operational error (`3`). Abrupt process termination or
power loss must not be described as a successful build; crash recovery mechanics
belong to the builder design, not to an assumed universal atomic-rename guarantee.

For the same supported inputs and generator version, generated metadata must not
introduce timestamps, absolute machine paths, secrets, or random content that
break repeatability or disclose local information.

## Concurrent operations

Only one operation that can modify the output may be active for a given project.
The guard must cover validation of output ownership, generation, publication,
and cleanup; two processes must not both decide they own the same destination.

Preview retains that exclusive ownership for its complete startup/service/shutdown
lifecycle. A second build or preview for the same project fails with `3` instead
of waiting indefinitely or replacing files being served. Init protects its new
destination against concurrent creation. Different client projects are independent.

The implementation may select an appropriate coordination mechanism later; it
must release ownership on ordinary failures and interruption. User editing of
source configuration/assets is allowed while preview runs, but those edits do
not trigger a build. Manual output edits are detected by the next build's checks.

## Manual preview lifecycle

`enrama preview` runs in the foreground and follows this sequence:

1. Parse arguments and resolve the project configuration path.
2. Acquire the project's exclusive output ownership.
3. Check and reserve the exact address `127.0.0.1:PORT` before modifying `dist/`.
4. Run the same validation/build and overwrite protections as `enrama build`.
5. Serve only the successfully published `dist/` and print its local URL.
6. On normal shutdown, stop the server, close sockets, release ownership, and
   retain the generated `dist/`.

The default port is `8000`. `--port PORT` accepts an integer from `1` through
`65535`; `0`, non-integers, and values outside this range return `2`. There is
no silent fallback to another port and no network-interface override in the MVP.
An occupied port returns `3` without modifying `dist/`.

A startup/build failure releases the reserved port and exclusive ownership and
returns the corresponding error code. The previous site is not served as though
the requested new build had succeeded. A server failure during service returns
`3` for an operational failure or `70` for an unexpected internal failure.

Preview does not watch files, rebuild on requests, reload the browser, launch a
browser, or run in the background. To see source changes, stop it with `Ctrl+C`,
run `enrama preview` again, and refresh the browser. A build from another process
is rejected while preview remains active.

Only `dist/` is an HTTP document root. Requests must not expose configuration,
source assets, parent directories, or external files through path traversal or
symlinks. Preview is a local development tool, not a production hosting service.

## Exit codes and terminal output

| Code | Meaning | Examples |
| --- | --- | --- |
| `0` | Success or normal end of an active preview service | Validation/build succeeded; help; `Ctrl+C` while serving |
| `1` | Missing or invalid project input | Missing YAML, invalid schema/field, missing asset, unsafe source reference |
| `2` | Invalid CLI invocation | Unknown command/option, missing destination, invalid port |
| `3` | Operational or protected-filesystem failure | Permissions, occupied port/project, existing init destination, protected/modified output |
| `70` | Unexpected internal error | An unhandled implementation defect rather than an expected validation/I/O error |
| `130` | Interruption before ordinary completion | `Ctrl+C` during init, validation, build, or preview preparation |

The `Ctrl+C` exception for preview applies only once it is serving successfully.
Interrupting its initial build returns `130`; stopping the active service normally
returns `0`. Release sockets/ownership and preserve source/previous valid output
in either case. Failures must not print a success message or return `0`.

Normal results, help, version, and the preview URL go to `stdout`. Diagnostics go
to `stderr`, identify the file/field/path/port involved, and suggest a corrective
action. Expected user errors do not display a Python traceback. Unexpected errors
are identified as internal failures and return `70`; diagnostic wording is not
a machine-readable API. JSON output and exit-code changes require a later contract
decision rather than an undocumented shortcut.

## Acceptance examples

These are specification scenarios for later tests, not commands executed against
an implemented Enrama package. Unless stated otherwise, input is valid, writable
parents exist, required resources are free, and any existing output is intact
and owned by Enrama.

| Scenario / invocation | Expected result | Code |
| --- | --- | --- |
| `enrama init new-client` with an absent destination | Create starter YAML, assets directory, and ignore file; no `dist/` | `0` |
| `enrama init existing-client` with an existing directory, even empty | Preserve destination and report conflict | `3` |
| `enrama init existing-file` or a symlink destination | Preserve destination; reject unsafe/existing path | `3` |
| `enrama init` | Explain the missing destination; no writes | `2` |
| Init with a missing or unwritable parent | Explain the parent error; preserve existing content | `3` |
| `enrama validate` in a valid client root | Validate YAML/assets without modifying files | `0` |
| Validate from a child directory with YAML only in its parent | Report missing local YAML; do not search upward | `1` |
| `enrama validate --config clients/shop/enrama.yaml` | Resolve assets against `clients/shop/`, regardless of caller directory | `0` |
| Validate with missing YAML, malformed YAML, invalid fields, or a missing asset | Actionable file/field diagnostics; no writes | `1` |
| Validate with an unreadable existing YAML or asset | Explain filesystem access failure; no writes | `3` |
| `enrama build` with absent `dist/` | Publish a complete site only after successful generation | `0` |
| Build with intact owned output and a removed image reference | Replace site and remove the obsolete generated image | `0` |
| Build with existing empty/unrecognized `dist/` | Refuse replacement without deleting contents | `3` |
| Build with a manually edited or extra output file | Refuse replacement and preserve the modification | `3` |
| Build with a symlinked `dist/` or symlink within its tree | Reject output; leave the link and its target untouched | `3` |
| Build with a source reference into `dist/` or outside the allowed project boundary | Reject invalid input without publishing | `1` |
| Build with invalid YAML and a previous valid `dist/` | Preserve the previous site | `1` |
| Build with a publication I/O failure | Preserve/restore the previous site and explain failure | `3` |
| Build with an unexpected renderer defect | Preserve previous output; identify an internal error | `70` |
| `enrama build --output other` or `enrama build --force` | Reject unsupported option; no writes | `2` |
| `enrama preview` | Reserve loopback port 8000, build, serve, and retain output on normal shutdown | `0` on normal shutdown |
| `enrama preview --config clients/shop/enrama.yaml --port 8001` | Use that project's `dist/` and exact loopback port | `0` on normal shutdown |
| Preview with port 8000 already occupied | Reject before output changes; do not select a different port | `3` |
| `enrama preview --port 0`, `--port 65536`, or `--port abc` | Reject invalid port before configuration/build work | `2` |
| Preview with a validation or protected-output failure | Release reserved port/ownership; do not start serving | `1` or `3`, matching the cause |
| Edit YAML/assets while preview serves | Keep the current generated page until stop/restart; no automatic build | Service remains active |
| Run another build/preview for the same active project | Reject the conflicting operation; keep the running service/site intact | `3` for the new operation |
| `Ctrl+C` while preview is serving | Stop cleanly, free the port/ownership, retain `dist/` | `0` |
| `Ctrl+C` during init, validate, build, or preview startup | Stop, release resources, preserve pre-existing content | `130` |
| `enrama --help`, `enrama --version`, or command `--help` without YAML | Print requested information; no project writes | `0` |

## Delivery boundary

F01 delivers this accepted specification and its documentation links. Packaging,
model/loader behavior, build/manifest implementation, concurrency mechanics,
CLI commands, server code, and executable tests remain their existing roadmap
tasks. The scenarios above define expected behavior for those tasks; they are
not evidence of implemented functionality or passing product tests.
