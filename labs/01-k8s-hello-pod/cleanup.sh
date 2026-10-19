#!/usr/bin/env bash
# Lab 1: remove the Pod and Service. Pass --stop to also stop Minikube.
set -euo pipefail

cd "$(dirname "$0")"

kubectl delete -f service.yaml -f pod.yaml --ignore-not-found

if [ "${1:-}" = "--stop" ]; then
  minikube stop
fi
