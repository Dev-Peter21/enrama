# Reusable Docker tooling

The CLI image validates, builds and previews a client. The separate static image serves only `/srv` with nginx, without Python. Generic images contain no client content. Docker Desktop/Engine with Compose v2 and curl are sufficient; no host Python is required.

## Current publication status

The initial public GHCR publication is pending. Existing GitHub OAuth access has no `write:packages`; no credentials, grants, package visibility or Actions package permissions were changed. The digest placeholders below are deliberately unusable. After authorized publication, verify unauthenticated pulls and both Linux architectures before replacing placeholders. A package initially private must have its public visibility verified. Never put client content in the generic image context or public package.

## Build locally while publication is pending

From this reviewed Enrama branch:

```sh
REVISION=$(git rev-parse HEAD)
docker build --target cli --build-arg REVISION="$REVISION" -t "enrama-cli:sha-$REVISION" .
docker build --target static --build-arg REVISION="$REVISION" -t "enrama-static:sha-$REVISION" .
```

Use these local SHA tags for testing. Production consumers should record published image digests (`ghcr.io/dev-peter21/enrama@sha256:...`), not `latest` or the development Python package version. CLI/static have different digests. The image label `org.opencontainers.image.revision` records source identity. Do not claim these local images are released.

## Consume a versioned template

Download `docker/compose.yaml` and `docker/.env.example` from a reviewed **full Git commit SHA**, record their SHA256 checksums, and commit the unmodified template in your consumer repo. You do not need a product checkout to consume a published image. This deliberately uses a regular versioned template: OCI Compose does not support bind mounts.

```sh
# ENRAMA_SOURCE_SHA must be a full reviewed commit, not a branch or tag.
curl --fail --location "https://raw.githubusercontent.com/Dev-Peter21/enrama/$ENRAMA_SOURCE_SHA/docker/compose.yaml" -o compose.yaml
curl --fail --location "https://raw.githubusercontent.com/Dev-Peter21/enrama/$ENRAMA_SOURCE_SHA/docker/.env.example" -o .env
# Compare SHA256 with the release/consumer lock before using the files.
```

Edit `.env`: supply the verified CLI digest, absolute path to a single client directory, and numeric `id -u`/`id -g`. Do not run as root. The directory must already contain `enrama.yaml` and `assets/`; a missing directory fails without being created. Keep the template outside that directory.

```sh
docker compose run --rm cli validate
docker compose run --rm cli build
docker compose up --abort-on-container-exit --exit-code-from preview preview
# Open http://127.0.0.1:8000/; Ctrl+C stops preview.
docker compose down
```

Generation has no watch/reload. Stop/restart preview after edits. A preview retains the project lock; a simultaneous build fails. Repeated builds retain collision/recovery protection. If `dist` contains edited/foreign files, move it to a backup after inspection. Never add `--force` or delete it automatically.

The bind is writable **only for the selected client directory**. Enrama needs its `.enrama` lock and atomic rename of `dist` siblings in that directory. Mounting `dist` alone or mounting the parent read-only breaks this safety design. Do not bind a repository root, home directory, credentials or Docker socket. Containers use the caller UID/GID, a read-only root, dropped capabilities, no-new-privileges and tmpfs. The CLI has no network. Preview binds `0.0.0.0` internally, publishes only host `127.0.0.1`, and serves its generated allowlist. Client inputs remain readable to the trusted CLI image, so review/pin it.

## Private production images

A consumer Dockerfile should use the pinned CLI as a build stage, copy only that client's YAML/assets into `/site` with UID/GID 10001, run `enrama validate && enrama build`, then use the pinned static image as final stage and copy `/site/dist/` to `/srv/`. Exclude `.git`, secrets and old output via a narrow `.dockerignore`. Never push a client derivative to the public Enrama package.

The runtime defaults to non-root UID 101, `PORT=8080`, HTTP on `0.0.0.0`, foreground nginx with SIGTERM handling, logs on stdout/stderr and temporary files under `/tmp`. It accepts integer PORT values 1024–65535. Use a writable `/tmp` tmpfs when running with a read-only root. Dotfiles/manifests return 404. No SPA fallback masks missing assets.

Build `linux/amd64` for Cloud Run; build `linux/arm64` for Apple Silicon. Docker's platform flag must match the CLI and runtime images available locally or in the registry. A future multi-platform published manifest must include both architectures. Local contract tests do not prove an actual Cloud Run deployment. See the official [container contract](https://docs.cloud.google.com/run/docs/container-contract) for x86_64, PORT/listen and SIGTERM requirements. No GCP resources are created by these files.

## Verification

```sh
docker build --target cli -t enrama-cli:local .
docker build --target static -t enrama-static:local .
./scripts/docker-smoke.sh
```

The smoke test creates a clean disposable consumer, verifies missing binds, non-root ownership, repeated builds, foreign output preservation, preview locking/HTTP privacy, runtime assets, default/custom PORT, invalid PORT rejection, absence of Python and graceful SIGTERM. CI runs it natively on amd64 and arm64 with read-only repository permissions. It does not publish images or add package grants.

## Publication permission decision (read-only inspection)

`Dev-Peter21/enrama` is public, default branch `main`; Actions is enabled and its
repository default workflow permission is `read`. Existing OAuth scopes omit
`read:packages`/`write:packages`, and Docker has no stored GHCR credentials.
Listing packages returned HTTP 403; existing package presence/linkage is unknown.

The minimal future change is a publication job with `contents: read` and
`packages: write`, using its ephemeral `GITHUB_TOKEN` only on the runner. It can
publish both `cli-sha-<full SHA>` and `static-sha-<full SHA>` in the single generic
`ghcr.io/dev-peter21/enrama` package. It needs no PAT, stored local Docker login,
repository-wide write default, OIDC, `id-token: write` or GCP credentials. This
permission expansion has **not** been implemented. A manual workflow new to the
repo needs default-branch integration first, or a separately authorized branch
trigger; no merge is assumed. If an existing package is not linked to Enrama,
linking/granting Actions access may be an additional permission change and must
be reviewed explicitly. First publication creates a private package; an admin
must set the generic package public and anonymous pulls/digests must be verified.

Sources: [GHCR authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[package visibility/access](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).
