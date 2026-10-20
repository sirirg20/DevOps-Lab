#!/usr/bin/env bash
# Lab 10: remove what the lab deployed.
# Usage: ./cleanup.sh             delete the namespace (apps, services, Redis, PDBs); keep the cluster
#        ./cleanup.sh --cluster   also delete the Minikube cluster and the local images
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh

if command -v kubectl >/dev/null 2>&1 && kc get namespace "$NS" >/dev/null 2>&1; then
  kc delete namespace "$NS" --wait=true
else
  echo "Namespace $NS not found; nothing to delete in the cluster."
fi

if [ "${1:-}" = "--cluster" ]; then
  if command -v minikube >/dev/null 2>&1; then
    minikube delete -p "$PROFILE" || true
  fi
  if command -v docker >/dev/null 2>&1; then
    docker rmi lab10/product-catalog:1.0 lab10/shopping-cart:1.0 >/dev/null 2>&1 || true
  fi
  echo "Removed cluster $PROFILE and local images."
else
  echo "Kept the cluster. Use --cluster to delete it too, or 'minikube stop -p $PROFILE' to pause it."
fi
