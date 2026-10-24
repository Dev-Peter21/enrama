# Local asset resolution and copying contract

Status: **G01 implemented on develop, awaiting maintainer acceptance**, following
the design agreed and implementation authorized on 2026-10-24 for
[issue #8](https://github.com/Dev-Peter21/enrama/issues/8).
The asset preparation/copy API, Pillow dependency and focused tests are
implemented on **`develop`**. See [verification evidence](verification/g01.md).
Package version remains `0.1.0.dev0`; issue #8 stays open for acceptance.

## Intent, approaches, and boundaries

Resolve client-owned image references safely, explain invalid inputs, and supply
verified unchanged bytes to the future static builder. The shared core must be
usable by eventual validate/build commands without depending on a CLI or editor.

| Approach discussed | Tradeoff | Decision |
| --- | --- | --- |
| Validate and copy original bytes | Predictable output, original quality and metadata; users prepare appropriately sized images themselves | Accepted |
| Convert, resize, optimize, or strip metadata | Adds transformation policy, output changes and more implementation scope | Outside the MVP |
| Inspect only signatures/headers | Lower dependency cost, but does not establish that pixels can be decoded | Not sufficient |
| Verify structure and decode with Pillow | Adds a runtime dependency and bounded decoding work; detects decoder-rejected content | Accepted |
| Allow symlinks whose targets remain inside the project | More flexible but makes resolution depend on filesystem links | Not accepted |
| Reject all internal source symlinks | Restrictive and predictable across supported environments | Accepted |

Only `profile.avatar`, `site.favicon`, and `site.og_image` are inputs. Omitted/null
references require no image; do not invent defaults or avatar-to-OG fallbacks.
Do not scan/copy an assets directory recursively. Images may be anywhere allowed
inside the selected client root; an `assets/` source directory is conventional,
not mandatory. Packaged theme CSS, icons and fonts remain separate tasks.

Reuse [C01 lexical path rules](configuration.md#local-image-references) and
[F01 root/output rules](cli-contract.md). [C02](yaml-loader.md) still loads and
validates YAML without opening images. This contract resolves O04; it does not
alter YAML fields, JSON Schema, configuration discovery, or C01/C02 semantics.

## Resolution and filesystem boundary

- The directory containing the selected configuration defines the client root.
  Resolve asset references from that root, never cwd, and do not change cwd.
- Resolve the real client root once. Reject a symlink at the referenced file or
  at any path component **within** that root, even if it points inside. A broken
  symlink is still a symlink. Do not apply this rule to external ancestors above
  the resolved root, such as the operating system's own directory aliases.
- Preserve C01's rejection of absolute/drive/UNC paths, parent traversal, remote
  URLs/data and reserved `dist/` spellings. Do not expand environment variables,
  home references or URL escapes into a different filesystem path. Use C01's
  portable separator interpretation rather than introducing a second path policy.
- Confirm actual containment and a regular file before reading image content.
  Reject directories, FIFOs, sockets, devices and symlink escapes without blocking
  on a special-file read. Recheck relevant boundaries when opening/copying rather
  than treating a prior string check as permanent authorization.
- Sources cannot come from `dist/` or builder staging/backup/coordination areas,
  even when physically inside the project. G03 supplies its reserved working
  locations; G01 must honor them without guessing ownership from filename prefixes.
- Source reads and destination writes must not alias so copying can overwrite an
  original. Copy only inside the builder-authorized staging tree; reject unsafe
  destination components, symlinks and nonregular existing targets.
- Do not fetch assets, run external conversion tools, open URLs or interpret
  client image content as templates/scripts. Runtime work must remain local.

A validated image is one bounded byte snapshot. Format checks, decoding, digest
and eventual copy use **that same snapshot**. Do not validate one read and reopen
an unchecked changed source for copying. A later invocation may see a later
snapshot; a concurrent source edit does not authorize copying unvalidated bytes.
Concrete safe-open mechanics and platform-specific tests belong to implementation;
path checks alone must not be described as a general-purpose filesystem sandbox.

## Supported images and fixed limits

| Role | Accepted formats/extensions | Maximum original bytes |
| --- | --- | --- |
| Avatar | PNG `.png`, JPEG `.jpg`/`.jpeg`, static WebP `.webp` | 5 MiB = 5,242,880 |
| Open Graph | PNG `.png`, JPEG `.jpg`/`.jpeg`, static WebP `.webp` | 5 MiB = 5,242,880 |
| Favicon | Static PNG `.png`, ICO `.ico` | 1 MiB = 1,048,576 |
| All referenced images combined | Unique content snapshots, counted once | 10 MiB = 10,485,760 |

Extensions are compared case-insensitively; output extensions are canonical
lowercase. JPEG aliases are equivalent. An allowed extension must match the
detected format and its field's allowlist. Do not accept a renamed GIF/SVG, an
ICO renamed PNG or another format because a decoder happens to recognize it.
Empty files and files without an accepted matching extension are invalid.

Apply the byte limit during the actual read, not merely to filesystem metadata.
Read at most the role limit plus one byte to establish overflow. Exact maxima
are allowed; one byte above is rejected. Identical bytes referenced more than
once count once toward the total, but **every reference still meets its own
role's size/format/dimension rules**, including when snapshots are reused.

| Decoded resource | Maximum accepted value |
| --- | --- |
| Avatar/Open Graph width and height | Each side at most 8,192 pixels |
| Avatar/Open Graph pixel count | Width × height at most 16,000,000 |
| Favicon PNG width and height | Each side at most 1,024 pixels |
| ICO directory entries | At most 16 actual entries, not merely distinct sizes |
| Each ICO image's width and height | Each side at most 256 pixels |

Dimensions must be positive. All applicable limits apply together; for example,
8,192 × 8,192 fails the 16,000,000-pixel cap. Exact limits pass their respective
check, subject to all other rules. ICO entries are alternative resolutions, not
animation frames; every entry must validate, including duplicate-size entries.
No configurable flag, YAML field or environment variable raises these MVP limits.

## Image validation and unchanged copying

Pillow **13.0.0** is the pinned runtime dependency. PNG/JPEG/WebP capabilities
are required; missing codecs produce an environment failure rather than silently
disabling a supported format. Installed wheel/sdist consumer probes decode and
copy every supported format. The package includes typing; no Pillow stubs or new
build constraints are required for the tested wheel installations. Actual
environments and matrix evidence are recorded in [G01 verification](verification/g01.md).

For each snapshot:

1. Detect the actual allowed image format and compare it with extension/role.
2. Inspect declared dimensions, container entries and animation structure. Enforce
   dimensions/counts as soon as available, before pixel decoding of that image.
3. Verify structure and decode the image content with Pillow. Decoding must fail
   on rejected/truncated data; do not enable permissive truncated-image loading,
   suppress decompression safeguards, repair content or ignore a failed ICO entry.
4. Reject APNG animation containers and animated WebP, including animation
   containers with only one frame. Do not use `n_frames > 1` as the sole test.
   An ICO with several supported resolutions is permitted; validate every entry,
   not only the largest image the default reader selects.
5. Hash and retain the original validated bytes for unchanged copying. Do not
   re-encode, resize, rotate from EXIF, normalize color, strip metadata, or change
   transparency. Decoding is validation, not an output transformation.

An image is accepted according to these checks and the reviewed decoder; this
is not a promise to detect every malformed byte, trailing payload or browser
incompatibility. Original metadata remains in the published copy. Do not claim
sanitization, compression savings, automatic orientation correction or a minimum
visual quality/aspect ratio. No new square-image requirement is introduced.

The Pillow documentation distinguishes
[structure verification from pixel loading](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.verify),
describes [decompression protection](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open),
and notes [ICO's default largest-image loading](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#ico).
The numeric limits and animation policy above are Enrama decisions, not Pillow
library defaults. Implementation must exercise these behaviors on real fixtures.

## Deterministic paths and collision policy

The renderer receives a field-to-public-path mapping, for example:

```text
profile.avatar -> assets/client/<full-sha256>.png
site.og_image  -> assets/client/<full-sha256>.jpg
```

- Compute the full 64-character lowercase SHA-256 of the unchanged content.
  Canonical extensions are `png`, `jpg`, `webp`, `ico`, based on verified format.
- Paths are POSIX-style and relative to the generated site root, without a
  leading slash. G02 constructs HTML/public metadata URLs while preserving any
  `site.url` hosting prefix. Do not emit local absolute paths in generated output.
- Source filenames/directories, field names, input order, timestamps and machine
  details do not influence the generated filename. Equal bytes/format give the
  same path across supported platforms; changed bytes give a content-based name.
- Reuse one copy for matching bytes/format, including different references or
  source files. Hash equality alone is insufficient to authorize reuse: compare
  bytes before treating two snapshots or an existing target as identical.
- Same basename with different content is not a collision: content-derived paths
  differ. Never append order-dependent numeric suffixes or overwrite by basename.
- An existing identical regular staging file can be reused after verifying its
  contents. A conflicting file, directory, link or other target is a protected
  destination conflict. Fail explicitly; do not overwrite it or invent a new name.
- Different bytes claiming the same digest/output path are an explicit asset
  collision, not a successful deduplication. Preserve both inputs and the
  destination; do not silently select a winner, even for this unlikely case.

`assets/client/` is the client-image output namespace. Other generated resources
must not occupy it; G02/U03 coordinate their own namespaces separately.
G01 never writes directly into the published `dist/`. G03 owns staging lifecycle,
manifest integrity, publication, rollback, obsolete-output removal and concurrency.
A copy failure may leave this invocation's partial staging data for G03's safe
cleanup; it never authorizes modification of a previous site or original image.

## Outcomes and structured errors

The core has a read-only validation/preparation operation and an explicit staging
copy operation. Validation creates no files/directories, persistent locks or
published output. Copying requires a successful complete preparation; do not
copy some fields after other fields have failed. No partial success is returned
as a validated asset set. Concrete function/result/exception names and caching
mechanics remain implementation choices; avoid extra abstractions without need.

Diagnostics follow C02's semantics without extending its loader responsibilities:

- Carry an expected failure category, selected YAML path, structured field
  location, affected asset reference when applicable, concise English message,
  and concrete corrective hint. Global total/collision errors may use `$` and
  related fields rather than falsely blaming one reference.
- Use line/column only when reliable source marks are actually supplied. C02's
  current public API returns a model without a source map; G01 must work without
  coordinates and must not reparse/search YAML to invent them or change C02's API
  merely to fabricate more precise locations.
- Escape paths/references/control characters for terminal-safe display. Never
  dump image bytes, metadata, YAML excerpts, raw decoder/OS exception strings or
  tracebacks for expected failures. The core neither prints nor exits.
- For independent references, collect one primary actionable error per field in
  fixed order: `profile.avatar`, `site.favicon`, `site.og_image`. Stop that field's
  dependent checks after failure. The same bad source can identify each affected
  field; deduplicating content must not hide a field-specific failure.
- Report independent global failures after field failures. Do not invent totals
  or duplicate total-limit errors when a source could not be read/validated well
  enough to establish them. Retain at most 20 diagnostics, with honest total and
  omitted counts like C02; three image fields normally produce far fewer.

| Failure | Eventual F01 exit code |
| --- | --- |
| Missing source, forbidden path/symlink/special file, empty image, unsupported/mismatched format, decoder-rejected/truncated image, animation or input byte/pixel/entry limit | `1` |
| Different source bytes claiming the same digest/output path | `1` |
| Permission denial, operational source read failure, staging access/write failure, unsafe or conflicting staging destination | `3` |
| Unexpected programming defect or missing required decoder capability in the installed environment | `70` |
| Interruption during validation/copy | `130` |

Mixed expected validation/operational failures produce eventual code `3`; otherwise
invalid input produces `1`. Do not choose the code from the first sorted message
alone. Unexpected defects and interrupts remain distinct; never catch every
exception and relabel it as a broken user image. In particular, a decoder rejecting
already-read bytes is an image failure even if its exception class is `OSError`;
a filesystem read failing before the snapshot exists is operational instead.
These are internal structured outcomes, not a new public JSON CLI format or
byte-stable English message API. The future CLI implements process exit mapping.

Representative presentation without invented coordinates:

```text
enrama.yaml — profile.avatar
Asset: assets/portrait.png
The image exceeds the 16,000,000-pixel limit.
Hint: Export a smaller image and update the referenced file.
```

## Implementation acceptance

These are acceptance requirements; executed checks and remaining limits are
recorded in [G01 verification](verification/g01.md):

| Case | Required result |
| --- | --- |
| All optional images omitted/null | Empty mapping, no image reads or writes |
| Valid PNG/JPEG/WebP by role; valid PNG/ICO favicon | Validate and copy exact original bytes |
| Mixed-case extensions; `.jpg`/`.jpeg` | Accept matching format and produce canonical extension |
| Wrong extension, renamed unsupported image, wrong role | Input failure, no publication |
| Empty, truncated, corrupt or decoder-rejected image | Actionable field failure; no permissive repair |
| Static PNG/WebP vs APNG/animated WebP, including one-frame animation container | Accept static only |
| Multi-resolution ICO, duplicate-size entry, one corrupt inner image | Check every actual entry; reject if any entry fails |
| Exactly/one above each byte/total/pixel/side/ICO-entry limit | Enforce exact boundaries before excess reading/decoding |
| Shared source under avatar and favicon | Apply each role's restrictions before reuse |
| Distinct files with equal bytes | One output copy and one total-budget charge |
| Same basename/different bytes; changed image bytes | Distinct deterministic content paths |
| Forced digest collision with different bytes | Explicit input collision; no winner or overwrite |
| Invocation from unrelated cwd or selected alternate config | Same client-root resolution and public paths |
| Traversal, absolute/drive/UNC, remote/data or reserved output/working source | Reject without escaping project protections |
| File/directory symlink, in-root symlink, escape, broken symlink | Reject every internal symlink and preserve its target |
| Directory, FIFO, socket/device where available | Reject without blocking/special-file content reads |
| Source changes between validation and copy | Copy only validated snapshot bytes, never unchecked replacement |
| Existing identical staging file vs different file/link/directory | Verified reuse vs protected destination failure |
| Unreadable source, unwritable staging, interrupted operation | Correct failure class; originals/previous output preserved |
| Independent field failures, shared bad source, total-only failure, mixed I/O/input failures | Stable contextual diagnostics, honest counts and correct exit class |
| Control characters and decoder/OS payloads | Safe English diagnostics without raw content/exception disclosure |
| Repeat inputs across clean runs/platforms | Identical bytes, names and mapping; no volatile output metadata |
| Validation/copy success and failure | No printing/exiting; validation has no writes; copying is confined to authorized staging |
| Installed wheel and sdist, all six CI verification environments | Used Pillow codecs/module/data available, positive test counts and unchanged scope |

Use synthetic redistributable fixtures, including real decode failures, rather
than tests that merely assert documented strings. Tests must demonstrate byte
preservation, bounds and rejected side effects. Future implementation records
exact source/dependency versions, positive counts and installed-distribution
results under the [testing strategy](testing.md).

## Documentation clarifications

To make the agreed behavior implementable, this document fixes case-insensitive
input extensions, actual ICO-entry counting, per-role revalidation before reuse,
field ordering and the existing 20-diagnostic convention. It classifies a missing
required decoder as an internal environment defect rather than bad client input,
and separates input digest collisions from protected staging conflicts. These
are author clarifications supporting the approved policies, not additional
features or an implementation authorization.

## Python API

```python
from pathlib import Path
from enrama.config import load_config
from enrama.core import AssetError, prepare_assets, copy_assets

source = Path("clients/shop/enrama.yaml")
config = load_config(source)  # YAML only; this does not open images.
prepared = prepare_assets(config, source=source, reserved_paths=(Path("work"),))
# Validation above writes nothing and returns original immutable byte snapshots.
paths = prepared.mapping  # e.g. {"profile.avatar": "assets/client/<sha256>.png"}
# Only an authorized caller owns/creates its staging directory; this example
# deliberately does not create a builder or publish anything.
# Once clients/shop/work already exists as that caller's real staging directory:
copy_assets(prepared, "work")
```

`prepare_assets(config, *, source="enrama.yaml", reserved_paths=())` returns
`PreparedAssets` or raises `AssetError` for expected input/operational failures.
It does not load YAML again. `source` supplies the selected configuration path
and root, not a request to read that file. Relative reserved working paths resolve
against the canonical client root; exclude all of them from source selection.

`PreparedAssets` contains `root`, `source`, canonical `reserved_paths`, immutable
`assets` (original `data` bytes and `public_path`) and immutable `bindings`
(structured `location`, original `reference`, `public_path`). `mapping` returns
a fresh dictionary keyed by dotted field name; modifying it cannot mutate the
snapshots. These are in-memory records from preparation, not a serialized input
format or authorization token for arbitrary Python callers.

`copy_assets(prepared, staging)` requires an **existing real directory exactly
listed among prepared.reserved_paths**, inside the client root and outside dist.
Relative staging paths resolve against that root. Only namespace subdirectories
are created. It checks prepared path/content integrity before writes, uses
exclusive file creation, and reads/compares existing targets without truncation.
Changed/deleted sources after preparation do not change the bytes copied.
Caller-owned staging and partial residue remain the caller's responsibility.

`AssetError.diagnostics` retains at most twenty immutable `AssetDiagnostic`
records, with `total_count`, `omitted_count` and `kind` (`invalid_input` or
`operational`). Each record carries `category`, selected YAML `source`, structured
`location`, optional `reference`, English `message` and `hint`. Coordinates are
not invented. `str(error)` safely formats these diagnostics without printing.
`AssetEnvironmentError`, unexpected defects and `KeyboardInterrupt` propagate;
the future CLI maps those outcomes to F01 codes. G01 assigns no process exit.

The implementation uses anchored no-follow directory descriptors where supported
(POSIX). The Windows fallback checks internal reparse points, regular-file types
and file/directory identities around full-path operations. These checks cover
ordinary path substitution and static unsafe paths; this API is not an OS sandbox
against an adversary concurrently rewriting the filesystem. G03 must provide
its own output-operation coordination. Image decoders/settings and trusted
Python callers remain explicit boundaries.

## Delivery boundary

G01 delivers asset validation/preparation, snapshots, protected staging copying,
Pillow runtime packaging and focused unit/installed-consumer tests. C01/C02 and
the checked schema remain unchanged. No renderer, builder lifecycle/manifest/
cleanup/locking/publication, CLI, image transformation, theme/icon/editor, package
release, PyPI upload or client deployment is delivered. Source implementation
is on `develop`; closure/Done requires maintainer acceptance of the evidence.
