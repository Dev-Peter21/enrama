# JSON Schema and VS Code contract

Status: **accepted C03 design for the 0.1 MVP**, agreed on 2026-10-23 for
[issue #7](https://github.com/Dev-Peter21/enrama/issues/7).
This change delivers documentation only. No JSON Schema artifact, generation
script, dependency, editor settings file, or executable test is created here.
Future implementation must target **`develop`**, after separate authorization.

## Purpose and chosen approach

Give client configuration authors completion, hover help, and structural
validation in VS Code using a generated JSON Schema. The implemented
[C01 models](configuration.md) remain the field-policy source of truth; the
[C02 loader](yaml-loader.md) remains the complete configuration input boundary.
An editor reporting no problems does not establish that Enrama accepts the file.

| Approach discussed | Tradeoff | Decision |
| --- | --- | --- |
| Local generated schema copy in each client repository | Works offline and changes only through a deliberate client update; requires copying the matching artifact | Accepted for the MVP |
| GitHub schema URL pinned to a commit | Avoids a local copy but needs an initial download and editor cache/network handling | Not the default client workflow |
| Hand-maintained schema or automatic latest-version synchronization | Introduces a second field contract or changes client behavior outside a reviewed update | Excluded |

The maintainer accepted structural editor assistance, a local copy per client,
and manual schema/tool updates committed together. This is tooling for editing
YAML, not the local visual editor planned for 0.2.

## Generation and artifact

Future C03 implementation must:

- Derive the schema from `EnramaConfig` using Pydantic's **validation** mode,
  not its serialization representation or a parallel handwritten field model.
- Use **JSON Schema Draft 2020-12**, declaring that dialect with `$schema` in the
  JSON artifact. That keyword identifies the JSON Schema dialect; it does not
  replace YAML's `schema_version` or select an Enrama package version.
- Generate one checked-in artifact at **`schemas/enrama-v1.schema.json`** in the
  Enrama repository. The same relative path is used for the copied client file.
  These are intended paths; the artifact does not exist yet.
- Produce deterministic UTF-8 output from the reviewed models and locked tooling.
  Regeneration must not introduce current timestamps, machine paths, or a live
  Git HEAD value that changes merely because the artifact is committed.
- Keep definitions/references self-contained so loading the local schema does not
  require downloading Enrama schema fragments. Standard dialect identifiers are
  not hosted Enrama application services.
- Carry the structural constraints expressed by the models: object/field types,
  required/optional/nullable fields, forbidden extra keys, list limits, declared
  string constraints, catalog/theme choices, and the supported version value.
  Expose model-derived titles, descriptions and defaults where available for the
  editor. Descriptions may explain rules that JSON Schema cannot enforce.
- Treat defaults as information/completion suggestions, not an instruction to
  rewrite or populate the client's YAML. Runtime defaults still belong to C01;
  platform-dependent social labels must not acquire a fabricated constant default.

No custom implementation of URL, language, ID uniqueness, or parser policy may
be added as a second validation engine merely to make the editor look complete.
Documentation metadata must not silently change C01 validation behavior.

## Structural assistance and runtime authority

| Concern | JSON Schema/editor role | Authoritative check |
| --- | --- | --- |
| Types, required fields, nullability, unknown keys, declared lengths/list limits and enums | Reflect model-derived structural constraints | C01/C02 still validate input |
| Global ID uniqueness across links and socials | Explain the rule; no claim of equivalent enforcement | C01 |
| Full URL, language registry and lexical asset-path rules | Explain field expectations; arbitrary Python validators are not automatically reproduced | C01 |
| YAML byte/depth/node limits, unsupported tags/anchors/aliases/merges and decoding | No guarantee from JSON Schema | C02 |
| Actual asset files, rendering and generated output | Outside C03 | Later asset/generator tasks |

Structural agreement does not mean every raw YAML input has identical outcomes.
For example, C01 trims some text before checking lengths, whereas a schema
consumer may apply string lengths to the original text. JSON Schema also does
not distinguish every Python strict-type or YAML scalar spelling decision.
The editor can therefore miss runtime errors or flag a value Enrama accepts.
Document such boundaries rather than weakening C01/C02 or duplicating them.

## Versioning and provenance

Keep these identities separate:

| Identity | Meaning |
| --- | --- |
| `schema_version: 1` in YAML | Configuration compatibility contract |
| `enrama-v1.schema.json` filename | Stable artifact name for that contract family |
| Exact Enrama package version | Generator/models release from which the schema was produced |
| Full Git commit for development snapshots | Exact source/artifact revision when `0.1.0.dev0` alone is ambiguous |

A package version change does not automatically change `schema_version` or the
v1 filename. Compatible changes can produce a newer v1 artifact; incompatible
configuration changes require an explicit version/migration decision first,
under the [C01 compatibility policy](configuration.md#compatibility-and-delivery-boundaries).
Do not infer that every generator accepting schema version 1 knows later fields
or catalog entries. Match the artifact to the exact generator revision in use.

The MVP introduces no independent semantic-version counter for the schema and
no mutable latest-schema endpoint. Immutable repository revisions distinguish
artifact snapshots. Record the chosen Enrama version and source revision in the
client README without editing the generated JSON. For current development
snapshots, record the full commit; `develop` or `0.1.0.dev0` alone is insufficient.
Future public release versions must already exist before instructions use them.
No release or PyPI distribution is created by this design.

## Manual client update workflow

The schema is a client-owned tooling copy, tracked in the client's Git repository
alongside `.vscode/settings.json` and its README provenance. It does not belong
in generated `dist/` or become a required runtime dependency of the published site.

1. Select an exact Enrama version/revision. Review relevant contract/changelog
   changes and pin the version/revision used by the client's local/CI workflow.
2. Obtain `schemas/enrama-v1.schema.json` from that exact source revision, after
   the artifact exists. Copy it unchanged to the client at the same relative path.
   Do not copy a floating `develop`/latest artifact into an older client workflow.
3. Record/update the exact Enrama version and source commit in the client README.
   Update schema association patterns only if client filenames/layout changed.
4. Validate the client YAML with the **same Enrama revision** using its supported
   API or, once available, CLI. Inspect editor completion/diagnostics separately;
   a clean Problems panel is not complete validation evidence.
5. Commit the schema, generator version reference, README provenance and any
   necessary settings/YAML changes **together in the same client commit**.

This is a deliberate manual update. C03 adds no updater, notification service,
background network synchronization, YAML migration, client rewrite, or automatic
schema installation by `init`. A schema copy alone does not upgrade Enrama.
Do not edit a generated schema to make invalid client data pass. If an update
fails validation, fix the configuration or restore the matching prior tool/schema
pair before accepting it. Existing client/site files are not rewritten by C03.

## VS Code configuration

Use **YAML by Red Hat**, extension identifier `redhat.vscode-yaml`. Open the
client folder as the VS Code workspace. The documented default is a single-folder
workspace with the copied schema at `schemas/enrama-v1.schema.json`.

The following is the accepted configuration example for the client's
`.vscode/settings.json`; this design change does not create that file:

```json
{
  "yaml.schemas": {
    "./schemas/enrama-v1.schema.json": ["/enrama.yaml"]
  },
  "yaml.yamlVersion": "1.2",
  "yaml.validate": true
}
```

- Relative schema paths resolve from the workspace root. The mapping targets the
  client's root `enrama.yaml`, not every YAML file or its CI workflows.
- If F01's explicit configuration selection uses another filename/path, add its
  association pattern deliberately; do not rename or relocate the file implicitly.
- A different file layout or multi-root workspace requires an explicit adjusted
  association. Do not present the single-folder example as universal.
- Keep this association in the workspace settings. Do not add a top-level
  `$schema` property to Enrama YAML: C01 forbids unknown fields. A schema modeline
  comment is not the default mechanism and must not override the intended local
  association with another schema.
- YAML 1.2 editor parsing helps with familiar boolean spellings but does not make
  the editor enforce C02's narrower scalar/construct/resource policies.
- The local Enrama schema must work without a remote schema download after the
  extension is installed and the local file is present. This does not promise
  that all unrelated VS Code extensions/services operate offline.
- Completion, hover descriptions and structural diagnostics are the expected
  editor features. Completion may offer defaults; it must not be described as
  automatic YAML normalization or runtime validation.

The schema is ordinary portable JSON; installing a custom Enrama VS Code
extension or running an Enrama server is not part of this contract.

## Future implementation acceptance

These are requirements for later implementation, **not executed C03 tests**.

| Case | Required evidence |
| --- | --- |
| Artifact derives from current C01 models in validation mode | Reproducible generation, no handwritten duplicate field contract |
| Committed artifact agrees with generation | Deterministic regeneration/check fails on stale or missing output; intentional updates reviewed together |
| Draft declaration and self-contained references | Valid Draft 2020-12 schema with no remote Enrama fragment dependency |
| Minimal/expanded examples and defaults/nulls | Representative valid inputs accepted by the schema and C01/C02; YAML is not mutated |
| Missing/wrong-type/unknown fields, unsupported version and invalid catalog values | Representative model-expressed structural errors rejected |
| URLs/languages/duplicate IDs and parser restrictions | Runtime rejection remains authoritative; documented schema gaps are not hidden as complete validation |
| Client copy and recorded provenance | Match the selected exact tool/source revision, including an unambiguous dev commit |
| Manual update | Schema and generator reference/settings/provenance changes fit one reviewed client commit |
| Documented VS Code setup | Record actual tested VS Code/extension versions; demonstrate completion, hover where metadata exists, and structural diagnostics |
| Offline use | With extension installed/local schema present, demonstrate the association without fetching an Enrama schema |
| Alternate config filename | Document an explicit mapping without applying the schema to unrelated YAML |
| Delivery scope | No CLI/generator/editor service, schema updater, client write, release, PyPI upload or deployment |

Tests must distinguish structural schema checks from full C01/C02 validation and
keep the existing Python/CI baseline intact. A docs snippet or successful schema
generation alone is not proof that VS Code was exercised. Do not report zero
collected tests, skipped editor verification or an unavailable extension as
passing editor evidence.

## Builder choices and delivery boundary

The later implementation plan may choose internal generator/check entry points,
JSON formatting details, focused test libraries/development dependencies and
exact tested editor versions. Those choices must preserve deterministic output,
one model authority, the fixed artifact path and the approved client workflow.
No new public CLI command, runtime schema service, package publication workflow,
or independent schema release policy is implied.

Documentation-only clarifications made while writing this contract: keep schema
references internal, keep provenance in the client README, and omit volatile
machine/time/HEAD data from generated bytes. These support the accepted offline
copy and reproducible artifact workflow without adding a client-facing feature.

Issue #7 stays open with implementation acceptance unchecked. Future source
implementation integrates into `develop` only after the maintainer requests it.

## References

- [Pydantic JSON Schema generation, modes and metadata](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [JSON Schema Draft 2020-12 specification](https://json-schema.org/draft/2020-12)
- [Red Hat YAML language server: schema association and features](https://github.com/redhat-developer/yaml-language-server#associating-schemas)
- [Red Hat VS Code YAML extension](https://github.com/redhat-developer/vscode-yaml)
