"""Original Pydantic contract checks. No LLM, HTTP, or real business data."""
import json
from datetime import date
from typing import Annotated, Literal, Self
import pydantic
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, field_validator, model_validator


class Point(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    crs: Literal['GCJ-02']


class InsightQuery(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)
    schema_version: Literal['insight-query.v1']
    poi_id: str = Field(pattern=r'^POI-[0-9]{3}$')
    population_type: Annotated[StrictInt, Field(ge=1, le=4)]
    metric: Literal['visitor_count', 'repeat_visit_ratio']
    start_date: str = Field(pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
    end_date: str = Field(pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
    center: Point

    @field_validator('start_date', 'end_date')
    @classmethod
    def valid_calendar_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

    @model_validator(mode='after')
    def valid_window(self) -> Self:
        days = (date.fromisoformat(self.end_date) - date.fromisoformat(self.start_date)).days + 1
        if not 1 <= days <= 90:
            raise ValueError('inclusive date window must be 1..90 days')
        return self


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('nonstandard JSON constant')


def validate_command(raw: str, allowed_pois: frozenset[str]) -> InsightQuery:
    # The server derives allowed_pois from authentication, never from model input.
    if len(raw.encode('utf-8')) > 4096:
        raise ValueError('payload too large')
    data = json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    command = InsightQuery.model_validate(data)
    if command.poi_id not in allowed_pois:
        raise PermissionError('POI outside authenticated scope')
    return command


def checks():
    good = {'schema_version': 'insight-query.v1', 'poi_id': 'POI-001',
            'population_type': 4, 'metric': 'visitor_count',
            'start_date': '2026-09-01', 'end_date': '2026-09-30',
            'center': {'lng': 116.4, 'lat': 39.9, 'crs': 'GCJ-02'}}
    allowed = frozenset({'POI-001'})
    cmd = validate_command(json.dumps(good), allowed)
    assert cmd.population_type == 4 and cmd.center.crs == 'GCJ-02'
    count = 1
    invalid = [
        dict(good, population_type='4'),
        dict(good, population_type=True),
        dict(good, population_type=4.0),
        dict(good, population_type=None),
        dict(good, population_type=5),
        dict(good, tenant_id='pretend-admin'),
        {k: v for k, v in good.items() if k != 'metric'},
        dict(good, metric='execute_sql'),
        dict(good, schema_version='insight-query.v2'),
        dict(good, start_date='2026-02-30'),
        dict(good, start_date='2026-10-01'),
        dict(good, start_date='2026-01-01'),
        dict(good, center=dict(good['center'], crs='BD-09')),
        dict(good, center=dict(good['center'], lat=91)),
        dict(good, center=dict(good['center'], lng=float('nan'))),
        dict(good, poi_id='POI-002'),
    ]
    raws = [json.dumps(item) for item in invalid]
    raws += ['{"poi_id":"POI-001","poi_id":"POI-002"}',
             json.dumps(good)[:-1], ' ' * 4097, '[]']
    for raw in raws:
        try:
            validate_command(raw, allowed)
        except (ValueError, PermissionError):
            count += 1
        else:
            raise AssertionError('invalid input accepted')
    try:
        cmd.center.lat = 20
    except ValidationError:
        count += 1
    else:
        raise AssertionError('nested command mutable')
    schema = InsightQuery.model_json_schema()
    assert schema['additionalProperties'] is False
    assert schema['$defs']['Point']['additionalProperties'] is False
    assert schema['properties']['population_type']['maximum'] == 4
    # The inclusive date-window rule is application code, not in generated schema.
    assert 'valid_window' not in json.dumps(schema)
    count += 1
    print(f'{count} structured-output checks passed; pydantic={pydantic.__version__}')


if __name__ == '__main__':
    checks()
