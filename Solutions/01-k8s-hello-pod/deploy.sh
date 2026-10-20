#!/usr/bin/env bash
# Lab 1: start Minikube, create the Pod and Service, and print the URL.
set -euo pipefail

cd "$(dirname "$0")"

for tool in minikube kubectl; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "error: '$tool' not found on PATH (see docs/prerequisites.md)" >&2
    exit 1
  }
done

DRIVER="${MINIKUBE_DRIVER:-docker}"

if ! minikube status >/dev/null 2>&1; then
  echo "==> Starting Minikube (driver: $DRIVER)"
  minikube start --driver="$DRIVER"
fi

echo "==> Applying manifests"
kubectl apply -f pod.yaml -f service.yaml

echo "==> Waiting for the Pod to become Ready"
kubectl wait --for=condition=Ready pod/hello-pod --timeout=120s

kubectl get pod hello-pod -o wide
kubectl get svc hello-svc

echo "==> Service URL"
minikube service hello-svc --url
echo "Run 'minikube service hello-svc' to open it in a browser."
