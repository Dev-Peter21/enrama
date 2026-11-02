# Documentation

Enrama [0.1.0 is published](https://pypi.org/project/enrama/0.1.0/), including typed
YAML, safe loading/assets, JSON Schema, the guarded generator, CLI/preview and
minimal/bold themes. See the [installation instructions](../README.md#install-and-create-a-page)
and [verified publication](verification/r03-release.md). Development continues on
`develop`; the visual editor, tested client Pages recipe and final MVP acceptance
remain separate roadmap work.

| Document | Purpose |
| --- | --- |
| [Product](product.md) | Audience, problem, scope, and MVP acceptance criteria |
| [Architecture](architecture.md) | Boundaries, data flow, stack, and planned layout |
| [CLI and filesystem contract](cli-contract.md) | Accepted MVP commands, paths, overwrite/cleanup rules, manual preview, and exit codes |
| [Python development setup](development-setup.md) | Accepted F02 environment, dependency/build policy, quality tools, and executable packaging checks |
| [Foundation CI design](continuous-integration.md) | F03 workflow contract, quality job, six verification environments, permissions, and evidence |
| [Configuration](configuration.md) | Accepted YAML v1 fields, defaults, validation, catalogs, compatibility, and future acceptance cases |
| [Safe YAML loader and diagnostics](yaml-loader.md) | Accepted C02 input subset, fixed limits, source positions, diagnostic cap, Python API, and acceptance cases |
| [JSON Schema and VS Code](json-schema.md) | Accepted C03 generation, structural-assistance limits, artifact versioning, manual client updates, and local editor configuration |
| [Local assets](assets.md) | Implemented G01 formats, bounded Pillow validation, snapshots, protected staging copying, diagnostics, API and acceptance |
| [HTML rendering and metadata](rendering.md) | Implemented G02 shared HTML base, metadata, directory public URLs, destination behavior, asset integration, failures, Python API and acceptance checks |
| [Safe builder](builder.md) | Guarded output, deterministic manifests and manual interrupted-operation recovery |
| [Local demo](local-demo.md) | Reproducible CLI/preview/theme workflow and limits |
| [Themes](themes.md) | Built-in theme requirements and extension boundaries |
| [Deployment](deployment.md) | Client repositories, static hosting, and Pages plan |
| [Roadmap](roadmap.md) | Milestones, scoped tasks, dependencies, and completion evidence |
| [Published backlog](backlog.md) | MVP issue index, Kanban workflow, and final acceptance gate |
| [F03 verification](verification/f03.md) | Actual Actions runs, interpreter versions, artifacts, and failure/cancellation checks |
| [F02 verification](verification/f02.md) | Executed Python 3.12 setup and artifact evidence |
| [C01 verification](verification/c01.md) | Model/validator tests, dependency/data snapshot, and isolated artifact evidence |
| [C02 verification](verification/c02.md) | Executed loader, diagnostics, file-boundary, dependency source-build, and installed-consumer evidence |
| [C03 verification](verification/c03.md) | Executed schema/drift/packaging tests, actual VS Code provider and offline evidence, and scope limits |
| [G01 verification](verification/g01.md) | Actual image/filesystem/snapshot/copy tests, Pillow codecs, installed distributions and scope boundaries |
| [G02 verification](verification/g02.md) | Actual renderer/escaping/metadata, installed resources, static hosting and matrix evidence |
| [Local demo verification](verification/local-demo.md) | Local CLI/build/theme/preview/installed and visual evidence, with real limits |
| [Testing](testing.md) | Validation strategy and security/packaging coverage |
| [First release and PyPI publication](releasing.md) | Accepted R03 ownership, manual publication, canonical artifacts, verification, retries and maintenance |
| [Release preparation](release-preparation.md) | Implemented credential-free manual workflow, source/CI gates, canonical bundle and local rehearsal |
| [R03 preparation verification](verification/r03-preparation.md) | Executed metadata/bundle/consumer checks and honest manual-dispatch/publication boundaries |
| [Manual publication](publication.md) | Exact-candidate approvals, public consumption and immutable tag/release recovery controls |
| [0.1.0 publication verification](verification/r03-release.md) | Actual PyPI/GitHub publication, successful public consumers, hashes, recovery history and remaining acceptance |
| [Decisions](decisions.md) | Accepted choices and decisions still requiring review |

Community guidance lives at the repository root:
[contributing](../CONTRIBUTING.md), [governance](../GOVERNANCE.md),
[support](../SUPPORT.md), [conduct](../CODE_OF_CONDUCT.md), and
[security](../SECURITY.md). Changes are tracked in the [changelog](../CHANGELOG.md).

The source of truth for product scope is [product.md](product.md). The YAML v1
contract is implemented by C01 models and the C02 loader; C03 supplies the
[generated structural schema](json-schema.md) for editor assistance. The roadmap describes
planned work; the published backlog links the corresponding GitHub milestones
and issues. Creating an issue does not mean its feature is implemented.
