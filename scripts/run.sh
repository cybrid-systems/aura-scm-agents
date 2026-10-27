#!/usr/bin/env bash
# Run an Aura file from the repo root inside the Aura dev image (glibc/libstdc++ match build-rel).
#   AURA_BIN=/path/to/aura/build-rel/aura scripts/run.sh [aura/main.aura]
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-aura/main.aura}"
MODULES="aura/data.aura aura/scenario.aura aura/runtime.aura aura/workspace.aura aura/agents.aura aura/supervisor.aura aura/evolve.aura"
mkdir -p "$REPO/build"; FILE="build/$(basename "$SRC" .aura).all.aura"
( cd "$REPO"; for m in $MODULES; do [ "$m" = "$SRC" ] || cat "$m"; echo; done; cat "$SRC" ) > "$REPO/$FILE"
: "${AURA_BIN:?set AURA_BIN to an Aura build-rel/aura}"
BIN_DIR="$(cd "$(dirname "$AURA_BIN")" && pwd)"
LIBS="${AURA_LIB:-$BIN_DIR/lib}"
if [ "${AURA_NO_DOCKER:-0}" = 1 ]; then
  cd "$REPO"; exec env AURA_SANDBOX=off AURA_PIPELINE_STRICT=0 timeout "${SCM_TIMEOUT:-300}" "$AURA_BIN" --load "$FILE"
fi
IMAGE="${AURA_IMAGE:-ghcr.io/cybrid-systems/dev:v1.0.9}"
DOCKER="docker"; docker info >/dev/null 2>&1 || DOCKER="sudo docker"
mounts=(-v "$REPO:$REPO" -v "$BIN_DIR:$BIN_DIR")
[ -d "$LIBS" ] && mounts+=(-v "$LIBS:$LIBS")
[ -n "${AURA_EXTRA_MOUNT:-}" ] && mounts+=(-v "$AURA_EXTRA_MOUNT:$AURA_EXTRA_MOUNT")
exec $DOCKER run --rm -i --memory=4g --entrypoint bash --user "$(id -u):$(id -g)" -e HOME=/tmp "${mounts[@]}" -w "$REPO" \
  -e AURA_SANDBOX=off -e AURA_PIPELINE_STRICT=0 -e SCM_MODE="${SCM_MODE:-all}" "$IMAGE" \
  -c "LD_LIBRARY_PATH=$LIBS:${AURA_EXTRA_MOUNT:-} timeout ${SCM_TIMEOUT:-300} $AURA_BIN --load $FILE"
