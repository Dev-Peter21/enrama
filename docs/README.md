# Documentation

Enrama includes its F02 Python package/tooling foundation on `develop`.
The CLI, generator, themes, and editor remain planned unless stated otherwise.

| Document | Purpose |
| --- | --- |
| [Product](product.md) | Audience, problem, scope, and MVP acceptance criteria |
| [Architecture](architecture.md) | Boundaries, data flow, stack, and planned layout |
| [CLI and filesystem contract](cli-contract.md) | Accepted MVP commands, paths, overwrite/cleanup rules, manual preview, and exit codes |
| [Python development setup](development-setup.md) | Accepted F02 environment, dependency/build policy, quality tools, and executable packaging checks |
| [Foundation CI design](continuous-integration.md) | Accepted F03 triggers, quality job, six verification environments, permissions, and future evidence |
| [Configuration](configuration.md) | Draft public YAML contract and compatibility |
| [Themes](themes.md) | Built-in theme requirements and extension boundaries |
| [Deployment](deployment.md) | Client repositories, static hosting, and Pages plan |
| [Roadmap](roadmap.md) | Milestones, scoped tasks, dependencies, and completion evidence |
| [Published backlog](backlog.md) | MVP issue index, Kanban workflow, and final acceptance gate |
| [F02 verification](verification/f02.md) | Executed Python 3.12 setup and artifact evidence |
| [Testing](testing.md) | Validation strategy and security/packaging coverage |
| [Releasing](releasing.md) | Intended release process and first-release gates |
| [Decisions](decisions.md) | Accepted choices and decisions still requiring review |

Community guidance lives at the repository root:
[contributing](../CONTRIBUTING.md), [governance](../GOVERNANCE.md),
[support](../SUPPORT.md), [conduct](../CODE_OF_CONDUCT.md), and
[security](../SECURITY.md). Changes are tracked in the [changelog](../CHANGELOG.md).

The source of truth for product scope is [product.md](product.md). The YAML
contract is a draft until reviewed and implemented in M1. The roadmap describes
planned work; the published backlog links the corresponding GitHub milestones
and issues. Creating an issue does not mean its feature is implemented.
