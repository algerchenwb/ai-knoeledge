"""Original token-bucket admission model; fake time, no sleeping or external calls."""
from dataclasses import dataclass
from fractions import Fraction
from threading import Barrier, Lock, Thread


@dataclass
class Bucket:
    capacity: int
    rate: Fraction
    tokens: Fraction
    last: Fraction

    def refill(self, now):
        if now < self.last:
            raise ValueError('time moved backward')
        self.tokens = min(Fraction(self.capacity), self.tokens + (now - self.last) * self.rate)
        self.last = now

    def ready(self, now, amount):
        return now + max(Fraction(0), Fraction(amount) - self.tokens) / self.rate


class Gate:
    def __init__(self, global_capacity=2, tenant_capacity=1, rate=1):
        if global_capacity < 1 or tenant_capacity < 1 or rate <= 0:
            raise ValueError('positive capacity and rate required')
        self.global_bucket = Bucket(global_capacity, Fraction(rate), Fraction(global_capacity), Fraction(0))
        self.tenant_capacity, self.rate = tenant_capacity, Fraction(rate)
        self.tenants = {}
        self.not_before = Fraction(0)
        self.lock = Lock()

    def backoff_until(self, value):
        with self.lock:
            self.not_before = max(self.not_before, Fraction(value))

    def offer(self, tenant, now, deadline, amount=1):
        if type(amount) is not int or not 1 <= amount <= min(self.global_bucket.capacity, self.tenant_capacity):
            raise ValueError('weight must be a positive integer within both capacities')
        now, deadline = Fraction(now), Fraction(deadline)
        with self.lock:
            global_bucket = self.global_bucket
            global_bucket.refill(now)
            if now >= deadline:
                return {'status': 'rejected', 'reason': 'deadline'}
            bucket = self.tenants.setdefault(tenant, Bucket(self.tenant_capacity, self.rate,
                                                          Fraction(self.tenant_capacity), now))
            bucket.refill(now)
            ready = max(global_bucket.ready(now, amount), bucket.ready(now, amount), self.not_before)
            if ready >= deadline:
                return {'status': 'rejected', 'reason': 'deadline'}
            if ready > now:
                return {'status': 'wait', 'not_before': ready}
            global_bucket.tokens -= amount
            bucket.tokens -= amount
            return {'status': 'admitted'}


def checks():
    count = 0
    gate = Gate(tenant_capacity=2)
    assert gate.offer('a', 0, 10)['status'] == 'admitted'
    assert gate.offer('a', 0, 10)['status'] == 'admitted'
    assert gate.offer('a', 0, 10) == {'status': 'wait', 'not_before': Fraction(1)}; count += 1
    assert gate.offer('a', Fraction(1, 2), 10) == {'status': 'wait', 'not_before': Fraction(1)}; count += 1
    assert gate.offer('a', 1, 10)['status'] == 'admitted'; count += 1
    gate = Gate()
    gate.offer('a', 0, 10)
    assert gate.offer('a', 0, 10)['status'] == 'wait'
    assert gate.global_bucket.tokens == 1
    assert gate.offer('b', 0, 10)['status'] == 'admitted'; count += 1
    assert gate.offer('c', 0, 10) == {'status': 'wait', 'not_before': Fraction(1)}; count += 1
    assert gate.offer('c', 0, 1) == {'status': 'rejected', 'reason': 'deadline'}; count += 1
    fresh = Gate()
    assert fresh.offer('a', 0, 0)['status'] == 'rejected' and fresh.global_bucket.tokens == 2; count += 1
    gate = Gate(); gate.backoff_until(5); gate.backoff_until(2)
    assert gate.offer('a', 0, 10) == {'status': 'wait', 'not_before': Fraction(5)}
    assert gate.global_bucket.tokens == 2; count += 1
    assert gate.offer('a', 5, 10)['status'] == 'admitted'; count += 1
    gate.offer('b', 100, 110)
    assert gate.global_bucket.tokens == 1; count += 1
    try:
        gate.offer('a', 99, 110)
    except ValueError:
        count += 1
    else:
        raise AssertionError('backward time accepted')
    for weight in [0, -1, 3, True, 1.0]:
        try:
            Gate().offer('a', 0, 10, weight)
        except ValueError:
            count += 1
        else:
            raise AssertionError('invalid weight accepted')
    gate = Gate(global_capacity=4, tenant_capacity=4)
    gate.offer('a', 0, 10, 3)
    assert gate.offer('a', 0, 10, 2) == {'status': 'wait', 'not_before': Fraction(1)}; count += 1
    gate = Gate(global_capacity=1); barrier = Barrier(2); outcomes = []
    def attempt(tenant):
        barrier.wait()
        outcomes.append(gate.offer(tenant, 0, 10)['status'])
    threads = [Thread(target=attempt, args=(tenant,)) for tenant in ('a', 'b')]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sorted(outcomes) == ['admitted', 'wait']; count += 1
    print(f'{count} rate-limit checks passed')


if __name__ == '__main__':
    checks()
