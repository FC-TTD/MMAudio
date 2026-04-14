#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  printf 'usage: %s <host> [image] [gpu_id] [port]\n' "$0" >&2
  exit 1
fi

HOST="$1"
IMAGE="${2:-${MMAUDIO_IMAGE:-registry.ttd/mmaudio/mmaudio:latest}}"
GPU_ID="${3:-${MMAUDIO_GPU_ID:-0}}"
PORT="${4:-${MMAUDIO_PORT:-7860}}"
REMOTE_DIR="${REMOTE_DIR:-/home/docker/MMAudio}"

ssh "$HOST" "mkdir -p '$REMOTE_DIR' /TTD-Data/MMAudio/output"
scp compose.deploy.yaml "$HOST:$REMOTE_DIR/compose.deploy.yaml"
ssh "$HOST" "cd '$REMOTE_DIR' && MMAUDIO_IMAGE='$IMAGE' MMAUDIO_GPU_ID='$GPU_ID' MMAUDIO_PORT='$PORT' docker compose -f compose.deploy.yaml pull && MMAUDIO_IMAGE='$IMAGE' MMAUDIO_GPU_ID='$GPU_ID' MMAUDIO_PORT='$PORT' docker compose -f compose.deploy.yaml up -d"

printf 'deployed %s to %s on gpu %s\n' "$IMAGE" "$HOST" "$GPU_ID"
