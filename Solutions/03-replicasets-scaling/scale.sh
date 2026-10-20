#!/usr/bin/env bash
# Lab 3: scale the ReplicaSet, then demonstrate self-healing.
# Usage: ./scale.sh [replicas]   (default 5)
set -euo pipefail

TARGET="${1:-5}"
RS=flashsale-rs

echo "==> Before"
kubectl get rs "$RS"

echo "==> Scaling to $TARGET replicas"
kubectl scale rs "$RS" --replicas="$TARGET"
kubectl wait --for=condition=Ready pod -l app=flashsale --timeout=120s
kubectl get pods -l app=flashsale -o wide

echo "==> Self-healing: deleting one Pod"
VICTIM="$(kubectl get pods -l app=flashsale -o jsonpath='{.items[0].metadata.name}')"
kubectl delete pod "$VICTIM" --wait=false
sleep 3
kubectl get pods -l app=flashsale

echo "==> Waiting for the ReplicaSet to restore $TARGET Ready Pods"
kubectl wait --for=condition=Ready pod -l app=flashsale --timeout=120s
kubectl get rs "$RS"
echo "Deleted $VICTIM; a replacement with a new name was created."
