#!/bin/sh
# A cold Docker build must enforce the separately reviewed build backend hashes.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cp "$ROOT/Dockerfile" "$ROOT/.dockerignore" "$ROOT/pyproject.toml" "$ROOT/uv.lock" "$ROOT/README.md" "$ROOT/LICENSE" "$WORK/"
cp -R "$ROOT/src" "$ROOT/docker" "$WORK/"
printf 'hatchling==0.0.0 --hash=sha256:0000000000000000000000000000000000000000000000000000000000000000\n' > "$WORK/build-constraints.txt"
if docker build --target cli --no-cache -t enrama-constraints-test:local "$WORK" > "$WORK/log" 2>&1; then
  docker image rm enrama-constraints-test:local >/dev/null
  echo 'FAIL: Docker build ignored invalid backend constraints' >&2
  exit 1
fi
grep -q '0.0.0' "$WORK/log" || { cat "$WORK/log" >&2; exit 1; }
echo 'Docker build rejected invalid backend constraints.'
