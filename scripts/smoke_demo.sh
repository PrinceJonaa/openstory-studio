#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(dirname -- "$SCRIPT_DIRECTORY")
SMOKE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/openstory-smoke.XXXXXX")
SMOKE_PORT=${OPENSTORY_SMOKE_PORT:-8765}
SMOKE_BASE_URL="http://127.0.0.1:${SMOKE_PORT}"
SERVER_PID=""
SERVER_LOG="${SMOKE_ROOT}/uvicorn.log"

cleanup() {
  local exit_code=$?
  trap - EXIT
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ $exit_code -ne 0 ]] && [[ -f "$SERVER_LOG" ]]; then
    printf 'Smoke demo failed. API log follows:\n' >&2
    sed -n '1,160p' "$SERVER_LOG" >&2
  fi
  rm -rf -- "$SMOKE_ROOT"
  exit "$exit_code"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

cd "$REPOSITORY_ROOT"

python3 -c 'import socket, sys
port = int(sys.argv[1])
with socket.socket() as candidate:
    candidate.bind(("127.0.0.1", port))' "$SMOKE_PORT"

export OPENSTORY_DATABASE_URL="sqlite+pysqlite:///${SMOKE_ROOT}/openstory.db"
export OPENSTORY_WORKSPACE_ROOT="${SMOKE_ROOT}/workspaces"
export OPENSTORY_TEXT_PROVIDER=mock
export OPENSTORY_IMAGE_PROVIDER=placeholder
export OPENSTORY_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

UV_CACHE_DIR=${UV_CACHE_DIR:-/tmp/openstory-uv-cache} \
  uv run uvicorn openstory_api.main:app \
  --host 127.0.0.1 \
  --port "$SMOKE_PORT" \
  >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

API_READY=0
for _attempt in $(seq 1 60); do
  if curl --silent --fail --max-time 2 "${SMOKE_BASE_URL}/health" >/dev/null; then
    API_READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  sleep 0.1
done
if [[ $API_READY -ne 1 ]]; then
  printf 'API did not become healthy at %s.\n' "$SMOKE_BASE_URL" >&2
  exit 1
fi

CURL=(curl --silent --show-error --fail --max-time 30)

PROJECT_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/projects" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Glass Orchard Smoke Demo","target_format":"storyboard"}')
PROJECT_ID=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])' \
  <<<"$PROJECT_JSON")

SOURCE_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/projects/${PROJECT_ID}/sources" \
  -F 'file=@tests/fixtures/glass_orchard.md;type=text/markdown')
ADAPT_REQUEST=$(python3 -c 'import json, sys
payload = json.load(sys.stdin)
print(json.dumps({
    "source_chunk_ids": [chunk["id"] for chunk in payload["chunks"]],
    "number": 1,
    "target_format": "storyboard",
}))' <<<"$SOURCE_JSON")
SNAPSHOT_ORDINAL=$(python3 -c 'import json, sys
print(max(chunk["ordinal"] for chunk in json.load(sys.stdin)["chunks"]))' \
  <<<"$SOURCE_JSON")

CANON_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/projects/${PROJECT_ID}/canon/extract" \
  -H 'Content-Type: application/json' \
  -d '{}')
CANON_STATUS=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])' \
  <<<"$CANON_JSON")
"${CURL[@]}" \
  "${SMOKE_BASE_URL}/projects/${PROJECT_ID}/canon/snapshot?ordinal=${SNAPSHOT_ORDINAL}" \
  >/dev/null

EPISODE_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/projects/${PROJECT_ID}/episodes/adapt" \
  -H 'Content-Type: application/json' \
  -d "$ADAPT_REQUEST")
EPISODE_ID=$(python3 -c 'import json, sys
print(json.load(sys.stdin)["result"]["episode"]["id"])' <<<"$EPISODE_JSON")
SCENE_ID=$(python3 -c 'import json, sys
print(json.load(sys.stdin)["result"]["scenes"][-1]["id"])' <<<"$EPISODE_JSON")
EPISODE_STATUS=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])' \
  <<<"$EPISODE_JSON")

STORYBOARD_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/scenes/${SCENE_ID}/storyboard")
STORYBOARD_STATUS=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])' \
  <<<"$STORYBOARD_JSON")

RENDER_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/scenes/${SCENE_ID}/render" \
  -H 'Content-Type: application/json' \
  -d '{"width":320,"height":480}')
RENDER_STATUS=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])' \
  <<<"$RENDER_JSON")

EXPORT_REQUEST=$(python3 -c 'import json, sys
print(json.dumps({"episode_id": sys.argv[1]}))' "$EPISODE_ID")
EXPORT_JSON=$("${CURL[@]}" \
  -X POST "${SMOKE_BASE_URL}/projects/${PROJECT_ID}/export" \
  -H 'Content-Type: application/json' \
  -d "$EXPORT_REQUEST")
EXPORT_STATUS=$(python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])' \
  <<<"$EXPORT_JSON")
EXPORT_PATH=$(python3 -c 'import json, sys
print(json.load(sys.stdin)["result"]["output_path"])' <<<"$EXPORT_JSON")

test -f "${EXPORT_PATH}/episode.json"
test -f "${EXPORT_PATH}/episode.md"
test -f "${EXPORT_PATH}/manifest.json"
PNG_COUNT=$(find "${EXPORT_PATH}/storyboard" -maxdepth 1 -type f -name 'panel-*.png' | wc -l)
if [[ $PNG_COUNT -ne 6 ]]; then
  printf 'Expected six storyboard PNGs, found %s.\n' "$PNG_COUNT" >&2
  exit 1
fi

printf 'OpenStory Studio mock pipeline succeeded.\n'
printf 'Jobs: canon=%s episode=%s storyboard=%s render=%s export=%s\n' \
  "$CANON_STATUS" \
  "$EPISODE_STATUS" \
  "$STORYBOARD_STATUS" \
  "$RENDER_STATUS" \
  "$EXPORT_STATUS"
printf 'Export: %s\n' "$EXPORT_PATH"
printf 'Files: episode.json, episode.md, manifest.json, storyboard/panel-0001.png…panel-0006.png\n'
