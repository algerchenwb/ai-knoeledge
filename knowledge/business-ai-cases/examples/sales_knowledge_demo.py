"""Independent sales capability gate. Fictional facts; no LLM or retrieval engine."""
from dataclasses import dataclass
from datetime import date


CONTEXT_KEYS = {"plan", "region", "deployment"}


@dataclass(frozen=True)
class Fact:
    record_id: str
    product: str
    capability: str
    state: str
    review: str
    audience: str
    start: str
    end: str | None
    requirements: tuple[tuple[str, str], ...]
    evidence: str


class CapabilityBook:
    def __init__(self, facts: tuple[Fact, ...], version: str):
        if not version or len({f.record_id for f in facts}) != len(facts):
            raise ValueError("invalid book version or duplicate record id")
        for f in facts:
            if not all(isinstance(v, str) and v for v in
                       (f.record_id, f.product, f.capability)):
                raise ValueError("invalid identity")
            if f.state not in {"supported", "planned", "unsupported"}:
                raise ValueError("invalid state")
            if f.review not in {"approved", "draft"} or f.audience not in {"public", "internal"}:
                raise ValueError("invalid review or audience")
            start = date.fromisoformat(f.start)
            if f.end is not None and date.fromisoformat(f.end) <= start:
                raise ValueError("invalid interval")
            keys = [k for k, _ in f.requirements]
            if len(keys) != len(set(keys)) or any(k not in CONTEXT_KEYS for k in keys):
                raise ValueError("invalid prerequisite key")
            if any(not isinstance(v, str) or not v for _, v in f.requirements):
                raise ValueError("invalid prerequisite value")
            if not isinstance(f.evidence, str):
                raise ValueError("invalid evidence")
        self.facts = tuple(facts)
        self.version = version

    def answer(self, product: str, capability: str, as_of: str,
               context: dict[str, str], audience: str = "public") -> dict:
        """Audience/date/book must be selected by trusted service, not an LLM."""
        if audience not in {"public", "internal"}:
            raise ValueError("invalid audience")
        if not isinstance(context, dict) or any(k not in CONTEXT_KEYS or
                not isinstance(v, str) or not v for k, v in context.items()):
            raise ValueError("invalid context")
        if not isinstance(product, str) or not product or not isinstance(capability, str) or not capability:
            raise ValueError("invalid query")
        day = date.fromisoformat(as_of)
        base = {"product": product, "capability": capability,
                "as_of": day.isoformat(), "book_version": self.version}

        def result(status, records=(), missing=(), failed=()):
            return {**base, "status": status,
                    "record_ids": [f.record_id for f in records],
                    "evidence_ids": [f.evidence for f in records if f.evidence.strip()],
                    "missing_fields": list(missing), "failed_conditions": list(failed)}

        # Exact keys only. Filtering precedes selection and evidence exposure.
        visible = [f for f in self.facts if f.product == product and f.capability == capability
                   and (f.audience == "public" or audience == "internal")
                   and f.review == "approved" and date.fromisoformat(f.start) <= day
                   and (f.end is None or day < date.fromisoformat(f.end))]
        if not visible:
            return result("insufficient_evidence")
        # An overlapping approved claim is a maintenance error, not a ranking decision.
        if len(visible) != 1:
            return result("conflict", visible)
        fact = visible[0]
        if not fact.evidence.strip():
            return result("insufficient_evidence", (fact,))
        if fact.state != "supported":
            return result(fact.state, (fact,))
        failed = [k for k, v in fact.requirements if k in context and context[k] != v]
        missing = [k for k, _ in fact.requirements if k not in context]
        if failed:
            return result("not_applicable", (fact,), missing, failed)
        if missing:
            return result("needs_info", (fact,), missing)
        return result("supported", (fact,))


def fixture_book():
    return CapabilityBook((
        Fact("export-v1", "atlas", "export", "supported", "approved", "public",
             "2026-01-01", "2026-09-01", (("plan", "basic"),), "release-1#export"),
        Fact("export-v2", "atlas", "export", "supported", "approved", "public",
             "2026-09-01", None, (("plan", "pro"), ("region", "CN")), "release-2#export"),
        Fact("export-v3-draft", "atlas", "export", "supported", "draft", "public",
             "2026-09-20", None, (), "draft-3#export"),
        Fact("forecast-plan", "atlas", "forecast", "planned", "approved", "public",
             "2026-09-01", None, (), "roadmap-1#forecast"),
        Fact("realtime-no", "atlas", "realtime", "unsupported", "approved", "public",
             "2026-09-01", None, (), "limits-2#realtime"),
        Fact("private-preview", "atlas", "private-preview", "supported", "approved", "internal",
             "2026-09-01", None, (), "internal-2#preview"),
    ), "capability-book-2")


def examples():
    book = fixture_book()
    return [book.answer("atlas", key, "2026-10-05", ctx) for key, ctx in (
        ("export", {"plan": "pro", "region": "CN"}),
        ("export", {"plan": "pro"}),
        ("export", {"plan": "basic", "region": "CN"}),
        ("forecast", {}), ("realtime", {}), ("unknown", {}))]


if __name__ == "__main__":
    import json
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
