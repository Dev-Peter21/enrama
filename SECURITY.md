# Security policy

## Supported versions

Enrama has no released software yet. There is no supported production version
or security maintenance schedule. Version support will be documented with the
first release.

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

The planned generator must validate URL protocols, escape untrusted HTML,
load YAML safely, constrain asset paths to the client project, and avoid
arbitrary HTML or executable templates from configuration. Tests must cover
symlink escapes as well as ordinary path traversal.

Generated sites are public artifacts: client configuration and assets must
not contain secrets. Static hosting, DNS, TLS, and access to client repositories
remain the responsibility of the site operator.

Both preview and the future editor must bind to `127.0.0.1` by default. The
editor's write endpoints need an explicit local security design before release.
These are requirements for future implementation, not claims about existing code.
