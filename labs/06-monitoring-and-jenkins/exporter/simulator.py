"""Pure-Python delivery simulation (no third-party imports, easy to unit test)."""
import random
from dataclasses import dataclass, field


@dataclass
class StepResult:
    arrivals: int
    dispatched: int
    completed: int
    durations: list = field(default_factory=list)


class DeliverySimulator:
    """Orders arrive -> pending -> dispatched (in transit) -> delivered."""

    def __init__(self, arrival_max=3, dispatch_max=3, complete_max=3,
                 duration_range=(10.0, 40.0), rng=None):
        self.arrival_max = arrival_max
        self.dispatch_max = dispatch_max
        self.complete_max = complete_max
        self.duration_range = duration_range
        self.rng = rng or random.Random()
        self.pending = 0
        self.in_transit = 0
        self.delivered = 0

    def step(self):
        arrivals = self.rng.randint(0, self.arrival_max)
        self.pending += arrivals

        dispatched = min(self.pending, self.rng.randint(0, self.dispatch_max))
        self.pending -= dispatched
        self.in_transit += dispatched

        completed = min(self.in_transit, self.rng.randint(0, self.complete_max))
        self.in_transit -= completed
        self.delivered += completed

        lo, hi = self.duration_range
        durations = [self.rng.uniform(lo, hi) for _ in range(completed)]
        return StepResult(arrivals, dispatched, completed, durations)
