"""Independent synthetic unit ledger; no pricing, payment or upstream integration."""
import sqlite3


def units(value):
    if type(value) is not int or value < 0:
        raise ValueError('units must be a nonnegative integer')
    return value


def key(value):
    if not isinstance(value, str) or not value or len(value) > 100:
        raise ValueError('invalid identifier')
    return value


class Ledger:
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS budgets (tenant TEXT, period TEXT, quota INTEGER NOT NULL, PRIMARY KEY(tenant,period))')
        self.db.execute('CREATE TABLE IF NOT EXISTS requests (tenant TEXT, period TEXT, request TEXT, fingerprint TEXT NOT NULL, reserved INTEGER NOT NULL, state TEXT NOT NULL, actual INTEGER, PRIMARY KEY(tenant,period,request))')

    def close(self):
        self.db.close()

    def transaction(self, operation):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            result = operation()
            self.db.execute('COMMIT')
            return result
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def configure(self, tenant, period, quota):
        tenant, period, quota = key(tenant), key(period), units(quota)
        def run():
            old = self.db.execute('SELECT quota FROM budgets WHERE tenant=? AND period=?', (tenant, period)).fetchone()
            if old and old[0] != quota:
                raise ValueError('immutable quota; use an audited policy-change workflow')
            self.db.execute('INSERT OR IGNORE INTO budgets VALUES (?,?,?)', (tenant, period, quota))
        self.transaction(run)

    def balance(self, tenant, period):
        tenant, period = key(tenant), key(period)
        budget = self.db.execute('SELECT quota FROM budgets WHERE tenant=? AND period=?', (tenant, period)).fetchone()
        if budget is None:
            raise ValueError('unknown budget')
        # One statement gives a coherent snapshot for all three totals.
        held, used = self.db.execute("SELECT COALESCE(SUM(CASE WHEN state='held' THEN reserved ELSE 0 END),0), COALESCE(SUM(CASE WHEN state='settled' THEN actual ELSE 0 END),0) FROM requests WHERE tenant=? AND period=?", (tenant, period)).fetchone()
        return {'quota': budget[0], 'held': held, 'used': used, 'available': budget[0]-held-used}

    def reserve(self, tenant, period, request, fingerprint, amount):
        tenant, period, request, fingerprint = map(key, (tenant, period, request, fingerprint))
        amount = units(amount)
        if amount == 0:
            raise ValueError('positive reservation required')
        def run():
            old = self.db.execute('SELECT fingerprint,reserved,state,actual FROM requests WHERE tenant=? AND period=? AND request=?', (tenant, period, request)).fetchone()
            if old:
                if old[:2] != (fingerprint, amount):
                    raise ValueError('idempotency conflict')
                return {'state': old[2], 'actual': old[3], 'replayed': True}
            if self.balance(tenant, period)['available'] < amount:
                return {'state': 'denied', 'actual': None, 'replayed': False}
            self.db.execute("INSERT INTO requests VALUES (?,?,?,?,?,'held',NULL)", (tenant, period, request, fingerprint, amount))
            return {'state': 'held', 'actual': None, 'replayed': False}
        return self.transaction(run)

    def finish(self, tenant, period, request, actual=None, *, confirmed_unused=False):
        tenant, period, request = map(key, (tenant, period, request))
        if type(confirmed_unused) is not bool:
            raise ValueError('confirmation must be boolean')
        target = 'released' if confirmed_unused else 'settled'
        if confirmed_unused:
            if actual is not None:
                raise ValueError('release requires no actual usage')
        else:
            actual = units(actual)
        def run():
            old = self.db.execute('SELECT reserved,state,actual FROM requests WHERE tenant=? AND period=? AND request=?', (tenant, period, request)).fetchone()
            if old is None:
                raise ValueError('unknown request')
            reserved, state, previous = old
            if state != 'held':
                if (state, previous) != (target, actual):
                    raise ValueError('terminal-state conflict')
                return {'state': state, 'actual': previous, 'replayed': True}
            if target == 'settled' and actual > reserved:
                raise ValueError('usage exceeds enforced execution cap; needs reconciliation')
            self.db.execute('UPDATE requests SET state=?, actual=? WHERE tenant=? AND period=? AND request=?', (target, actual, tenant, period, request))
            return {'state': target, 'actual': actual, 'replayed': False}
        return self.transaction(run)


def demo():
    ledger = Ledger()
    try:
        ledger.configure('tenant-demo', '2026-10', 100)
        reserved = ledger.reserve('tenant-demo', '2026-10', 'job-1', 'synthetic-plan-v1', 40)
        during = ledger.balance('tenant-demo', '2026-10')
        settled = ledger.finish('tenant-demo', '2026-10', 'job-1', 25)
        replay = ledger.finish('tenant-demo', '2026-10', 'job-1', 25)
        ledger.reserve('tenant-demo', '2026-10', 'job-2', 'synthetic-plan-v2', 30)
        ledger.finish('tenant-demo', '2026-10', 'job-2', confirmed_unused=True)
        return {'fictional': True, 'unit': 'internal_work_unit_not_money_or_tokens', 'reserved': reserved, 'during': during, 'settled': settled, 'settlement_retry': replay, 'final': ledger.balance('tenant-demo', '2026-10')}
    finally:
        ledger.close()
