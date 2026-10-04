"""Independent teaching ledger; no provider pricing or distributed guarantees."""
from threading import Lock, Barrier, Thread


class Denied(Exception):
    pass


class Ledger:
    def __init__(self, limit=100, attempts=3, concurrency=2):
        self.limit, self.max_attempts, self.concurrency = limit, attempts, concurrency
        self.spent = self.attempts = 0
        self.open = {}
        self.closed = {}
        self.lock = Lock()

    def reserve(self, key, estimate):
        if not isinstance(estimate, int) or isinstance(estimate, bool) or estimate < 0:
            raise ValueError('estimate must be a nonnegative integer')
        with self.lock:
            if key in self.open or key in self.closed:
                raise Denied('duplicate attempt identity')
            if self.attempts >= self.max_attempts:
                raise Denied('attempt limit')
            if sum(v['active'] for v in self.open.values()) >= self.concurrency:
                raise Denied('concurrency limit')
            if self.spent + sum(v['estimate'] for v in self.open.values()) + estimate > self.limit:
                raise Denied('budget limit')
            self.open[key] = {'estimate': estimate, 'active': True}
            self.attempts += 1

    def settle(self, key, actual):
        if actual is not None and (not isinstance(actual, int) or isinstance(actual, bool) or actual < 0):
            raise ValueError('actual must be a nonnegative integer or None')
        with self.lock:
            if key in self.closed:
                if self.closed[key] != actual:
                    raise ValueError('conflicting receipt')
                return
            reservation = self.open[key]
            if actual is None:
                reservation['active'] = False
                return  # Request ended, but unknown spending still occupies budget.
            self.spent += actual
            del self.open[key]
            self.closed[key] = actual


def rejected(fn):
    try:
        fn()
    except Denied:
        return
    raise AssertionError('expected admission rejection')


def checks():
    count = 0
    b = Ledger(); b.reserve('a', 100); b.settle('a', 100)
    rejected(lambda: b.reserve('b', 1)); count += 1

    b = Ledger(); b.reserve('a', 80); b.settle('a', 20); b.reserve('b', 80)
    assert b.spent == 20; count += 1

    b = Ledger(); b.reserve('a', 60); b.settle('a', None)
    rejected(lambda: b.reserve('b', 50))
    assert b.spent == 0 and b.open['a']['estimate'] == 60
    b.settle('a', 30); b.reserve('b', 70); count += 1

    b = Ledger(); b.reserve('a', 40); b.settle('a', 120)
    assert b.spent == 120
    rejected(lambda: b.reserve('b', 0)); count += 1

    b = Ledger(); b.reserve('a', 20); b.settle('a', 10); b.settle('a', 10)
    assert b.spent == 10
    try:
        b.settle('a', 11)
    except ValueError:
        pass
    else:
        raise AssertionError('conflicting receipt accepted')
    count += 1

    b = Ledger(attempts=2)
    for key in ('child-first', 'child-retry'):
        b.reserve(key, 10); b.settle(key, 5)
    rejected(lambda: b.reserve('other-child', 10))
    assert b.attempts == 2 and b.spent == 10; count += 1

    b = Ledger(concurrency=1); b.reserve('a', 10)
    rejected(lambda: b.reserve('b', 10)); b.settle('a', None)
    b.reserve('b', 10); count += 1

    b = Ledger(); b.reserve('a', 10)
    rejected(lambda: b.reserve('a', 10)); assert b.attempts == 1; count += 1

    b = Ledger(); barrier = Barrier(2); outcomes = []
    def contender(key):
        barrier.wait()
        try:
            b.reserve(key, 60)
        except Denied:
            outcomes.append('denied')
        else:
            outcomes.append('accepted')
    workers = [Thread(target=contender, args=(str(i),)) for i in range(2)]
    for worker in workers: worker.start()
    for worker in workers: worker.join()
    assert sorted(outcomes) == ['accepted', 'denied']
    assert b.attempts == 1 and sum(v['estimate'] for v in b.open.values()) == 60
    count += 1
    print(f'{count} budget checks passed')


if __name__ == '__main__':
    checks()
