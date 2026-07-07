#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="ctod"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building Docker image: ${FULL_IMAGE}"
docker build -t "$FULL_IMAGE" .

echo "==> Done. Image: ${FULL_IMAGE}"
echo ""
echo "Usage:"
echo "  docker run -p 5000:5000 \\"
echo "    -v /path/to/data:/data \\"
echo "    -v /path/to/cache:/cache \\"
echo "    -e CTOD_TILE_CACHE_PATH=/cache \\"
echo "    -e CTOD_LOGGING_LEVEL=info \\"
echo "    ${FULL_IMAGE}"
echo ""
echo "Example with custom config:"
echo "  docker run -p 5000:5000 \\"
echo "    -v /home/shilei/source-data:/data \\"
echo "    -v /home/shilei/source-data/terrain:/cache \\"
echo "    -e CTOD_TILE_CACHE_PATH=/cache \\"
echo "    -e CTOD_LOGGING_LEVEL=info \\"
echo "    ${FULL_IMAGE}"
echo ""
echo "Access URLs:"
echo "  Homepage:     http://localhost:5000/terrain-service/"
echo "  API Docs:     http://localhost:5000/terrain-service/docs"
echo "  Layer JSON:   http://localhost:5000/terrain-service/tiles/dynamic/layer.json?cog=/data/your-file.tif"
