# Safe YAML loader and diagnostics contract

Status: **C02 implemented on `develop`, awaiting maintainer acceptance**, following
the contract and implementation authorization on 2026-10-23 for
[issue #6](https://github.com/Dev-Peter21/enrama/issues/6).
The loader, diagnostics, PyYAML dependency, and tests are implemented. See the
[verification record](verification/c02.md). CLI, generator, and generated JSON
Schema remain separate tasks.

## Purpose, approaches, and boundaries

Load one client configuration safely, validate it with the implemented
[YAML v1 models](configuration.md), and explain expected failures with useful
file/field context. The loader is shared core functionality, independent of
terminal output, Typer, rendering, and the future editor.

| Reviewed approach | Tradeoff | Decision |
| --- | --- | --- |
| Conventional YAML with anchors, aliases, and merges | Supports reuse but adds shared/cyclic structures, expansion concerns, and less direct source locations | Excluded from the MVP |
| Controlled YAML subset with bounded parsing and C01 validation | Keeps each value explicit and diagnostics predictable; some valid general YAML is intentionally unsupported | Accepted |

Use PyYAML's safe parsing facilities with Enrama's own restrictions and scalar
policy. Calling a generic safe-load function alone is not the whole contract:
Enrama must also enforce duplicate keys, resource limits, permitted structures,
source positions, and its explicit scalar rules. No constructor may execute
Python objects or application-specific code supplied by the YAML.

Configuration selection and the client project root remain governed by
[F01](cli-contract.md#configuration-discovery-and-path-resolution): exact
current-directory discovery or an explicit file path; no parent search, guessed
filename, or working-directory change. The directory containing the selected
configuration remains the client root; do not redefine it from asset references.

The loader reads the selected configuration only. It never rewrites it, creates
`dist/` or temporary output, opens referenced images, checks their existence,
resolves their symlinks, fetches URLs, or installs packages. Actual asset checks
belong to G01. Comments are accepted but comment-preserving writes remain editor
work, not a C02 feature.

## Processing order and outcome

1. Read the selected file within the byte limit and decode UTF-8.
2. Check YAML syntax, document count, supported structure, keys/tags, and parser
   resource limits before constructing application data.
3. Construct only supported plain mappings, lists, and scalar data, retaining
   source positions for later diagnostics.
4. Pass that data to C01's `EnramaConfig` validation. Reuse its version, field,
   URL, language, ID, catalog, and lexical asset rules without a second semantic
   implementation.
5. Return the validated model or structured failure information. Never return a
   partial model, silently repair input, or substitute an empty configuration.

Read/encoding/YAML-stage failures stop processing; do not run C01 on partially
parsed data. If C01 is reached, collect independent model errors together under
the diagnostic cap. Expected invalid input must not escape as a raw parser or
Pydantic traceback. Unexpected programming defects must remain distinguishable
from expected validation and I/O failures.

The builder may choose the concrete function signatures and exception/result
classes. The outcome must preserve the validated model on success, or the
failure category, retained diagnostics, total actionable diagnostic count, and
omitted count on expected failure. No terminal printing or process exit belongs
inside the loader API.

## File and YAML input policy

- Accept UTF-8 with or without an initial UTF-8 BOM. The BOM counts toward the
  byte limit. Reject invalid UTF-8; do not fall back to locale encoding, UTF-16,
  or replacement characters.
- Require exactly one nonempty YAML document whose root is a mapping. Reject
  empty/comment-only input, scalar/list/null roots, and multiple documents rather
  than selecting the first or combining them. Ordinary `---`/`...` document
  markers are allowed around the single document.
- Require string mapping keys at every level. Reject duplicate keys after
  decoding their string value: `title` and `"title"` are the same key. Identify
  both occurrences; never implement first-wins or last-wins behavior. Do not
  normalize key casing or spelling to make a key match a C01 field.
- Reject anchors, aliases, and merge keys (`<<`) before application-data
  construction. Detect YAML constructs, not occurrences of `&`, `*`, or `<<`
  inside ordinary string content.
- Reject Python tags, custom tags/constructors, and data types outside the
  supported plain-data subset. No includes, environment interpolation, secret
  expansion, remote references, or object instantiation.
- Block/flow collections, comments, quoted strings, and literal/folded text
  remain usable within the same limits and C01 field constraints.

### Scalar resolution

Scalar interpretation must be explicit and isolated to Enrama's loader, not a
process-wide modification to PyYAML behavior. Without an explicit supported
standard tag, quotes preserve text; C01 still
rejects quoted strings in boolean/integer fields when a real boolean/integer is
required.

The approved behavior is: `true`/`false` are booleans, while plain `on`, `off`,
`yes`, `no`, and date-looking values remain strings. The following concrete
resolution table makes that policy predictable without YAML 1.1 conversions:

| Plain scalar | Constructed data |
| --- | --- |
| `true`, `false` | Boolean |
| `null`, `~`, or an omitted mapping value | Null; C01 decides whether that field permits it |
| Canonical decimal integer, such as `1`, `0`, `-2` | Integer |
| Finite decimal/exponent number, such as `1.0`, `1e2` | Float |
| Other ordinary scalar text, including dates, `on`/`off`/`yes`/`no`, `True`/`False`, leading-zero or non-decimal number spellings | String |

For numeric resolution, use JSON-style number spelling: optional leading minus,
no leading zeros except `0`, optional fractional part requiring digits after the
point, optional exponent with optional sign and required digits. Numeric overflow
must not introduce an infinite/NaN float; report invalid scalar input instead.
Numbers are not converted back into strings to make a C01 text field pass.

Only the standard map, sequence, string, null, boolean, integer, and float data
kinds are supported. Explicit standard tags for these kinds must obey the same
construction constraints; they cannot re-enable `!!bool yes`, non-decimal integer
conversion, timestamps, binary values, sets, or application objects. Directive or
tag syntax must not override Enrama's scalar policy. This table is a construction
clarification of the accepted plain-data approach, not a change to C01's fields.

## Fixed resource limits

| Resource | Maximum accepted value | Counting rule |
| --- | --- | --- |
| Configuration file | **1 MiB = 1,048,576 bytes** | Raw file bytes, including BOM and comments, before UTF-8 decoding |
| Nesting depth | **32 containers** | Root mapping is level 1; each nested mapping/list adds one; scalar nodes do not add a container level |
| YAML nodes | **10,000 nodes** | Each mapping, sequence, scalar key, and scalar value counts once; stream/document markers and comments do not count |
| Returned diagnostics | **20** | First 20 actionable diagnostics in the ordering below; preserve total and omitted counts |

Values exactly at a maximum are accepted by that limit; one byte, container
level, or node above it is rejected. Acceptance by these limits does not bypass
C01's smaller field/list limits.

Bound the actual read, not just a preliminary filesystem size check: a file that
grows after inspection must still be limited. Read at most the limit plus the
extra byte needed to establish overflow. Enforce nesting/node limits while
parsing, before constructing the corresponding Python collections or recursively
validating an unbounded tree. Do not parse the whole document first and inspect
its expanded Python objects afterward.

Exceeding any parsing limit is invalid input, stops loading, and produces an
expected resource-limit diagnostic. There are no MVP flags, YAML settings, or
environment overrides to raise/disable these limits. The diagnostic cap limits
failure output; it is not a substitute for parser resource controls.

## Structured diagnostics

Each retained diagnostic carries these semantics; representation/class names
remain an implementation choice:

| Component | Meaning |
| --- | --- |
| Category | Missing configuration, read failure, invalid encoding, YAML syntax/structure, resource limit, or C01 model validation |
| File | Selected configuration path, safely displayed |
| Field | Structured key/index location, such as `("links", 0, "url")`; empty/root location displays as `$` |
| Position | Line and column together, when reliably known |
| Message | Concise English explanation of the failure |
| Hint | Concrete corrective action appropriate to that category/field |
| Related positions | Other relevant source locations, notably the first occurrence of a duplicate YAML key |

Line and column numbers are **1-based**. List indexes remain **0-based**, as in
`links[0].url`. Use source marks rather than searching the input for a repeated
value or guessing a location from a message.

### Location rules

- A present field's validation error points to its value when possible; a
  duplicate-key error points to the second key and references the first key.
- For a missing field, point to its nearest existing container when available
  and explicitly label that position as the parent, not as the missing token.
- If no reliable position exists, retain the file and field/root without line
  or column. A global C01 error, such as cross-collection ID uniqueness, may
  remain at `$`; do not invent an offending entry location.
- Preserve structured Pydantic field locations. Do not parse English validator
  messages to reconstruct IDs, field paths, or source coordinates.
- Treat framework bookkeeping about a dependent default not being computed as
  secondary when an existing primary field error explains it; show/count
  actionable primary errors rather than telling the user to fix an internal
  default factory. No semantic validation rule is duplicated by this filtering.

### Ordering and cap

Use deterministic source order for diagnostics with source positions. For ties,
use field location and category as stable tie-breakers; integer indexes sort
numerically. Diagnostics without a reliable source position follow positioned
ones and use deterministic field/category order. Preserve deterministic
validator order for any otherwise identical keys.

If 27 actionable diagnostics are available, return the first 20, total count 27,
and omitted count 7. Do not describe truncated output as all errors. The future
terminal presentation includes `Showing 20 of 27 errors.` Do not invent a count
of additional syntax errors after a YAML-stage failure stops analysis.

## Human-readable presentation and exit mapping

The future CLI sends diagnostics to `stderr`; normal results remain on `stdout`.
The loader itself does neither. A representative presentation is:

```text
enrama.yaml:18:10 — links[0].url
Unsupported URL scheme.
Hint: Use https, http, mailto or tel.
```

Without coordinates:

```text
enrama.yaml — $
Entry IDs must be unique across links and socials.
Hint: Give every link and social entry its own stable ID.
```

These are representative English messages, not a byte-for-byte terminal API.
Diagnostics do not include received field values, YAML excerpts, full parser
exception strings, Pydantic `input` values, arbitrary exception context, or
tracebacks for expected failures. Paths and field names are themselves untrusted
text for display: escape control characters rather than letting them alter
terminal output. Quote unusual field keys unambiguously instead of pretending
that every key is a simple dotted identifier.

| Condition | Eventual F01 exit code | Expected response |
| --- | --- | --- |
| Selected configuration missing | `1` | Identify the path; suggest creating it or selecting the correct file |
| Invalid UTF-8, YAML syntax/structure, duplicate keys, unsupported constructs/tags, resource limit, or C01 model error | `1` | Explain the restriction and how to correct the input |
| Permission denial or another operational failure reading existing input | `3` | Identify the path and access failure without dumping raw exception/input content |
| Unexpected implementation defect | `70` | Identify an internal failure; do not disguise it as invalid user YAML |
| Interruption during loading/validation | `130` | Preserve normal interruption semantics; do not swallow it as a validation error |

This maps to the existing [F01 exit policy](cli-contract.md#exit-codes-and-terminal-output).
It implements no CLI or new exit code. Structured diagnostics are internal core
information, not a new public JSON terminal format or stable message wording API.

## Required acceptance cases

These acceptance cases are exercised by C02 unit and installed-consumer tests;
executed counts and environments are recorded in [C02 verification](verification/c02.md).

| Case | Expected outcome |
| --- | --- |
| Both documented YAML v1 examples, including no `site.url` | C01 model and defaults agree with direct validation |
| UTF-8 with/without BOM; invalid UTF-8; UTF-16 bytes | Accept supported encoding only; no decoding fallback |
| Empty/comment-only input; scalar/list/null root; second YAML document | Expected input error; never select/merge documents |
| Block/flow collections, quoted content, literal/folded text and comments | Preserve their plain-data meaning within C01 constraints |
| Duplicate root/nested key, including differently quoted equal strings | Reject; second and first key locations available |
| Non-string/complex mapping key | Reject before constructing invalid Python mapping data |
| Anchor, alias (including recursive reference), merge key, Python/custom/unsupported tag | Reject without executing constructors or expanding references |
| Literal `&`/`*` text in a quoted value | Treat as content, not an anchor/alias token |
| Booleans, quoted booleans/numbers, on/off/yes/no, dates, nulls, decimal/exponent numbers | Apply the resolution table, then C01 strict validation |
| File at/above 1,048,576 bytes, including BOM/comments; growth after size inspection | Bound actual bytes read; reject overflow |
| Depth 32/33 and nodes 10,000/10,001 | Accept at parser limit; reject above it before Python-data construction |
| Unsupported version, required/default/null/unknown fields, invalid or duplicate IDs | Reuse C01 outcomes; retain field/root context honestly |
| Dangerous URL schemes including obfuscation; invalid language/catalog/path values | Reject through C01 without network or asset access |
| Multiple independent model errors; dependent-default bookkeeping | Collect actionable errors, with deterministic order and no misleading secondary diagnostic |
| 20/21/27 actionable model diagnostics | Retain at most 20 and report exact total/omitted counts |
| Missing field, repeated values, global root validation error | Correct parent annotation or honest location omission; no text-search guess |
| Missing file, permission failure, interrupted read, unexpected injected defect | Distinguishable categories preserving F01 mapping |
| Values resembling secrets, malicious display names/control characters | No raw values/excerpts/tracebacks; escaped file/field display |
| Successful and failing calls | No printing, file writes, asset opens, downloads, or partial models |

Parser-limit acceptance can be tested independently of C01: a syntactically
permitted tree at a limit may still have an unknown field or exceed a model list
limit. Such input must fail for its actual C01 reason, not for an off-by-one
parser limit. Every error/output assertion must exercise real loader behavior,
not just compare documented strings or test a framework in isolation.

## Delivery boundary

C02 will introduce only the safe loader, its structured diagnostics/source context,
necessary PyYAML dependency/setup changes, and focused tests. The [implementation plan](superpowers/plans/2026-10-23-c02-loader.md) records
module boundaries and tests supporting the established Python 3.12–3.15 matrix.

C01 models remain the field-policy authority. C03 owns generated JSON Schema;
G01 owns asset I/O; CLI presentation/exit behavior is implemented with the CLI
tasks; generator, themes, editor, package publication, and deployment remain
separate work. No round-trip writer or schema migration is introduced here.

The maintainer authorized implementation on `develop`. Issue #6 remains open
until acceptance; no PyPI publication, release, CLI, or generation is included.

## Python API

```python
from enrama.config import ConfigurationError, load_config, parse_config

config = load_config("clients/shop/enrama.yaml")
# Or validate bytes already supplied by an interface, with no filesystem read:
config = parse_config(
    b"schema_version: 1\n"
    b"site: {title: Shop, description: Shop, language: en}\n"
    b"profile: {name: Shop}\n",
    source="draft.yaml",
)
```

`load_config(path="enrama.yaml")` reads only the selected regular file, using the
caller's cwd for relative paths. It does not change cwd or rebase asset strings;
the containing directory remains the project root for future asset consumers.
`parse_config(content: bytes, *, source="enrama.yaml")` performs the same decoding,
parsing and validation without opening the source label. Both return
`EnramaConfig` or raise `ConfigurationError` for expected input/read failures.
Unexpected defects and `KeyboardInterrupt` propagate.

`ConfigurationError.diagnostics` is a tuple of at most 20 immutable `Diagnostic`
objects. `total_count` and `omitted_count` describe actionable diagnostics before
and after truncation. Each diagnostic exposes `category`, `source` (`Path`),
`location` (key/index tuple), `message`, `hint`, `position` (`SourcePosition` or
`None`), `parent` (missing-field parent annotation), and `related` positions.
The error's `category` is its first retained category. Category strings are
`missing_file`, `read_error`, `invalid_encoding`, `yaml_syntax`, `yaml_structure`,
`resource_limit`, and `model_validation`.

`format_diagnostic(diagnostic)` and `str(error)` return escaped English text;
neither prints. These helpers do not assign exit codes or constitute a CLI.
PyYAML events are bounded before Enrama constructs its plain-data tree; no YAML
resolver/constructor is used and no global SafeLoader table is modified.
