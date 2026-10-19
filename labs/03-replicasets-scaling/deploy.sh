#!/usr/bin/env bash
# Lab 3: build the image in Minikube and create the ReplicaSet and Service.
set -euo pipefail

cd "$(dirname "$0")"

for tool in minikube kubectl docker; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "error: '$tool' not found on PATH (see docs/prerequisites.md)" >&2
    exit 1
  }
done

if ! minikube status >/dev/null 2>&1; then
  echo "==> Starting Minikube"
  minikube start --driver="${MINIKUBE_DRIVER:-docker}"
fi

echo "==> Building flashsale:1.0 inside Minikube's Docker daemon"
eval "$(minikube docker-env --shell bash)"
docker build -t flashsale:1.0 .

echo "==> Creating ReplicaSet and Service"
kubectl apply -f k8s/replicaset.yaml -f k8s/service.yaml

echo "==> Waiting for the Pods"
kubectl wait --for=condition=Ready pod -l app=flashsale --timeout=120s

kubectl get rs flashsale-rs
kubectl get pods -l app=flashsale -o wide
