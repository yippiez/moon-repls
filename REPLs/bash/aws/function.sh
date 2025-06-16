#!/bin/bash
set -euo pipefail

# tiny guardrail – 10 s CPU & 64 MB mem
ulimit -t 10 -v 65536

# ---------- helper ----------
json() { jq -nc --arg body "$1" '{statusCode:200,body:$body}'; }

# ---------- handler ----------
function handler() {
  local event="$1"
  local route method src

  method=$(echo "$event" | jq -r '.httpMethod')
  route=$(echo  "$event" | jq -r '.requestContext.resourcePath')

  # health check -------------------------------------------------
  if [[ "$method $route" == "GET /api/health" ]]; then
    json "Ok."
    return
  fi

  # code execution ----------------------------------------------
  if [[ "$method $route" == "GET /api/exec/{_src}" ]]; then
    src=$(echo "$event" | jq -r '.pathParameters._src' | base64 -d)

    # run in subshell with 5-second timeout
    result=$(timeout 5 bash -c "$src" 2>&1) || true
    json "$result"
    return
  fi

  # fallback -----------------------------------------------------
  jq -nc '{statusCode:501,body:"Not Implemented"}'
}
