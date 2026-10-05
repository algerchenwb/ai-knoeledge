"""Synthetic ordered user funnel with complete follow-up windows. No AI model."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Event:
    tenant: str
    event_id: str
    user_id: str
    name: str
    at: str


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC timestamp required")
    return parsed


def rate(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "ratio": numerator / denominator if denominator else None}


def analyze(events, tenant, cohort_start, cohort_end, as_of, coverage_start, coverage_end,
            data_version, window_days=7):
    start, end, cutoff = map(timestamp, (cohort_start, cohort_end, as_of))
    if not tenant or not data_version or not start < end <= cutoff:
        raise ValueError("invalid cohort or scope")
    if type(window_days) is not int or not 1 <= window_days <= 30:
        raise ValueError("invalid follow-up window")
    if timestamp(coverage_start) > start or timestamp(coverage_end) < cutoff:
        raise ValueError("event coverage incomplete")
    # Tenant selected by trusted service. Dedupe before sequence matching.
    unique = {}
    for event in events:
        if event.tenant != tenant:
            continue
        if not event.event_id or not event.user_id or event.name not in {"signup", "query_succeeded", "report_saved"}:
            raise ValueError("invalid event identity or type")
        timestamp(event.at)
        if event.event_id in unique and unique[event.event_id] != event:
            raise ValueError("conflicting duplicate event id")
        unique[event.event_id] = event
    users = {}
    for event in unique.values():
        at = timestamp(event.at)
        if at < cutoff:
            users.setdefault(event.user_id, []).append((at, event.name))
    entrants = eligible = pending = queried = activated = 0
    for timeline in users.values():
        timeline.sort()
        signups = [at for at, name in timeline if name == "signup" and start <= at < end]
        if not signups:
            continue
        entrants += 1
        entered = min(signups)  # First signup within cohort, not lifetime-first signup.
        deadline = entered + timedelta(days=window_days)
        if deadline > cutoff:
            pending += 1
            continue
        eligible += 1
        queries = [at for at, name in timeline if name == "query_succeeded" and entered < at < deadline]
        if not queries:
            continue
        queried += 1
        first_query = min(queries)
        if any(name == "report_saved" and first_query < at < deadline for at, name in timeline):
            activated += 1
    return {"status": "observed" if eligible else "no_mature_sample", "tenant": tenant,
            "definition_version": "ordered-user-activation-1", "data_version": data_version,
            "cohort": [cohort_start, cohort_end], "as_of": as_of, "window_days": window_days,
            "entrants": entrants, "eligible": eligible, "pending": pending,
            "queried": queried, "activated": activated,
            "signup_to_query": rate(queried, eligible),
            "query_to_report": rate(activated, queried),
            "signup_to_report": rate(activated, eligible)}


def fixtures():
    rows = [("a", "s1", "u1", "signup", "2026-09-01T00:00:00Z"),
            ("a", "q1", "u1", "query_succeeded", "2026-09-02T00:00:00Z"),
            ("a", "r1", "u1", "report_saved", "2026-09-03T00:00:00Z"),
            ("a", "s2", "u2", "signup", "2026-09-02T00:00:00Z"),
            ("a", "q2", "u2", "query_succeeded", "2026-09-03T00:00:00Z"),
            ("a", "s3", "u3", "signup", "2026-09-03T00:00:00Z"),
            ("a", "r3", "u3", "report_saved", "2026-09-03T01:00:00Z"),
            ("a", "q3", "u3", "query_succeeded", "2026-09-04T00:00:00Z"),
            ("a", "s4", "u4", "signup", "2026-09-05T00:00:00Z")]
    events = [Event(*row) for row in rows]
    options = dict(tenant="a", cohort_start="2026-09-01T00:00:00Z", cohort_end="2026-09-06T00:00:00Z",
                   as_of="2026-09-10T00:00:00Z", coverage_start="2026-09-01T00:00:00Z",
                   coverage_end="2026-09-10T00:00:00Z", data_version="events-demo-1")
    return events, options


def examples():
    events, options = fixtures()
    return {"base": analyze(events, **options), "duplicate_delivery": analyze(events + events[:3], **options),
            "no_mature_sample": analyze([events[-1]], **options)}


if __name__ == "__main__":
    import json
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
