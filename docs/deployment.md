# Deployment

Status: the generator is [released as 0.1.0](verification/r03-release.md), while
the tested client Pages recipe/public deployment remains R04 work. See the
[source demo](local-demo.md); a package release does not establish a deployed site.

## Separate generator and client projects

`Dev-Peter21/enrama` holds the open-source generator, built-in themes,
documentation, and package releases.

A separate client repository holds its `enrama.yaml`, logo, images, and an
optional build/deployment workflow. Use one project per client, with no shared
database or multi-tenant application.

## Static hosting contract

`enrama build` writes a self-contained `dist/` directory. Publish
that directory to a suitable static host. Production serves files and does not
need Python, Enrama, an API, or a database.

Use the final public URL for canonical/Open Graph metadata. Generated local
asset paths must work when the site is hosted under a repository subpath as
well as a custom domain. Hosted assets and metadata must be verified at the
actual destination before declaring deployment complete.

The agreed [G02 URL contract](rendering.md#public-url-and-local-path-rules)
interprets `site.url` as the public directory containing `index.html`, deriving
a trailing slash when needed. Local image/favicon paths remain relative; the
public base supplies canonical/OG URLs without redirecting local preview assets.

The operator manages hosting, DNS, TLS, and any external service linked from
the page. Site content and distributed assets are public; do not include secrets
or private source files in the output.

## R04 GitHub Pages recipe contract

The maintainer accepted this design on 2026-11-03 for
[issue #18](https://github.com/Dev-Peter21/enrama/issues/18). The recipe will be
documented in the generator repository for clients to copy. The client
repository owns its YAML, assets, and workflow.

### Test destination

Use the public repository `Dev-Peter21/enrama-pages-demo` with synthetic content
and no custom domain. The expected Pages URL is
`https://dev-peter21.github.io/enrama-pages-demo/`. Use GitHub Actions as the
Pages source. Confirm the actual Pages base URL before deploying. The configured
`site.url` must match that HTTPS directory URL, including the repository subpath
and a trailing slash. A mismatch blocks deployment and is corrected in the
reviewed YAML. Repository creation, Pages setup, and each live deployment are
separate execution steps.

### Build and deployment

1. On pull requests and pushes to `main`, validate and build the client site.
   Use Linux, Python 3.12, pinned uv 0.13.5, and the public PyPI release
   `enrama==0.1.0`. Start from a clean client checkout and record the installed
   versions. Use the released CLI for validation and generation.
2. A manual run from the client's `main` builds the reviewed commit. Upload
   only the static contents of `dist/` with `actions/upload-pages-artifact`.
   Check that `index.html` is at the artifact root and that generated assets
   resolve within it. The publication artifact excludes client source files,
   workspace state, and the hidden build manifest. Preserve the local manifest
   for build evidence.
3. The deployment job depends on the successful build and uses
   `actions/deploy-pages` with that run's artifact. It does not rebuild after
   approval. Pin reviewed action revisions by commit SHA during implementation.
   The build uses read access. Pages write and OIDC token permissions are
   confined to the deployment job.
4. Restrict the `github-pages` environment to `main`. Pedro reviews the
   commit, theme, and artifact before approving each deployment. Allow him to
   approve a run he started. Serialize deployments for the destination without
   canceling an active deployment. Verify one theme before starting the next.

See the [official Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
and [environment protection settings](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

### Live acceptance

Deploy `bold` first and `minimal` second from separate reviewed commits on
`main`. Each commit selects its theme in `enrama.yaml`, and each deployment
requires its own approval. Leave `minimal` as the final public demo.

For each theme, check the root locally and the repository subpath on Pages.
Verify that the live HTML, CSS, images, and favicon load, that the canonical
and Open Graph metadata use the expected public URLs, and that enabled links
have the expected destinations. Check mobile layout and keyboard navigation.
Confirm that hosting serves static files. Record the client SHA, installed
Enrama version, theme, Actions run, artifact identity, deployment URL, and check
results for both runs before accepting R04.

### Failure and recovery

A validation or build failure blocks deployment and preserves any existing
site. A failed live check is recorded and leaves R04 open. Recover by restoring
the last verified client content in a reviewed commit on `main`, then build,
approve, deploy, and verify it again. If there is no verified deployment yet,
fix the issue in a reviewed commit and repeat the checks. Recovery is manual.

## Local preview

The preview command serves generated files on `127.0.0.1` by default.
It is a local development convenience. Deployment does not require running it.
The accepted [CLI contract](cli-contract.md#manual-preview-lifecycle) fixes the
default port to `8000`, allows `--port`, and requires manual stop/restart to
rebuild. An occupied port fails without changing output. Normal `Ctrl+C` while
serving releases the port and retains `dist/`.

## Verification

After deployment, verify links, images, favicon, metadata, mobile layout, keyboard
navigation, and repository-subpath resolution. Confirm the host serves static
files independently of the local generator. Record the actual URL and results
without committing private client information to the generator repository.
