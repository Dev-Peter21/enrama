# Product definition

## Purpose and first user

Enrama will generate independently hosted link-in-bio pages from YAML using
Python. It is intended for developers and small agencies maintaining one or
more client pages. The first validation case is replacing a client's unavailable
Linktree page with a professional page they can host and update themselves.

**Your links. Your hosting. Your rules.**

Each client has a separate project containing configuration and assets. Enrama
generates static files; the published page has no dependency on an Enrama
service, account, Python runtime, API, or database.

## Principles

1. **Static first:** HTML, CSS, images, and minimal JavaScript are the product.
2. **Configuration as code:** versioned YAML is the source of truth.
3. **No central infrastructure:** no mandatory hosted Enrama services.
4. **One reusable engine:** CLI and a later editor share validation and build logic.
5. **Practical extensibility:** typed models and independent themes without
   unnecessary layers, services, or plugin infrastructure.

## Target 0.1.0

| Capability | Expected user outcome |
| --- | --- |
| CLI | Create, validate, preview, and build a client project with clear errors |
| Configuration | Edit profile, ordered links, local images, colors, and theme in YAML |
| Themes | Choose `minimal` or `bold`, both responsive and accessible |
| Output | Publish self-contained static files from `dist/` |
| Discoverability | Set semantic content, SEO and Open Graph metadata, and favicon |
| Distribution | Install a Python package without cloning the source |
| Delivery | Use a tested example and a GitHub Pages deployment recipe |
| Quality | Run automated tests, typing, linting, and packaging checks in CI |

The intended commands are `enrama init`, `enrama validate`, `enrama preview`,
and `enrama build`. Their exact options and filesystem behavior are a decision
for M0/M1; see [decisions](decisions.md).

## Target 0.2

A local visual editor using FastAPI, Jinja2, HTML forms, and minimal JavaScript.
It must call the same core services as the CLI and preserve the YAML contract.
Saving configuration should preserve comments and structure; evaluate a
round-trip YAML library before selecting the editor's writer.

## Outside the MVP

- Accounts, login, and multi-tenant infrastructure.
- Managed hosting, subscriptions, and billing.
- Click analytics and URL shortening.
- Angular or another separate frontend application for the initial editor.
- Remote theme execution or a general plugin marketplace.

## Release acceptance criteria

Version `0.1.0` is complete only when evidence demonstrates all of the following:

1. Install Enrama from its Python distribution without cloning the source.
2. Create a client project with `enrama init`.
3. Validate edited YAML with field-specific, understandable errors.
4. Preview the generated page locally.
5. Generate the published contents of `dist/` with `enrama build`.
6. Serve those files without Python, an API, or a database, including on a
   host with a repository path prefix.
7. Verify both themes at mobile and desktop sizes, with keyboard access.
8. Pass CI tests and packaging checks using installed package artifacts.
9. Cover dangerous URL protocols, HTML escaping, asset traversal, and repeatable builds.
10. Reproduce the complete workflow from the example and documentation.

## Current delivery boundary

This initialization provides the repository, license, documentation, and
contribution templates. It does not implement product code, reserve a PyPI
name, publish a release, deploy a site, or create client repositories.
