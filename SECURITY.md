# Security policy

## Supported versions

Enrama has no public release yet. The prepared `0.1.0` metadata does not establish
PyPI availability or a supported production release.

Once 0.1.0 ships, support covers the latest 0.1.x patch until 0.2.0 is published;
older patches should upgrade. Python 3.12–3.15 is the initial verified range.
Patch releases preserve CLI/YAML v1 and advertised Python support. There is no
fixed release cadence, parallel LTS line or guaranteed remediation time. Update
this page with the actual shipped version when publication is verified.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/Dev-Peter21/enrama/security/advisories/new)
to contact the maintainer. Include the affected commit or version, a minimal
reproduction, expected and actual behavior, and the potential impact.
Use synthetic data and remove secrets from attachments.

If the reporting form is unavailable, open an issue asking the maintainer for
a private security contact, without publishing the vulnerability details.
Do not post exploit details in a public issue or pull request before coordination.

This is a volunteer-maintained project. There is no guaranteed response time
or paid bug bounty. Disclosure timing should be agreed with the reporter.

## Security design requirements

The implemented generator validates URL protocols, escapes untrusted HTML,
loads bounded YAML safely and constrains assets/output under the documented
filesystem rules. It does not execute HTML/templates from configuration.
See [validation and limits](docs/testing.md) and the linked verification records,
including traversal, symlink, protected-output and repeatability coverage.

Generated sites are public artifacts: client configuration and assets must
not contain secrets. Static hosting, DNS, TLS, and access to client repositories
remain the responsibility of the site operator.

Preview binds to `127.0.0.1`. The future editor must do so too; its write
endpoints need a separate origin/CSRF/file-safety design before implementation.
Release preparation has read-only GitHub permissions and no upload credentials
or publishing job. The separate publication workflow requires exact-candidate
authorization and protected environment approval, limits OIDC to upload and
contents write to finalization, and rejects conflicting public files/tags/assets.
See the [publication controls and limits](docs/publication.md). Workflow
implementation and publisher registration do not authorize execution/publication.
