#!/usr/bin/env bash
# Lab 10: create a 3-node Minikube cluster, build and load the images, deploy everything.
# Set MINIKUBE_DRIVER to use something other than docker. Does not use --force:
# run Docker/Minikube as a normal user (rootless setups are the safe default).
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
need minikube kubectl docker

if ! minikube -p "$PROFILE" status >/dev/null 2>&1; then
  echo "==> Starting a 3-node cluster (profile $PROFILE)"
  minikube start -p "$PROFILE" --nodes 3 --driver="${MINIKUBE_DRIVER:-docker}"
fi

echo "==> Waiting for all nodes to be Ready"
kc wait --for=condition=Ready node --all --timeout=180s
kc get nodes

echo "==> Building images"
docker build -t lab10/product-catalog:1.0 apps/product-catalog
docker build -t lab10/shopping-cart:1.0 apps/shopping-cart

# `image load` copies the image onto every node, which matters with imagePullPolicy: Never.
echo "==> Loading images into the cluster nodes"
minikube -p "$PROFILE" image load lab10/product-catalog:1.0
minikube -p "$PROFILE" image load lab10/shopping-cart:1.0

echo "==> Applying manifests (namespace first)"
kc apply -f k8s/00-namespace.yaml
kc apply -f k8s/

echo "==> Waiting for rollouts"
for dep in redis product-catalog shopping-cart; do
  k rollout status "deployment/$dep" --timeout=180s
done

k get pods -o wide
k get svc
echo
echo "Next: ./verify.sh  (checks nodes, spread, endpoints and behavior)"
