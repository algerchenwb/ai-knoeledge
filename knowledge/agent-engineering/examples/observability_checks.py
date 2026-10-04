"""Original in-memory tracing/aggregation checks; not an OpenTelemetry SDK."""
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from uuid import uuid4

active = ContextVar('active_span', default=None)


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_id: str | None
    status: str = 'unset'
    ended: bool = False
    attrs: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    def attribute(self, key, value):
        if self.ended:
            return
        if key == 'business.outcome' and value in {'complete', 'partial', 'failed'}:
            self.attrs[key] = value
        elif key == 'tool.name' and value in {'traffic', 'profile'}:
            self.attrs[key] = value

    def record_exception(self, exc):
        if not self.ended:
            self.events.append({'name': 'exception', 'type': type(exc).__name__})

    def set_status(self, value):
        if self.ended or self.status == 'ok':
            return
        if value in {'error', 'ok'}:
            self.status = value


class Tracer:
    def __init__(self):
        self.spans = []

    @contextmanager
    def start(self, name):
        parent = active.get()
        span = Span(name, parent.trace_id if parent else uuid4().hex,
                    uuid4().hex[:16], parent.span_id if parent else None)
        self.spans.append(span)
        token = active.set(span)
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status('error')
            raise
        finally:
            span.ended = True
            active.reset(token)


def aggregate(attempts, cache_hits):
    operations = {}
    known_cost = 0
    unknown_cost = 0
    for attempt in attempts:
        operations.setdefault(attempt['operation'], []).append(attempt['success'])
        if attempt['cost'] is None:
            unknown_cost += 1
        else:
            known_cost += attempt['cost']
    return {'attempts': len(attempts), 'attempt_successes': sum(a['success'] for a in attempts),
            'operations': len(operations), 'operation_successes': sum(any(v) for v in operations.values()),
            'known_cost_units': known_cost, 'unknown_cost_attempts': unknown_cost,
            'cache_hits': cache_hits}


def checks():
    t = Tracer(); count = 0
    with t.start('report') as root:
        with t.start('tool.operation') as operation:
            try:
                with t.start('tool.attempt') as failed:
                    raise TimeoutError('secret token must not be logged')
            except TimeoutError:
                pass
            assert active.get() is operation; count += 1
            with t.start('tool.attempt') as retry:
                retry.attribute('tool.name', 'traffic')
            assert failed.span_id != retry.span_id and failed.parent_id == retry.parent_id; count += 1
        assert operation.parent_id == root.span_id and failed.trace_id == root.trace_id; count += 1
        assert failed.status == 'error' and retry.status == 'unset'; count += 1
        assert failed.events == [{'name': 'exception', 'type': 'TimeoutError'}]; count += 1
        root.attribute('business.outcome', 'partial')
        assert root.status == 'unset' and root.attrs['business.outcome'] == 'partial'; count += 1
        root.attribute('access_token', 'secret'); root.attribute('tool.name', 'secret-in-name')
        assert 'access_token' not in root.attrs and 'tool.name' not in root.attrs; count += 1
        parent_id = root.span_id
        ctx = copy_context()
        def detached_work():
            with t.start('queued.step') as child:
                return child.parent_id
        assert ctx.run(detached_work) == parent_id; count += 1
    assert active.get() is None and all(s.ended for s in t.spans); count += 1
    root.attribute('business.outcome', 'complete')
    assert root.attrs['business.outcome'] == 'partial'; count += 1
    with t.start('next.request') as other:
        assert other.parent_id is None and other.trace_id != root.trace_id; count += 1
    with t.start('status.demo') as status:
        status.record_exception(ValueError('private input'))
        assert status.status == 'unset'
        status.set_status('error'); status.set_status('ok'); status.set_status('error')
        assert status.status == 'ok'; count += 1
    result = aggregate([
        {'operation': 'A', 'success': False, 'cost': None},
        {'operation': 'A', 'success': True, 'cost': 3},
        {'operation': 'B', 'success': True, 'cost': 2},
        {'operation': 'C', 'success': False, 'cost': None},
    ], cache_hits=1)
    assert result == {'attempts': 4, 'attempt_successes': 2, 'operations': 3,
                      'operation_successes': 2, 'known_cost_units': 5,
                      'unknown_cost_attempts': 2, 'cache_hits': 1}; count += 1
    print(f'{count} observability checks passed')
    print(result)


if __name__ == '__main__':
    checks()
