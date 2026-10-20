#!/usr/bin/env bash
# Lab 4: check the network, DNS names, connectivity and isolation.
set -euo pipefail

NET=lab-bridge-net
fail=0

echo "==> Network details"
docker network ls --filter "name=$NET"
docker network inspect "$NET" \
  --format 'driver={{.Driver}} scope={{.Scope}} subnet={{range .IPAM.Config}}{{.Subnet}}{{end}} gateway={{range .IPAM.Config}}{{.Gateway}}{{end}}'
echo "Attached containers:"
docker network inspect "$NET" --format '{{range .Containers}}  {{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'

echo "==> DNS resolution from web (Docker embedded DNS)"
for name in db cache; do
  docker exec web getent hosts "$name" || { echo "FAIL: $name does not resolve"; fail=1; }
done

echo "==> TCP connectivity via the API (retries while MySQL starts)"
ok=0
for _ in $(seq 1 15); do
  if curl -fsS http://localhost:5001/deps; then ok=1; echo; break; fi
  sleep 3
done
[ "$ok" = 1 ] || { echo "FAIL: /deps never returned 200"; fail=1; }

echo "==> /about"
curl -fsS http://localhost:5001/about; echo

echo "==> Isolation: db and cache are not published on the host"
docker port db || true
docker port cache || true

echo "==> Contrast: default bridge has no name-based DNS"
if docker run --rm busybox:1.36 nslookup db >/dev/null 2>&1; then
  echo "unexpected: 'db' resolved on the default bridge"; fail=1
else
  echo "'db' does not resolve from a container on the default bridge (expected)"
fi

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED"; exit 1; }
