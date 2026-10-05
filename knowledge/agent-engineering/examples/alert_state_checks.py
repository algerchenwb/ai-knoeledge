"""Independent teaching policy; no Prometheus runtime or external notifications."""
from dataclasses import dataclass, field
import unittest

@dataclass
class Monitor:
    key: tuple[str, str, str, str]
    phase: str = 'normal'
    quality: str = 'unknown'
    pending_since: int | None = None
    recovery_since: int | None = None
    last: tuple[int, int | None] | None = None
    episode: int = 0
    events: dict = field(default_factory=dict)

    def sample(self, ts, value, now):
        # Integer seconds and integer business scores are deliberately restricted.
        if type(ts) is not int or type(now) is not int or ts < 0 or now < ts:
            raise ValueError('invalid clock')
        if value is not None and (type(value) is not int or not 0 <= value <= 100):
            raise ValueError('invalid score')
        if self.last:
            if ts < self.last[0]:
                return 'late'
            if ts == self.last[0]:
                if value != self.last[1]:
                    raise ValueError('conflicting same timestamp')
                return 'duplicate'
        gap = self.last is not None and ts - self.last[0] > 5
        self.last = (ts, value)
        if gap:
            self.pending_since = self.recovery_since = None
            if self.phase == 'pending':
                self.phase = 'normal'
        if value is None or now - ts > 5:
            self.quality = 'unknown'
            self.pending_since = self.recovery_since = None
            if self.phase == 'pending':
                self.phase = 'normal'
            return 'unknown'
        self.quality = 'fresh'
        if self.phase in ('normal', 'pending'):
            if value < 80:
                if self.pending_since is None:
                    self.pending_since = ts
                self.phase = 'pending'
                if ts - self.pending_since >= 10:
                    self.phase = 'firing'
                    self.pending_since = None
                    self.episode += 1
                    self.events[(self.key, self.episode, 'firing')] = ts
            else:
                self.phase = 'normal'
                self.pending_since = None
        else:
            if value >= 90:
                if self.recovery_since is None:
                    self.recovery_since = ts
                if ts - self.recovery_since >= 5:
                    self.phase = 'normal'
                    self.recovery_since = None
                    self.events[(self.key, self.episode, 'resolved')] = ts
            else:
                self.recovery_since = None
        return self.phase

    def display(self, now):
        if type(now) is not int or now < 0 or (self.last and now < self.last[0]):
            raise ValueError('invalid display clock')
        # Read-time freshness prevents silence from looking like fresh health.
        fresh = self.quality == 'fresh' and self.last and now - self.last[0] <= 5
        return self.phase if fresh else 'unknown'


def monitor(version='v1', tenant='t1'):
    return Monitor((tenant, 'store-7', 'score-v1', version))


def fire(m):
    for t in (0, 5, 10):
        m.sample(t, 70, t)


class Checks(unittest.TestCase):
    def test_threshold_boundary(self):
        m = monitor(); self.assertEqual(m.sample(0, 80, 0), 'normal')
        self.assertEqual(m.sample(1, 79, 1), 'pending')

    def test_hold_boundary(self):
        m = monitor()
        for t in (0, 5, 9): m.sample(t, 70, t)
        self.assertEqual(m.phase, 'pending')
        self.assertEqual(m.sample(10, 70, 10), 'firing')

    def test_pending_reset(self):
        m = monitor(); m.sample(0, 70, 0); m.sample(5, 80, 5)
        for t in (6, 11, 15): m.sample(t, 70, t)
        self.assertEqual(m.phase, 'pending')
        self.assertEqual(m.sample(16, 70, 16), 'firing')

    def test_hysteresis(self):
        m = monitor(); fire(m)
        self.assertEqual(m.sample(15, 85, 15), 'firing')
        self.assertIsNone(m.recovery_since)

    def test_recovery_boundary(self):
        m = monitor(); fire(m)
        for t in (15, 19): m.sample(t, 90, t)
        self.assertEqual(m.phase, 'firing')
        self.assertEqual(m.sample(20, 90, 20), 'normal')

    def test_recovery_reset(self):
        m = monitor(); fire(m); m.sample(15, 90, 15)
        m.sample(19, 89, 19); m.sample(20, 90, 20)
        self.assertEqual(m.sample(24, 90, 24), 'firing')
        self.assertEqual(m.sample(25, 90, 25), 'normal')

    def test_missing_retains_incident(self):
        m = monitor(); fire(m); m.sample(15, 90, 15)
        self.assertEqual(m.sample(20, None, 20), 'unknown')
        self.assertEqual(m.phase, 'firing'); self.assertEqual(len(m.events), 1)
        self.assertIsNone(m.recovery_since)

    def test_stale_not_recovered(self):
        m = monitor(); fire(m)
        self.assertEqual(m.sample(15, 100, 21), 'unknown')
        self.assertEqual(m.phase, 'firing')

    def test_silence_display(self):
        m = monitor(); m.sample(0, 100, 0)
        self.assertEqual(m.display(5), 'normal')
        self.assertEqual(m.display(6), 'unknown')

    def test_duplicate(self):
        m = monitor(); fire(m)
        self.assertEqual(m.sample(10, 70, 10), 'duplicate')
        self.assertEqual(len(m.events), 1)

    def test_late(self):
        m = monitor(); fire(m)
        self.assertEqual(m.sample(9, 100, 10), 'late')
        self.assertEqual(m.phase, 'firing')

    def test_conflict(self):
        m = monitor(); fire(m)
        with self.assertRaises(ValueError): m.sample(10, 100, 10)
        self.assertEqual(m.last, (10, 70))

    def test_gap_resets_hold(self):
        m = monitor(); m.sample(0, 70, 0); m.sample(10, 70, 10)
        self.assertEqual(m.phase, 'pending'); self.assertEqual(m.pending_since, 10)

    def test_gap_resets_recovery(self):
        m = monitor(); fire(m); m.sample(15, 90, 15)
        self.assertEqual(m.sample(21, 90, 21), 'firing')
        self.assertEqual(m.recovery_since, 21)

    def test_missing_resets_pending(self):
        m = monitor(); m.sample(0, 70, 0); m.sample(5, None, 5)
        self.assertEqual(m.sample(10, 70, 10), 'pending')
        self.assertEqual(m.pending_since, 10)

    def test_episode_dedup(self):
        m = monitor(); fire(m)
        for t, v in ((15, 70), (20, 90), (25, 90), (30, 100), (35, 70), (40, 70), (45, 70)):
            m.sample(t, v, t)
        self.assertEqual(m.episode, 2)
        self.assertEqual([k[2] for k in m.events], ['firing', 'resolved', 'firing'])

    def test_identity_isolation(self):
        a, b, c = monitor(), monitor(tenant='t2'), monitor(version='v2')
        for m in (a, b, c): fire(m)
        self.assertEqual(len(set().union(*(set(m.events) for m in (a, b, c)))), 3)

    def test_invalid_input(self):
        for args in ((True, 70, 0), (0, True, 0), (0, 101, 0), (1, 70, 0), (0, 70, 0.0)):
            with self.assertRaises(ValueError): monitor().sample(*args)
        with self.assertRaises(ValueError): monitor().display(-1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
