#!/usr/bin/env bash
set -euo pipefail
IMAGE="ghcr.io/open-webui/open-webui:main"
NAME="open-webui"
HOST_PORT="3001"
CONTAINER_PORT="8080"
docker pull "$IMAGE"
docker rm -f "$NAME" 2>/dev/null || true
docker run -d \
  --name "$NAME" \
  --restart always \
  -p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}" \
  -v open-webui:/app/backend/data \
  "$IMAGE"
sleep 5
docker ps | grep "$NAME" || true
curl -I "http://127.0.0.1:${HOST_PORT}" || true
