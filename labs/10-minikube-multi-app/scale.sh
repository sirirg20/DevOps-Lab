#!/usr/bin/env bash
# Lab 10: scale the stateless apps and watch the replicas spread over the nodes.
# Usage: ./scale.sh [catalog-replicas] [cart-replicas]   (defaults 4 and 5)
#        ./scale.sh --reset                              (back to 2 and 3)
# Redis is deliberately not scaled: it is a single instance holding the carts.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
need kubectl

if [ "${1:-}" = "--reset" ]; then
  catalog=2; cart=3
else
  catalog="${1:-4}"; cart="${2:-5}"
fi

for n in "$catalog" "$cart"; do
  case "$n" in ''|*[!0-9]*) echo "error: replica counts must be positive integers" >&2; exit 2 ;; esac
  [ "$n" -ge 2 ] || { echo "error: keep at least 2 replicas (the PodDisruptionBudgets need room)" >&2; exit 2; }
done

echo "==> Before"
k get deployment product-catalog shopping-cart

k scale deployment/product-catalog --replicas="$catalog"
k scale deployment/shopping-cart --replicas="$cart"
k rollout status deployment/product-catalog --timeout=120s
k rollout status deployment/shopping-cart --timeout=120s

echo "==> After: pods per node"
for app in product-catalog shopping-cart; do
  echo "$app:"
  pods_on_nodes "$app" | sort | uniq -c | sed 's/^/  /'
done
k get pods -o wide -l 'app in (product-catalog,shopping-cart)'
