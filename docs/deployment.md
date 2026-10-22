# Deployment

Status: planned workflow. There is no generator, deployable demo, or Pages workflow
in this initialization.

## Separate generator and client projects

`Dev-Peter21/enrama` holds the open-source generator, built-in themes,
documentation, and eventual package releases.

A separate client repository holds its `enrama.yaml`, logo, images, and an
optional build/deployment workflow. Use one project per client, with no shared
database or multi-tenant application.

## Static hosting contract

The future `enrama build` writes a self-contained `dist/` directory. Publish
that directory to a suitable static host. Production serves files and does not
need Python, Enrama, an API, or a database.

Use the final public URL for canonical/Open Graph metadata. Generated local
asset paths must work when the site is hosted under a repository subpath as
well as a custom domain. Hosted assets and metadata must be verified at the
actual destination before declaring deployment complete.

The operator manages hosting, DNS, TLS, and any external service linked from
the page. Site content and distributed assets are public; do not include secrets
or private source files in the output.

## GitHub Pages recipe to implement in M4

The client workflow should:

1. Check out the client repository.
2. Set up a supported Python/uv environment.
3. Install a pinned, released Enrama version from its verified distribution.
4. Validate the client YAML and build the site.
5. Upload only `dist/` with `actions/upload-pages-artifact`.
6. Deploy it with `actions/deploy-pages` to the `github-pages` environment.

Grant the build only the permissions it needs. The deployment job needs Pages
write and OIDC token permissions. Use deployment concurrency, prevent untrusted
PRs from deploying, and pin reviewed action versions when writing the recipe.
The repository must use GitHub Actions as its Pages source.

The tested workflow will be provided after an installable release exists. This
avoids publishing a recipe that depends on an unavailable or unverified package.
See the [official custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Local preview

The future preview command serves generated files on `127.0.0.1` by default.
It is a local development convenience. Deployment does not require running it.
Port selection, rebuilding, and shutdown behavior are defined with the CLI task.

## Verification

After deployment, verify links, images, favicon, metadata, mobile layout, keyboard
navigation, and repository-subpath resolution. Confirm the host serves static
files independently of the local generator. Record the actual URL and results
without committing private client information to the generator repository.
