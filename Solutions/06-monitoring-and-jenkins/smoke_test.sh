#!/usr/bin/env bash
# Lab 6: check the running stack from a throwaway container on the Compose
# network. Using the network (not localhost) makes this work identically on a
# workstation and from inside the Jenkins container.
set -euo pipefail

NET="${COMPOSE_PROJECT_NAME:-lab6}_default"
CURL_IMAGE=curlimages/curl:8.8.0

fetch() {
  docker run --rm --network "$NET" "$CURL_IMAGE" -fsS "$1"
}

# retry <description> <attempts> <command...>
retry() {
  local desc=$1 attempts=$2
  shift 2
  for _ in $(seq 1 "$attempts"); do
    if "$@" >/dev/null 2>&1; then
      echo "PASS: $desc"
      return 0
    fi
    sleep 3
  done
  echo "FAIL: $desc" >&2
  return 1
}

exporter_has_metrics() { fetch http://exporter:8000/metrics | grep -q '^deliveries_pending'; }
prometheus_ready()     { fetch http://prometheus:9090/-/ready; }
target_up()            { fetch 'http://prometheus:9090/api/v1/targets' | tr -d ' ' | grep -q '"job":"delivery_service".*"health":"up"'; }
rules_loaded()         { fetch http://prometheus:9090/api/v1/rules | grep -q 'HighPendingDeliveries'; }
grafana_healthy()      { fetch http://grafana:3000/api/health | tr -d ' ' | grep -q '"database":"ok"'; }

status=0
retry "exporter serves delivery metrics"        20 exporter_has_metrics || status=1
retry "prometheus is ready"                     20 prometheus_ready     || status=1
retry "prometheus scrapes delivery_service (up)" 20 target_up           || status=1
retry "alert rules are loaded"                  10 rules_loaded         || status=1
retry "grafana is healthy"                      20 grafana_healthy      || status=1

[ "$status" = 0 ] && echo "SMOKE TEST PASSED" || { echo "SMOKE TEST FAILED" >&2; exit 1; }
