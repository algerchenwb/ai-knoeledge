"""Original deterministic fixture evaluation; no real Agent or agentevals execution."""
from copy import deepcopy

EXPECTED = {'poi': 'POI-001', 'month': '2026-09', 'population_type': 4}


def evaluate(run, allow_partial=False):
    errors = set()
    calls = run['calls']
    if len(calls) > 4:
        errors.add('attempt_budget')
    resolved = False
    evidence = {}
    versions = set()
    for call in calls:
        tool = call['tool']
        if tool not in {'resolve_poi', 'traffic', 'profile'}:
            errors.add('forbidden_tool')
            continue
        if tool == 'resolve_poi':
            if call['status'] == 'ok' and call['value'] == 'POI-001':
                resolved = True
            continue
        if not resolved:
            errors.add('dependency_order')
        if call['args'] != EXPECTED or type(call['args'].get('population_type')) is not int:
            errors.add('query_contract')
            continue
        if call['status'] == 'ok':
            if tool in evidence and evidence[tool] != call['value']:
                errors.add('conflicting_receipt')
            evidence[tool] = call['value']
            if not call['version']:
                errors.add('missing_version')
            versions.add(call['version'])
    if len(versions) > 1:
        errors.add('mixed_snapshot')
    report = run['report']
    missing = sorted({'traffic', 'profile'} - evidence.keys())
    if sorted(report['missing']) != missing:
        errors.add('missing_disclosure')
    expected_status = 'partial' if missing else 'complete'
    if report['status'] != expected_status:
        errors.add('completion_claim')
    for tool, field in [('traffic', 'count'), ('profile', 'ratio')]:
        expected = evidence.get(tool)
        if report[field] != expected or (expected is not None and type(report[field]) is not type(expected)):
            errors.add('unsupported_value')
    complete = not missing and not errors
    return {'errors': sorted(errors), 'complete': complete,
            'acceptable': not errors and (complete or allow_partial)}


def baseline():
    return {'calls': [
        {'tool': 'resolve_poi', 'args': {'name': 'demo'}, 'status': 'ok', 'value': 'POI-001', 'version': None},
        {'tool': 'traffic', 'args': dict(EXPECTED), 'status': 'ok', 'value': 12, 'version': 'snapshot-1'},
        {'tool': 'profile', 'args': dict(EXPECTED), 'status': 'ok', 'value': 0.25, 'version': 'snapshot-1'},
    ], 'report': {'status': 'complete', 'count': 12, 'ratio': 0.25, 'missing': []}}


def checks():
    base = baseline(); count = 0
    assert evaluate(base)['complete']; count += 1
    run = deepcopy(base); run['calls'][1:3] = reversed(run['calls'][1:3])
    assert evaluate(run)['complete']; count += 1
    run = deepcopy(base); run['calls'][0:2] = reversed(run['calls'][0:2])
    assert 'dependency_order' in evaluate(run)['errors']; count += 1
    for field, value in [('poi', 'POI-002'), ('month', '2026-08'), ('population_type', 1),
                         ('population_type', '4'), ('population_type', 4.0)]:
        run = deepcopy(base); run['calls'][1]['args'][field] = value
        assert 'query_contract' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); run['calls'][2]['version'] = 'snapshot-2'
    assert 'mixed_snapshot' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); run['calls'][2]['version'] = None
    assert 'missing_version' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); run['report']['count'] = 120
    assert 'unsupported_value' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); run['calls'][2]['status'] = 'timeout'
    assert {'unsupported_value', 'completion_claim', 'missing_disclosure'} <= set(evaluate(run)['errors'])
    count += 1
    run['report'].update(status='partial', ratio=None, missing=['profile'])
    assert not evaluate(run)['acceptable'] and not evaluate(run)['complete']; count += 1
    assert evaluate(run, allow_partial=True)['acceptable'] and not evaluate(run, allow_partial=True)['complete']
    count += 1
    run = deepcopy(base); retry = deepcopy(run['calls'][1]); retry.update(status='timeout', value=None)
    run['calls'].insert(1, retry)
    assert evaluate(run)['complete']; count += 1
    run['calls'].insert(1, retry)
    assert 'attempt_budget' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); run['calls'].append({'tool': 'send_report'})
    assert 'forbidden_tool' in evaluate(run)['errors']; count += 1
    run = deepcopy(base); conflict = deepcopy(run['calls'][1]); conflict['value'] = 13
    run['calls'].append(conflict)
    assert 'conflicting_receipt' in evaluate(run)['errors']; count += 1
    print(f'{count} Agent acceptance checks passed')


if __name__ == '__main__':
    checks()
