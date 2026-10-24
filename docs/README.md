# Documentation

Enrama includes its F02 Python package/tooling foundation and F03 CI on `develop`.
The C01 models, C02 safe YAML loader/diagnostics and C03 generated editor schema
are also implemented there, along with G01 asset preparation and staging copying.
G02 shared HTML rendering is implemented too; the coordinated builder, CLI,
theme presentation and editor remain planned.

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
| [Testing](testing.md) | Validation strategy and security/packaging coverage |
| [Releasing](releasing.md) | Intended release process and first-release gates |
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
