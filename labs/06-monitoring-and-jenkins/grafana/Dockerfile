FROM grafana/grafana:11.1.0
# Provisioning is baked in so no host bind mounts are needed (see prometheus/Dockerfile).
COPY --chown=472:0 provisioning /etc/grafana/provisioning
