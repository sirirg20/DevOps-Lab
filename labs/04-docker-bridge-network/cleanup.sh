#!/usr/bin/env bash
# Lab 4: remove the containers, the network and the image.
set -euo pipefail

docker rm -f web db cache >/dev/null 2>&1 || true
docker network rm lab-bridge-net >/dev/null 2>&1 || true
docker rmi flask-api:1.0 >/dev/null 2>&1 || true
echo "Cleaned up containers, network and image."
