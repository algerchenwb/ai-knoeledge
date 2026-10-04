"""Exact authorized object lookup on fictional catalog; no embedding or LLM.

Tickets are trusted internal values, not public signed authorization tokens.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import unicodedata


def normalize(text):
    if type(text) is not str or not 1 <= len(text) <= 80:
        raise ValueError("expected nonempty bounded text")
    value = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    if not value:
        raise ValueError("empty normalized text")
    return value


@dataclass(frozen=True)
class ObjectRecord:
    object_id: str
    tenant: str
    label: str
    city: str
    object_type: str
    aliases: tuple[str, ...]
    version: str = "1"
    active: bool = True


@dataclass(frozen=True)
class Access:
    tenant: str
    object_ids: tuple[str, ...]
    policy_version: str


@dataclass(frozen=True)
class Ticket:
    catalog_revision: str
    access_fingerprint: str
    text: str
    object_type: str
    city: str | None
    candidate_ids: tuple[str, ...]
    has_more: bool


FIXTURES = (
    ObjectRecord("area-a", "tenant-a", "星河园区", "甲城", "region", ("星河", "XH Park")),
    ObjectRecord("area-b", "tenant-a", "星河园区", "乙城", "region", ("星河",)),
    ObjectRecord("poi-a", "tenant-a", "星河门店", "甲城", "poi", ("星河",)),
    ObjectRecord("area-hidden", "tenant-b", "星河园区", "甲城", "region", ("星河",)),
    ObjectRecord("area-old", "tenant-a", "旧园区", "甲城", "region", ("旧园",), active=False),
)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Resolver:
    def __init__(self, records=FIXTURES, max_candidates=3):
        self.records = tuple(records)
        if type(max_candidates) is not int or not 1 <= max_candidates <= 10:
            raise ValueError("invalid candidate limit")
        ids = set()
        for record in self.records:
            if not isinstance(record, ObjectRecord) or record.object_id in ids:
                raise ValueError("invalid or duplicate object ID")
            ids.add(record.object_id)
            for field in (record.object_id, record.tenant, record.label, record.city, record.version):
                normalize(field)
            if record.object_type not in {"region", "poi"} or type(record.active) is not bool:
                raise ValueError("invalid type or active flag")
            if type(record.aliases) is not tuple:
                raise ValueError("aliases must be immutable tuple")
            for alias in record.aliases:
                normalize(alias)
        self.max_candidates = max_candidates
        self.revision = fingerprint([asdict(x) for x in sorted(self.records, key=lambda x: x.object_id)])
        self.searches = 0

    def authorized(self, access, record):
        return record.active and record.tenant == access.tenant and record.object_id in access.object_ids

    def access_fingerprint(self, access):
        return fingerprint([access.tenant, sorted(access.object_ids), access.policy_version])

    def resolve(self, access, text, object_type, city=None):
        target = normalize(text)
        if object_type not in {"region", "poi"}:
            raise ValueError("unsupported object type")
        city_key = normalize(city) if city is not None else None
        self.searches += 1
        candidates = [r for r in self.records if self.authorized(access, r)
                      and r.object_type == object_type and (city_key is None or normalize(r.city) == city_key)
                      and target in {normalize(r.label), *(normalize(a) for a in r.aliases)}]
        candidates.sort(key=lambda r: r.object_id)
        shown = candidates[:self.max_candidates]
        more = len(candidates) > len(shown)
        status = "resolved" if len(candidates) == 1 else "needs_clarification" if candidates else "not_found"
        ticket = Ticket(self.revision, self.access_fingerprint(access), target, object_type, city_key,
                        tuple(r.object_id for r in shown), more)
        result = {"status": status, "has_more": more,
                  "candidates": [{"object_id": r.object_id, "label": r.label, "city": r.city,
                                  "object_type": r.object_type, "object_version": r.version} for r in shown],
                  "catalog_revision": self.revision,
                  "reason": "authorized_exact_label_or_alias_lookup"}
        return result, ticket

    def choose(self, access, ticket, object_id):
        if type(ticket) is not Ticket or ticket.catalog_revision != self.revision:
            raise ValueError("STALE_CATALOG")
        if ticket.access_fingerprint != self.access_fingerprint(access):
            raise ValueError("STALE_ACCESS")
        current, refreshed = self.resolve(access, ticket.text, ticket.object_type, ticket.city)
        if refreshed != ticket:
            raise ValueError("STALE_CANDIDATES")
        if ticket.has_more:
            raise ValueError("NEEDS_REFINEMENT")
        if object_id not in ticket.candidate_ids:
            raise ValueError("INVALID_SELECTION")
        return next(x for x in current["candidates"] if x["object_id"] == object_id)

    def resolve_id(self, access, object_id):
        normalize(object_id)
        record = next((r for r in self.records if r.object_id == object_id and self.authorized(access, r)), None)
        # Unauthorized and nonexistent IDs have identical public shape.
        if record is None:
            return {"status": "not_found"}
        return {"status": "resolved", "object_id": record.object_id,
                "object_type": record.object_type, "object_version": record.version}


def fixture_access():
    return Access("tenant-a", ("area-a", "area-b", "poi-a", "area-old"), "fixture-policy-v1")


def example():
    r, a = Resolver(), fixture_access()
    ambiguous, ticket = r.resolve(a, "星河", "region")
    selected = r.choose(a, ticket, "area-b")
    narrowed, _ = r.resolve(a, "星河", "region", "甲城")
    return {"ambiguous": ambiguous, "selected": selected, "narrowed": narrowed,
            "not_found": r.resolve(a, "未收录园区", "region")[0], "searches": r.searches}


if __name__ == "__main__":
    print(json.dumps(example(), ensure_ascii=False, indent=2))
