#!/usr/bin/env bash
# Lab 2: build the image inside Minikube and deploy the Flask app.
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

echo "==> Building image inside Minikube's Docker daemon"
eval "$(minikube docker-env --shell bash)"
docker build -t flask-app:1.0 .

echo "==> Applying Deployment"
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/flask-app --timeout=120s

# Set SKIP_SERVICE=1 to deploy without a Service (README step 6).
if [ "${SKIP_SERVICE:-0}" != "1" ]; then
  kubectl apply -f k8s/service.yaml
  echo "==> Service URL (keep this terminal open with the Docker driver)"
  minikube service flask-app-service --url
fi
