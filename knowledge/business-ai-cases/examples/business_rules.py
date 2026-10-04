"""Independent business-rule teaching examples. No model, network, real user data."""
from collections import Counter
from decimal import Decimal
import json


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def coverage(region_users, category_visitors):
    pool, visitors = set(region_users), set(category_visitors)
    matched = pool & visitors
    return {"numerator": len(matched), "denominator": len(pool),
            "ratio": ratio(len(matched), len(pool)),
            "status": "ok" if pool else "no_denominator",
            "out_of_scope": len(visitors - pool)}


def co_visit(a_users, b_users):
    a, b = set(a_users), set(b_users)
    overlap = len(a & b)
    return {"overlap": overlap, "a_to_b": ratio(overlap, len(a)),
            "b_to_a": ratio(overlap, len(b)), "jaccard": ratio(overlap, len(a | b))}


def cohort(prior_users, current_events):
    # Repeated event IDs are ingestion duplicates; conflicting values are invalid.
    events = {}
    for event_id, user in current_events:
        if event_id in events and events[event_id] != user:
            raise ValueError("conflicting event ID")
        events[event_id] = user
    counts = Counter(events.values())
    old = set(counts) & set(prior_users)
    new = set(counts) - set(prior_users)
    return {"active": len(counts), "new": len(new), "old": len(old),
            "old_share": ratio(len(old), len(counts)),
            "old_frequency": dict(sorted(Counter(counts[u] for u in old).items()))}


def matched_day_trend(current, baseline, mature):
    if not mature:
        return {"status": "provisional", "changes": {}}
    if not current or set(current) != set(baseline):
        raise ValueError("day-type mismatch")
    changes = {}
    for day_type, values in current.items():
        reference = baseline[day_type]
        if not values or not reference or any(v is None or v < 0 for v in values + reference):
            raise ValueError("missing or invalid day")
        now, before = sum(values) / len(values), sum(reference) / len(reference)
        changes[day_type] = None if before == 0 else (now - before) / before
    return {"status": "ok", "changes": changes}


def site_score(features, weights, eligible):
    if not eligible:
        return {"status": "ineligible", "score": None}
    if set(features) != set(weights) or any(v is None for v in features.values()):
        return {"status": "missing_features", "score": None}
    w = {k: Decimal(str(v)) for k, v in weights.items()}
    f = {k: Decimal(str(v)) for k, v in features.items()}
    if any(not x.is_finite() for x in list(w.values()) + list(f.values())):
        raise ValueError("non-finite value")
    if sum(w.values()) != 1 or any(x < 0 for x in w.values()) or any(x < 0 or x > 100 for x in f.values()):
        raise ValueError("invalid scale or weights")
    contributions = {k: f[k] * w[k] for k in f}
    return {"status": "ok", "score": str(sum(contributions.values())),
            "contributions": {k: str(v) for k, v in contributions.items()}}


def capability_match(required, available):
    needed, supported = set(required), set(available)
    missing = sorted(needed - supported)
    return {"status": "supported" if not missing else "gap",
            "matched": sorted(needed & supported), "missing": missing}


def ticket_route(kind, affects_many=False):
    policy = {"data_delay": ("data_operations", "normal"),
              "metric_question": ("business_support", "normal"),
              "outage": ("incident", "high")}
    team, priority = policy.get(kind, ("manual_triage", "normal"))
    if kind == "data_delay" and affects_many:
        priority = "high"
    return {"team": team, "priority": priority}


def build_report(required_claims, evidence):
    # Explicit support sets are fixtures, not an automated semantic verifier.
    sections = []
    for claim in required_claims:
        sources = sorted(s["id"] for s in evidence if claim in s["supports"])
        sections.append({"claim": claim, "sources": sources,
                         "status": "supported" if sources else "missing_evidence"})
    return {"status": "complete" if all(s["sources"] for s in sections) else "partial",
            "sections": sections}


def prewarm(targets, fetch, max_attempts=2):
    if max_attempts < 1:
        raise ValueError("invalid attempt limit")
    output = []
    for target in dict.fromkeys(tuple(t) for t in targets):
        for attempt in range(1, max_attempts + 1):
            # Only a read/cache-refresh teaching operation: no external business write.
            try:
                value = fetch(target)
            except TimeoutError:
                if attempt == max_attempts:
                    output.append({"target": list(target), "status": "failed", "attempts": attempt})
            else:
                output.append({"target": list(target), "status": "ok", "attempts": attempt, "value": value})
                break
    return output


def quote_total(lines, fixed_fee="0", currency="CNY"):
    fee = Decimal(str(fixed_fee))
    if not fee.is_finite() or fee < 0:
        raise ValueError("invalid fee")
    total = fee
    for line in lines:
        count = line["quantity"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("invalid quantity")
        unit_price = Decimal(str(line["unit_price"]))
        if line["currency"] != currency or not unit_price.is_finite() or unit_price < 0:
            raise ValueError("currency/price mismatch")
        if unit_price != unit_price.quantize(Decimal("0.01")):
            raise ValueError("unit price requires two-decimal monetary scale")
        total += unit_price * count
    if fee != fee.quantize(Decimal("0.01")):
        raise ValueError("fee requires monetary scale")
    return {"currency": currency, "total": str(total.quantize(Decimal("0.01")))}


def demo():
    attempts = Counter()
    def fetch(target):
        attempts[target] += 1
        if target == ("B", 1) and attempts[target] == 1:
            raise TimeoutError("synthetic transient failure")
        return 10
    return {
        "01_coverage": coverage(["u1", "u2", "u3", "u4"], ["u2", "u2", "u4", "u9"]),
        "02_co_visit": co_visit(["u1", "u2", "u3", "u4"], ["u2", "u4"]),
        "03_cohort": cohort(["u1", "u2"], [("e1", "u1"), ("e2", "u1"), ("e2", "u1"), ("e3", "u3")]),
        "04_trend": matched_day_trend({"weekday": [80, 100], "weekend": [180]}, {"weekday": [100, 100], "weekend": [200]}, True),
        "05_site": site_score({"demand": 80, "access": 60, "cost_fit": 40}, {"demand": ".5", "access": ".3", "cost_fit": ".2"}, True),
        "06_capabilities": capability_match(["profile", "oauth", "export"], ["profile", "oauth"]),
        "07_ticket": ticket_route("data_delay", True),
        "08_report": build_report(["traffic_change", "change_cause"], [{"id": "fixture-1", "supports": ["traffic_change"]}]),
        "09_prewarm": prewarm([("A", 1), ("A", 1), ("A", 2), ("B", 1)], fetch),
        "10_quote": quote_total([{"quantity": 20, "unit_price": "120.00", "currency": "CNY"}], "300.00")}


if __name__ == "__main__":
    print(json.dumps(demo(), ensure_ascii=False, indent=2))
