#!/usr/bin/env bash
# Lab 10: simulate losing a node. Drain it, show the apps keep answering, put it back.
# Usage: ./failover.sh [node-name]    (default: a worker that does not run Redis)
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
need kubectl

redis_node="$(k get pods -l app=redis -o jsonpath='{.items[0].spec.nodeName}')"
node="${1:-}"
if [ -z "$node" ]; then
  # Prefer a worker without Redis so the cart data survives the drill.
  node="$(kc get nodes -l '!node-role.kubernetes.io/control-plane' -o name | sed 's#node/##' \
    | grep -vx "$redis_node" | head -1 || true)"
  [ -n "$node" ] || { echo "error: no suitable worker node found" >&2; exit 1; }
fi
echo "==> Using node $node (Redis runs on $redis_node)"

restore_node() {
  echo "==> Uncordoning $node"
  kc uncordon "$node" >/dev/null 2>&1 || true
}
trap restore_node EXIT

echo "==> Draining $node (respects the PodDisruptionBudgets)"
kc drain "$node" --ignore-daemonsets --delete-emptydir-data --timeout=180s

for dep in product-catalog shopping-cart; do
  k rollout status "deployment/$dep" --timeout=180s
done
echo "==> Pods now (none should be on $node):"
k get pods -o wide

echo "==> Do the apps still answer?"
incluster 'curl -fsS http://product-catalog/products >/dev/null && echo "catalog OK";
           curl -fsS http://shopping-cart/cart > /dev/null && echo "cart OK"'

echo "==> Done. The node is restored on exit; pods are not moved back automatically."
echo "    To rebalance: kubectl --context $PROFILE -n $NS rollout restart deployment/product-catalog deployment/shopping-cart"
