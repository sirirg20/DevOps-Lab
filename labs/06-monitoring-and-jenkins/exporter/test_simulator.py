import random
import unittest

from simulator import DeliverySimulator


class SimulatorTests(unittest.TestCase):
    def make(self, seed=1, **kw):
        return DeliverySimulator(rng=random.Random(seed), **kw)

    def test_counts_never_negative(self):
        sim = self.make()
        for _ in range(500):
            sim.step()
            self.assertGreaterEqual(sim.pending, 0)
            self.assertGreaterEqual(sim.in_transit, 0)

    def test_orders_are_conserved(self):
        sim = self.make(seed=7)
        arrived = 0
        for _ in range(300):
            arrived += sim.step().arrivals
        self.assertEqual(arrived, sim.pending + sim.in_transit + sim.delivered)

    def test_durations_match_completions_and_range(self):
        sim = self.make(seed=3, duration_range=(20.0, 25.0))
        for _ in range(200):
            res = sim.step()
            self.assertEqual(len(res.durations), res.completed)
            for d in res.durations:
                self.assertTrue(20.0 <= d <= 25.0)

    def test_heavy_arrivals_build_backlog(self):
        sim = self.make(seed=5, arrival_max=10, dispatch_max=1)
        for _ in range(60):
            sim.step()
        self.assertGreater(sim.pending, 15)

    def test_no_arrivals_means_nothing_happens(self):
        sim = self.make(arrival_max=0)
        for _ in range(20):
            res = sim.step()
            self.assertEqual((res.arrivals, res.dispatched, res.completed), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
