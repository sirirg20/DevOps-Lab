#!/usr/bin/env bash
# Lab 10: verify the cluster, placement, Services and application behavior.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
need kubectl

fail=0
pass() { echo "PASS: $*"; }
bad()  { echo "FAIL: $*" >&2; fail=1; }

# 1. Cluster: three nodes, all Ready.
nodes="$(kc get nodes --no-headers)"
count="$(echo "$nodes" | wc -l | tr -d ' ')"
not_ready="$(echo "$nodes" | awk '$2 != "Ready"' | wc -l | tr -d ' ')"
[ "$count" = 3 ] && pass "cluster has 3 nodes" || bad "expected 3 nodes, found $count"
[ "$not_ready" = 0 ] && pass "all nodes Ready" || bad "$not_ready node(s) not Ready"

# 2. Deployments have all replicas ready.
check_ready() {
  local app=$1 want=$2 got
  got="$(k get deployment "$app" -o jsonpath='{.status.readyReplicas}')"
  [ "${got:-0}" = "$want" ] && pass "$app: $got/$want replicas ready" || bad "$app: ${got:-0}/$want replicas ready"
}
check_ready redis 1
check_ready product-catalog 2
check_ready shopping-cart 3

# 3. Replicas are spread over more than one node.
for app in product-catalog shopping-cart; do
  distinct="$(pods_on_nodes "$app" | sort -u | grep -c . || true)"
  [ "$distinct" -ge 2 ] && pass "$app replicas run on $distinct different nodes" \
    || bad "$app replicas all on one node"
done

# 4. Each Service actually selects pods: endpoints exist and match the ready replicas.
#    (A Service in a different namespace than its pods, or with a wrong selector, has none.)
for pair in product-catalog:2 shopping-cart:3 redis:1; do
  svc=${pair%%:*}; want=${pair##*:}
  got="$(k get endpoints "$svc" -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w | tr -d ' ')"
  [ "$got" = "$want" ] && pass "service $svc has $got endpoints" || bad "service $svc has $got endpoints, expected $want"
done

# 5. PodDisruptionBudgets exist.
for pdb in product-catalog shopping-cart; do
  k get pdb "$pdb" >/dev/null 2>&1 && pass "PodDisruptionBudget $pdb exists" || bad "PodDisruptionBudget $pdb missing"
done

# 6. Behavior, from inside the cluster.
snippet="$(cat <<'EOF'
echo "CATALOG $(curl -fsS http://product-catalog/products | tr -d ' \r\n')"
curl -s -X DELETE -o /dev/null http://shopping-cart/cart
echo "EMPTY $(curl -fsS http://shopping-cart/cart | tr -d ' \r\n')"
for item in Laptop Pen Book; do
  curl -s -o /dev/null -w "POST %{http_code}\n" -H 'Content-Type: application/json' \
    -d "{\"item\": \"$item\"}" http://shopping-cart/cart
done
curl -s -o /dev/null -w "BADPOST %{http_code}\n" -H 'Content-Type: application/json' \
  -d '{"nope": 1}' http://shopping-cart/cart
i=0
while [ $i -lt 15 ]; do
  r=$(curl -si http://shopping-cart/cart | tr -d '\r')
  pod=$(printf '%s' "$r" | sed -n 's/^[Xx]-[Ss]erved-[Bb]y: //p')
  cnt=$(printf '%s' "$r" | tr -d ' \n' | sed -n 's/.*"count":\([0-9]*\).*/\1/p')
  echo "GET count=$cnt pod=$pod"
  i=$((i + 1))
done
EOF
)"
out="$(incluster "$snippet" || true)"

echo "$out" | grep -q '^CATALOG.*Laptop.*Smartphone.*Headphones' \
  && pass "catalog returns the three products" || bad "catalog response unexpected"
echo "$out" | grep -q '^EMPTY.*"count":0' && pass "cart starts empty" || bad "cart was not empty after DELETE"
posts="$(echo "$out" | grep -c '^POST 201' || true)"
[ "$posts" = 3 ] && pass "3 items added (HTTP 201)" || bad "expected 3 x 201, got $posts"
echo "$out" | grep -q '^BADPOST 400' && pass "invalid cart body rejected (400)" || bad "invalid body not rejected"

gets="$(echo "$out" | grep '^GET ' || true)"
consistent="$(echo "$gets" | grep -c 'count=3 ' || true)"
total="$(echo "$gets" | grep -c . || true)"
pods_seen="$(echo "$gets" | sed -n 's/.*pod=//p' | sort -u | grep -c . || true)"
[ "$total" -gt 0 ] && [ "$consistent" = "$total" ] \
  && pass "all $total cart reads agree (3 items) regardless of which replica answered" \
  || bad "cart reads disagree: $consistent of $total show 3 items (cart state not shared?)"
[ "$pods_seen" -ge 2 ] && pass "reads were served by $pods_seen different cart replicas" \
  || bad "all reads came from one replica, so consistency was not really tested"

k run "cleanup-$RANDOM" --rm -i --restart=Never --quiet --image=curlimages/curl:8.8.0 --command -- \
  curl -s -X DELETE -o /dev/null http://shopping-cart/cart >/dev/null 2>&1 || true

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED" >&2; exit 1; }
