#!/usr/bin/env bash
# Lab 3: remove the Service and ReplicaSet. --image also removes the image.
set -euo pipefail

cd "$(dirname "$0")"

kubectl delete -f k8s/service.yaml -f k8s/replicaset.yaml --ignore-not-found

if [ "${1:-}" = "--image" ]; then
  eval "$(minikube docker-env --shell bash)"
  docker rmi flashsale:1.0 || true
fi
