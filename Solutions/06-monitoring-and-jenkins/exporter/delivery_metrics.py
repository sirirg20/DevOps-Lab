"""Expose simulated delivery metrics for Prometheus on port 8000."""
import os
import time

from prometheus_client import Counter, Gauge, Summary, start_http_server

from simulator import DeliverySimulator

PORT = int(os.environ.get("METRICS_PORT", "8000"))
INTERVAL = float(os.environ.get("TICK_SECONDS", "1"))

# Raise ARRIVAL_MAX (for example to 8) to build a backlog and trigger the
# HighPendingDeliveries alert. Raise DURATION_MAX to trigger the slow-delivery alert.
sim = DeliverySimulator(
    arrival_max=int(os.environ.get("ARRIVAL_MAX", "3")),
    dispatch_max=int(os.environ.get("DISPATCH_MAX", "3")),
    complete_max=int(os.environ.get("COMPLETE_MAX", "3")),
    duration_range=(
        float(os.environ.get("DURATION_MIN", "10")),
        float(os.environ.get("DURATION_MAX", "40")),
    ),
)

DELIVERED = Counter("deliveries", "Deliveries completed since start")
PENDING = Gauge("deliveries_pending", "Orders waiting to be dispatched")
IN_TRANSIT = Gauge("deliveries_in_transit", "Deliveries currently on the way")
DURATION = Summary("delivery_duration_seconds", "Time taken to complete a delivery")


def main():
    start_http_server(PORT)
    print(f"Serving metrics on :{PORT}/metrics", flush=True)
    while True:
        result = sim.step()
        DELIVERED.inc(result.completed)
        for seconds in result.durations:
            DURATION.observe(seconds)
        PENDING.set(sim.pending)
        IN_TRANSIT.set(sim.in_transit)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
