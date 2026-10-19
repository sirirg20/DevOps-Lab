#!/usr/bin/env bash
# Shared helpers for the Lab 10 scripts (sourced, not executed).

PROFILE=lab10     # Minikube profile; also the kubectl context name
NS=lab10          # namespace for every resource in this lab

need() {
  for tool in "$@"; do
    command -v "$tool" >/dev/null 2>&1 || {
      echo "error: '$tool' not found on PATH (see docs/prerequisites.md)" >&2
      exit 1
    }
  done
}

# kubectl pinned to this lab's cluster and namespace, so it cannot touch another cluster by accident.
k() { kubectl --context "$PROFILE" -n "$NS" "$@"; }
kc() { kubectl --context "$PROFILE" "$@"; }

# incluster '<sh snippet>' : run a snippet in a throwaway pod inside the namespace.
# Testing from inside the cluster avoids needing `minikube service` tunnels.
incluster() {
  k run "probe-$RANDOM" --rm -i --restart=Never --quiet \
    --image=curlimages/curl:8.8.0 --command -- sh -c "$1"
}

# pods_on_nodes <app>: one node name per pod.
pods_on_nodes() {
  k get pods -l "app=$1" -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}'
}
