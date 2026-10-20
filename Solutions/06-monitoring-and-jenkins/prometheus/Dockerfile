FROM prom/prometheus:v2.53.0
# Config is baked in (no bind mounts) so it works when Docker is driven from
# inside the Jenkins container, where host paths do not match container paths.
COPY --chown=nobody:nobody prometheus.yml alert_rules.yml /etc/prometheus/
