"""Independent teaching state machine; no HTTP or pybreaker dependency."""
from dataclasses import dataclass
from threading import Barrier, Lock, Thread


class Blocked(Exception):
    pass


@dataclass(frozen=True)
class Permit:
    sequence: int
    epoch: int
    probe: bool


class Breaker:
    def __init__(self, clock, threshold=2, cooldown=10):
        self.clock, self.threshold, self.cooldown = clock, threshold, cooldown
        self.state, self.failures, self.epoch, self.sequence = 'closed', 0, 0, 0
        self.until = 0
        self.pending = {}
        self.lock = Lock()

    def admit(self, deadline):
        with self.lock:
            now = self.clock()
            if now >= deadline:
                raise Blocked('task deadline expired')
            if self.state == 'open':
                if now < self.until:
                    raise Blocked('circuit open')
                self.state = 'half_open'
            probe = self.state == 'half_open'
            if probe and any(p.probe and p.epoch == self.epoch for p in self.pending.values()):
                raise Blocked('probe already active')
            self.sequence += 1
            permit = Permit(self.sequence, self.epoch, probe)
            self.pending[permit.sequence] = permit
            return permit

    def _open(self):
        self.state = 'open'
        self.until = self.clock() + self.cooldown
        self.epoch += 1

    def finish(self, permit, outcome):
        if outcome not in {'success', 'system_failure', 'business_rejection'}:
            raise ValueError('unknown outcome')
        with self.lock:
            if self.pending.get(permit.sequence) != permit:
                raise ValueError('invalid or duplicate permit')
            del self.pending[permit.sequence]
            if permit.epoch != self.epoch:
                return False  # An old completion must not close a newer open state.
            if permit.probe:
                if outcome == 'success':
                    self.state, self.failures = 'closed', 0
                    self.epoch += 1
                else:
                    self._open()  # Rejection is not sufficient evidence of recovery.
            elif outcome == 'success':
                self.failures = 0
            elif outcome == 'system_failure':
                self.failures += 1
                if self.failures >= self.threshold:
                    self._open()
            # Business rejection leaves the closed-state counter unchanged.
            return True


def denied(fn):
    try:
        fn()
    except Blocked:
        return
    raise AssertionError('expected blocking')


def checks():
    now = [0]
    b = Breaker(lambda: now[0]); count = 0
    b.finish(b.admit(100), 'system_failure')
    assert b.state == 'closed' and b.failures == 1; count += 1
    b.finish(b.admit(100), 'business_rejection')
    assert b.failures == 1 and b.state == 'closed'; count += 1
    b.finish(b.admit(100), 'success')
    assert b.failures == 0; count += 1
    old = b.admit(100)
    for _ in range(2): b.finish(b.admit(100), 'system_failure')
    assert b.state == 'open'; count += 1
    sequence = b.sequence
    denied(lambda: b.admit(100))
    assert b.sequence == sequence; count += 1
    assert b.finish(old, 'success') is False and b.state == 'open'; count += 1
    now[0] = 9.999; denied(lambda: b.admit(100)); count += 1
    now[0] = 10; probe = b.admit(100)
    assert probe.probe and b.state == 'half_open'
    denied(lambda: b.admit(100)); count += 1
    b.finish(probe, 'system_failure')
    assert b.state == 'open' and b.until == 20; count += 1
    now[0] = 20; probe = b.admit(100); b.finish(probe, 'business_rejection')
    assert b.state == 'open' and b.until == 30; count += 1
    now[0] = 30; probe = b.admit(100); b.finish(probe, 'success')
    assert b.state == 'closed' and b.failures == 0; count += 1
    try:
        b.finish(probe, 'system_failure')
    except ValueError:
        assert b.state == 'closed'; count += 1
    else:
        raise AssertionError('duplicate completion accepted')
    denied(lambda: b.admit(30)); assert b.state == 'closed'; count += 1
    for _ in range(2): b.finish(b.admit(100), 'system_failure')
    assert b.state == 'open'
    other = Breaker(lambda: now[0])
    assert other.admit(100).probe is False; count += 1
    b = Breaker(lambda: now[0])
    for _ in range(2): b.finish(b.admit(100), 'system_failure')
    now[0] = 40; barrier = Barrier(2); outcomes = []
    def attempt():
        barrier.wait()
        try:
            b.admit(100)
        except Blocked:
            outcomes.append('blocked')
        else:
            outcomes.append('probe')
    threads = [Thread(target=attempt) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sorted(outcomes) == ['blocked', 'probe']; count += 1
    print(f'{count} circuit-breaker checks passed')


if __name__ == '__main__':
    checks()
