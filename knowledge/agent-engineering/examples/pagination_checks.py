"""Original in-memory cursor/snapshot teaching example, not Kubernetes code."""
from dataclasses import dataclass, replace
from uuid import uuid4


@dataclass(frozen=True)
class Context:
    tenant: str
    subject: str
    policy_version: int = 1
    can_read: bool = True


@dataclass(frozen=True)
class Query:
    metric: str = 'visitor_count'
    population_type: int = 4
    month: str = '2026-09'


@dataclass(frozen=True)
class Row:
    id: str
    value: int


class Pager:
    def __init__(self, clock):
        self.clock = clock
        self.live = [Row(str(i), i * 10) for i in range(5)]
        self.snapshots, self.cursors, self.positions = {}, {}, {}

    def page(self, context, query, cursor=None):
        if not context.can_read:
            raise PermissionError('current permission revoked')
        if cursor is None:
            sid, offset = uuid4().hex, 0
            self.snapshots[sid] = (context, query, tuple(self.live), self.clock() + 10)
        else:
            sid, offset = self.cursors[cursor]  # Unknown cursor is rejected, not restarted.
        original_context, original_query, rows, deadline = self.snapshots[sid]
        if context != original_context or query != original_query:
            raise PermissionError('cursor context/query mismatch')
        if self.clock() >= deadline:
            raise TimeoutError('snapshot lease expired')
        items = rows[offset:offset + 2]
        next_offset = offset + len(items)
        token = None
        if next_offset < len(rows):
            position = (sid, next_offset)
            if position not in self.positions:
                token = uuid4().hex
                self.positions[position] = token
                self.cursors[token] = position
            token = self.positions[position]
        return {'items': items, 'next': token, 'snapshot': sid}


def collect(fetch, max_pages=10):
    rows, ids, seen, snapshot, cursor = [], set(), set(), None, None
    for _ in range(max_pages):
        page = fetch(cursor)
        if snapshot is None:
            snapshot = page['snapshot']
        if page['snapshot'] != snapshot:
            raise ValueError('snapshot changed')
        for row in page['items']:
            if row.id in ids:
                raise ValueError('duplicate entity within snapshot')
            ids.add(row.id); rows.append(row)
        cursor = page['next']
        if cursor is None:
            return {'status': 'complete', 'items': rows, 'snapshot': snapshot}
        if cursor in seen:
            raise ValueError('cursor cycle')
        seen.add(cursor)
    return {'status': 'partial', 'reason': 'page_budget', 'items': rows,
            'snapshot': snapshot, 'next': cursor}


def rejected(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError('expected rejection')


def checks():
    now = [0]; pager = Pager(lambda: now[0]); ctx = Context('tenant-a', 'user-a'); q = Query()
    first = pager.page(ctx, q); count = 0
    pager.live[:] = [Row('new', 999)]  # Live insert/update/delete cannot alter captured rows.
    second = pager.page(ctx, q, first['next'])
    third = pager.page(ctx, q, second['next'])
    assert [r.id for page in (first, second, third) for r in page['items']] == list('01234')
    assert first['snapshot'] == second['snapshot'] == third['snapshot']
    assert third['next'] is None; count += 1
    assert pager.page(ctx, q, first['next']) == second; count += 1
    assert pager.page(ctx, q)['items'] == (Row('new', 999),); count += 1
    for changed in [replace(ctx, tenant='tenant-b'), replace(ctx, subject='user-b'),
                    replace(ctx, policy_version=2), replace(ctx, can_read=False)]:
        rejected(PermissionError, lambda: pager.page(changed, q, first['next']))
        count += 1
    rejected(PermissionError, lambda: pager.page(ctx, replace(q, month='2026-08'), first['next']))
    count += 1
    rejected(KeyError, lambda: pager.page(ctx, q, 'invented-cursor')); count += 1
    now[0] = 10
    rejected(TimeoutError, lambda: pager.page(ctx, q, first['next'])); count += 1
    pager = Pager(lambda: now[0])
    result = collect(lambda cursor: pager.page(ctx, q, cursor))
    assert result['status'] == 'complete' and len(result['items']) == 5; count += 1
    result = collect(lambda cursor: pager.page(ctx, q, cursor), max_pages=1)
    assert result['status'] == 'partial' and len(result['items']) == 2 and result['next']; count += 1
    def empty_middle(cursor):
        return {'snapshot': 's', 'items': [] if cursor is None else [Row('a', 1)],
                'next': 'after-empty' if cursor is None else None}
    assert len(collect(empty_middle)['items']) == 1; count += 1
    rejected(ValueError, lambda: collect(lambda cursor: {'snapshot': 's', 'items': [], 'next': 'loop'}))
    count += 1
    rejected(ValueError, lambda: collect(lambda cursor: {'snapshot': 's' if cursor is None else 'new',
                                                         'items': [], 'next': 'next'}))
    count += 1
    rejected(ValueError, lambda: collect(lambda cursor: {'snapshot': 's', 'items': [Row('same', 1)],
                                                         'next': 'next' if cursor is None else None}))
    count += 1
    print(f'{count} pagination checks passed')


if __name__ == '__main__':
    checks()
