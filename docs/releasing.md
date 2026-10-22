# Release process

Status: future process. No release, PyPI distribution, release credentials,
automation, or package-name reservation is created by this initialization.

## First-release gates

Before publishing `0.1.0`:

1. Confirm the `enrama` distribution namespace and maintainer ownership; review
   the provisional name before investing in public package identity.
2. Resolve versioning, Python support, and publication ownership decisions in
   the [decision log](decisions.md).
3. Verify all [MVP acceptance criteria](product.md#release-acceptance-criteria),
   including packaging, security regression, theme, and static-hosting evidence.
4. Review bundled assets and dependency licenses; include required notices.
5. Update the changelog with actual changes, release date, and version.
6. Document the exact developer and publishing commands once the tooling exists.

## Intended automation

CI validates pull requests and `main`. A separate reviewed release workflow
should build distributions, test the artifacts, and publish only after the
maintainer authorizes the release through the agreed release process.

Prefer scoped, short-lived publishing credentials or trusted publishing once
ownership is configured. Do not put package tokens in files or enable a release
workflow before the account and destination are verified. Pin reviewed action
versions and restrict write/token permissions to the jobs that need them.

The release trigger, tag format, environment approval, and prerelease process
must be documented when the workflow is introduced. A documentation commit
must never implicitly publish a Python package or deploy a client site.

## Artifact and publication checks

- Build and inspect wheel and source-distribution contents.
- Install each built distribution in an isolated environment and test the CLI
  and both bundled themes outside the source checkout.
- Publish the reviewed version only with authorization.
- Verify installation of the exact public version and run the documented workflow.
- Create the corresponding GitHub release with changelog and artifact references.
- Update README status and the security support policy to match what shipped.

The [Pages recipe](deployment.md) is verified against an actual pinned release.
Package publication and client deployment are distinct operations.

## Subsequent changes

Document compatibility of both the package and the YAML schema. A package
version change does not automatically change `schema_version`. Before an
incompatible configuration release, define and test a migration strategy.
Release cadence and supported-version duration remain maintainer decisions.
