#!/usr/bin/env bash
# Run the swarm search demo once:  AURA_BIN=... AURA_STDLIB=<aura>/lib SCM_SEARCH_N=8 scripts/run_search.sh
# Builds build/search-entry.aura = aura/search.aura + aura/search-main.aura, and runs it after the demo
# modules (like scripts/run.sh) inside the Aura dev image. AURA_PATH points Aura at the stdlib
# (std/pso, std/ant, std/swarm).  All SCM_* variables are passed through.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${AURA_BIN:?set AURA_BIN to an Aura build-rel/aura}"
: "${AURA_STDLIB:?set AURA_STDLIB to an Aura checkout lib/ directory (contains std/pso.aura)}"
MODULES="aura/data.aura aura/scenario.aura aura/runtime.aura aura/workspace.aura aura/agents.aura aura/supervisor.aura aura/evolve.aura aura/search.aura"
mkdir -p "$REPO/build"; FILE="build/${SCM_BUILD_NAME:-search}.all.aura"
# SCM_EXTRA_MODULES (space-separated, e.g. "aura/llm-search.aura build/llm-proposals.aura") are appended
# after the modules; SCM_MAIN replaces aura/search-main.aura (e.g. build/llm-main.aura).
( cd "$REPO"; for m in $MODULES ${SCM_EXTRA_MODULES:-}; do cat "$m"; echo; done; cat "${SCM_MAIN:-aura/search-main.aura}" ) > "$REPO/$FILE"
BIN_DIR="$(cd "$(dirname "$AURA_BIN")" && pwd)"; STD="$(cd "$AURA_STDLIB" && pwd)"
envs=(-e AURA_SANDBOX=off -e AURA_PIPELINE_STRICT=0 -e AURA_PATH="$STD")
# explicit K=V: `sudo docker` drops the caller's environment
while IFS= read -r kv; do envs+=(-e "$kv"); done < <(env | grep '^SCM_' || true)
# Host modes (no docker): AURA_LIBDIR=<dir with a new-enough glibc/libstdc++ and ld-linux-x86-64.so.2>
# runs the binary through that loader; AURA_NO_DOCKER=1 runs it directly.
if [ -n "${AURA_LIBDIR:-}" ]; then
  cd "$REPO"; exec env AURA_SANDBOX=off AURA_PIPELINE_STRICT=0 AURA_PATH="$STD" timeout "${SCM_TIMEOUT:-900}" \
    "$AURA_LIBDIR/ld-linux-x86-64.so.2" --library-path "$BIN_DIR:$AURA_LIBDIR" "$AURA_BIN" --load "$FILE"
fi
if [ "${AURA_NO_DOCKER:-0}" = 1 ]; then
  cd "$REPO"; exec env AURA_SANDBOX=off AURA_PIPELINE_STRICT=0 AURA_PATH="$STD" timeout "${SCM_TIMEOUT:-900}" "$AURA_BIN" --load "$FILE"
fi
IMAGE="${AURA_IMAGE:-ghcr.io/cybrid-systems/dev:v1.0.9}"
DOCKER="docker"; docker info >/dev/null 2>&1 || DOCKER="sudo docker"
exec $DOCKER run --rm -i --memory=6g --entrypoint bash --user "$(id -u):$(id -g)" -e HOME=/tmp "${envs[@]}" \
  -v "$REPO:$REPO" -v "$BIN_DIR:$BIN_DIR:ro" -v "$STD:$STD:ro" -w "$REPO" "$IMAGE" \
  -c "LD_LIBRARY_PATH=$BIN_DIR timeout ${SCM_TIMEOUT:-900} $AURA_BIN --load $FILE"
