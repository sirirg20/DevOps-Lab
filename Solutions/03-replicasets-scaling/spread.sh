#!/usr/bin/env bash
# Lab 3: send requests through the Service and count which Pod served each.
# Requests come from a throwaway in-cluster client, because kubectl
# port-forward would pin every request to a single Pod.
# Usage: ./spread.sh [requests]   (default 30)
set -euo pipefail

N="${1:-30}"

echo "==> Sending $N requests to flashsale-svc"
kubectl run spread-client --rm -i --restart=Never --image=busybox:1.36 -- \
  sh -c "i=0; while [ \$i -lt $N ]; do wget -qO- http://flashsale-svc/buy; echo; i=\$((i+1)); done" \
  | grep -o '"served_by_pod": *"[^"]*"' | sort | uniq -c
