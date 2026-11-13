#!/bin/sh
# Integration test: requires Docker, Compose v2, curl; no host Python.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENRAMA_CLI_IMAGE=${ENRAMA_CLI_IMAGE:-enrama-cli:local}
ENRAMA_STATIC_IMAGE=${ENRAMA_STATIC_IMAGE:-enrama-static:local}
export ENRAMA_CLI_IMAGE ENRAMA_STATIC_IMAGE
export ENRAMA_UID=$(id -u) ENRAMA_GID=$(id -g)
[ "$ENRAMA_UID" != 0 ] || { echo 'Run as a non-root user' >&2; exit 1; }
WORK=$(mktemp -d)
export ENRAMA_SITE="$WORK/client" ENRAMA_PREVIEW_PORT=${ENRAMA_PREVIEW_PORT:-18871}
PROJECT="enrama-test-$$"
compose() { docker compose -p "$PROJECT" -f "$ROOT/docker/compose.yaml" "$@"; }
cleanup() {
  compose down --timeout 5 >/dev/null 2>&1 || true
  docker rm -f "$PROJECT-static" >/dev/null 2>&1 || true
  docker image rm "$PROJECT-site" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# A missing path must fail without creating it.
if compose run --rm cli validate >"$WORK/missing.log" 2>&1; then exit 1; fi
test ! -e "$ENRAMA_SITE"
docker run --rm --network none --user "$ENRAMA_UID:$ENRAMA_GID" \
  --mount "type=bind,src=$WORK,dst=/work" "$ENRAMA_CLI_IMAGE" init /work/client
compose run --rm cli validate
compose run --rm cli build
compose run --rm cli build
test "$(ls -nd "$ENRAMA_SITE/dist" | awk '{print $3}')" = "$ENRAMA_UID"
printf 'foreign' > "$ENRAMA_SITE/dist/foreign.txt"
if compose run --rm cli build >"$WORK/conflict.log" 2>&1; then exit 1; fi
test "$(cat "$ENRAMA_SITE/dist/foreign.txt")" = foreign
rm "$ENRAMA_SITE/dist/foreign.txt"
compose up -d preview
URL="http://127.0.0.1:$ENRAMA_PREVIEW_PORT"
ready() {
  count=0
  until curl -fsS "$URL/" -o "$WORK/page.html" 2>/dev/null; do
    count=$((count + 1)); [ "$count" -lt 60 ] || { echo 'HTTP timeout' >&2; exit 1; }
    sleep 0.2
  done
}
ready
for path in enrama.yaml .enrama-manifest.json ../enrama.yaml; do
  test "$(curl --path-as-is -s -o /dev/null -w '%{http_code}' "$URL/$path")" = 404
done
if compose run --rm cli build >"$WORK/locked.log" 2>&1; then exit 1; fi
compose stop preview
compose run --rm cli build
# Bake only generated static files into a production derivative.
cat > "$WORK/Dockerfile" <<'DOCKER'
ARG STATIC_IMAGE
FROM ${STATIC_IMAGE}
COPY client/dist/ /srv/
DOCKER
docker build --build-arg "STATIC_IMAGE=$ENRAMA_STATIC_IMAGE" -t "$PROJECT-site" "$WORK"
for port in 8080 9090; do
  docker run -d --name "$PROJECT-static" --read-only --tmpfs /tmp:rw,noexec,nosuid \
    --cap-drop ALL --security-opt no-new-privileges -e "PORT=$port" \
    -p "127.0.0.1:$ENRAMA_PREVIEW_PORT:$port" "$PROJECT-site" >/dev/null
  ready
  grep -o 'assets/[^" ]*' "$WORK/page.html" | sort -u > "$WORK/assets.txt"
  test -s "$WORK/assets.txt"
  while IFS= read -r asset; do curl -fsS "$URL/$asset" -o /dev/null; done < "$WORK/assets.txt"
  for path in enrama.yaml .enrama-manifest.json; do
    test "$(curl -s -o /dev/null -w '%{http_code}' "$URL/$path")" = 404
  done
  docker exec "$PROJECT-static" sh -c 'test "$(id -u)" != 0; ! command -v python; ! command -v python3'
  docker stop --time 5 "$PROJECT-static" >/dev/null
  test "$(docker inspect -f '{{.State.ExitCode}}' "$PROJECT-static")" = 0
  docker rm "$PROJECT-static" >/dev/null
done
for port in 0 80 65536 invalid; do
  if docker run --rm -e "PORT=$port" "$PROJECT-site" >"$WORK/port.log" 2>&1; then exit 1; fi
done
printf 'Docker smoke passed: ownership, collision, locking, preview, assets, PORT, no Python, SIGTERM.\n'
