#!/usr/bin/env bash
# Lab 2: remove the Service and Deployment. --image also removes the image.
set -euo pipefail

cd "$(dirname "$0")"

kubectl delete -f k8s/service.yaml -f k8s/deployment.yaml --ignore-not-found

if [ "${1:-}" = "--image" ]; then
  eval "$(minikube docker-env --shell bash)"
  docker rmi flask-app:1.0 || true
fi
