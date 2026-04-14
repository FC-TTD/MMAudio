#!/usr/bin/env bash
set -euo pipefail

SOURCE_IMAGE="${SOURCE_IMAGE:-mmaudio-mmaudio:latest}"
REGISTRY_REPO="${REGISTRY_REPO:-registry.ttd/mmaudio/mmaudio}"
IMAGE_TAG="${IMAGE_TAG:-h-$(git rev-parse --short=12 HEAD)}"
PUSH_LATEST="${PUSH_LATEST:-1}"

docker image inspect "$SOURCE_IMAGE" >/dev/null

docker tag "$SOURCE_IMAGE" "${REGISTRY_REPO}:${IMAGE_TAG}"
docker push "${REGISTRY_REPO}:${IMAGE_TAG}"

if [[ "$PUSH_LATEST" == "1" ]]; then
  docker tag "$SOURCE_IMAGE" "${REGISTRY_REPO}:latest"
  docker push "${REGISTRY_REPO}:latest"
fi

printf 'published %s:%s\n' "$REGISTRY_REPO" "$IMAGE_TAG"
