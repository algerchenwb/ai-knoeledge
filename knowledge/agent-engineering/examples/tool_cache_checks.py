"""Original single-thread teaching cache, no external calls or cachetools dependency."""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Context:
    tenant: str
    subject: str
    permission_revision: int
    allowed_pois: tuple[str, ...]


@dataclass(frozen=True)
class Query:
    poi: str = 'POI-001'
    tool_version: str = 'insight.v1'
    metric: str = 'visitor_count'
    population_type: int = 4
    start: str = '2026-09-01'
    end: str = '2026-09-30'
    crs: str = 'GCJ-02'
    unit: str = 'people'
    data_version: str = 'snapshot-1'


class Cache:
    def __init__(self, clock, capacity=2):
        if capacity < 1:
            raise ValueError('capacity must be positive')
        self.clock, self.capacity = clock, capacity
        self.items = OrderedDict()

    @staticmethod
    def key(context, query):
        # context comes from server authentication, not the model.
        if query.poi not in context.allowed_pois:
            raise PermissionError('outside current scope')
        return context, query

    def expire(self):
        now = self.clock()
        for key, (deadline, _) in list(self.items.items()):
            if now >= deadline:
                del self.items[key]

    def put(self, context, query, result):
        key = self.key(context, query)
        ttl = {'ok': 10, 'not_found': 2}.get(result.get('status'))
        if ttl is None:
            raise ValueError('only confirmed ok/not_found results are cacheable')
        self.expire()
        self.items[key] = (self.clock() + ttl, deepcopy(result))
        self.items.move_to_end(key)
        while len(self.items) > self.capacity:
            self.items.popitem(last=False)

    def get(self, context, query):
        key = self.key(context, query)  # Check authorization even for cache hits.
        self.expire()
        if key not in self.items:
            return None
        _, result = self.items[key]
        self.items.move_to_end(key)
        return deepcopy(result)

    def invalidate(self, context, query):
        self.items.pop(self.key(context, query), None)


def checks():
    now = [0]
    ctx = Context('tenant-a', 'user-a', 1, ('POI-001',))
    query = Query()
    cache = Cache(lambda: now[0])
    result = {'status': 'ok', 'value': {'count': 12}, 'source_as_of': '2026-09-30'}
    cache.put(ctx, query, result)
    assert cache.get(ctx, query)['value']['count'] == 12
    count = 1
    result['value']['count'] = 99
    cached = cache.get(ctx, query); cached['value']['count'] = 88
    assert cache.get(ctx, query)['value']['count'] == 12
    count += 1
    for context in [replace(ctx, tenant='tenant-b'), replace(ctx, subject='user-b'),
                    replace(ctx, permission_revision=2)]:
        assert cache.get(context, query) is None
        count += 1
    try:
        cache.get(replace(ctx, allowed_pois=()), query)
    except PermissionError:
        count += 1
    else:
        raise AssertionError('revoked permission served cached data')
    variants = {'tool_version': 'insight.v2', 'metric': 'repeat_visit_ratio',
                'population_type': 1, 'start': '2026-09-02', 'end': '2026-09-29',
                'crs': 'BD-09', 'unit': 'thousand_people', 'data_version': 'snapshot-2'}
    for field, value in variants.items():
        assert cache.get(ctx, replace(query, **{field: value})) is None
        count += 1
    now[0] = 9.999
    assert cache.get(ctx, query) is not None
    now[0] = 10
    assert cache.get(ctx, query) is None and not cache.items
    count += 1
    cache.put(ctx, query, {'status': 'not_found'})
    now[0] = 11.999; assert cache.get(ctx, query)['status'] == 'not_found'
    now[0] = 12; assert cache.get(ctx, query) is None
    count += 1
    for status in ['timeout', 'permission_denied', 'partial']:
        try:
            cache.put(ctx, query, {'status': status})
        except ValueError:
            assert cache.get(ctx, query) is None
            count += 1
        else:
            raise AssertionError('uncertain/error result cached')
    q2 = replace(query, data_version='snapshot-2')
    q3 = replace(query, data_version='snapshot-3')
    cache.put(ctx, query, result); cache.put(ctx, q2, result)
    cache.get(ctx, query); cache.put(ctx, q3, result)
    assert cache.get(ctx, q2) is None and cache.get(ctx, query) is not None
    assert len(cache.items) == 2
    count += 1
    cache.invalidate(ctx, query)
    assert cache.get(ctx, query) is None
    count += 1
    print(f'{count} tool-cache checks passed')


if __name__ == '__main__':
    checks()
