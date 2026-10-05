"""Synthetic in-memory CSV preview/commit. Explicit mapping; no model or real auth."""
import csv
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import hashlib
import io
import re
import threading
import uuid


FIELDS = {"object_id", "population_type", "snapshot_date", "population_count"}


@dataclass(frozen=True)
class Actor:
    tenant: str
    subject: str


class Importer:
    def __init__(self):
        self.lock = threading.RLock()
        self.grants, self.records, self.versions, self.plans, self.receipts = {}, {}, {}, {}, {}

    def grant(self, actor, objects):
        # Fixture setup only. A production service obtains these from authorization.
        key = (actor.tenant, actor.subject)
        with self.lock:
            revision = self.grants.get(key, (set(), 0))[1] + 1
            self.grants[key] = (set(objects), revision)

    def _grant(self, actor):
        if not isinstance(actor, Actor) or not actor.tenant or not actor.subject:
            raise ValueError("invalid actor")
        grant = self.grants.get((actor.tenant, actor.subject))
        if grant is None:
            raise ValueError("no import grant")
        return grant

    @staticmethod
    def _clock(now):
        if type(now) is not int or now < 0:
            raise ValueError("invalid service clock")

    def preview(self, actor, text, mapping, now):
        self._clock(now)
        if not isinstance(text, str) or len(text.encode("utf-8")) > 65536:
            raise ValueError("CSV text exceeds 64 KiB or has invalid type")
        if not isinstance(mapping, dict) or set(mapping.values()) != FIELDS or len(mapping) != 4:
            raise ValueError("explicit one-to-one mapping required")
        reader = csv.reader(io.StringIO(text.removeprefix("\ufeff")), strict=True)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValueError("header required") from None
        headers = [h.strip() for h in raw_headers]
        if len(headers) != 4 or any(not h for h in headers) or len(set(headers)) != 4:
            raise ValueError("exactly four distinct nonempty headers required")
        if set(mapping) != set(headers):
            raise ValueError("mapping does not match normalized headers")
        with self.lock:
            allowed, revision = self._grant(actor)
            accepted, errors, seen = [], [], set()
            existing = self.records.get(actor.tenant, {})
            for line_number, cells in enumerate(reader, 2):
                if line_number > 1001:
                    raise ValueError("more than 1000 records")
                if len(cells) != 4:
                    errors.append({"record_number": line_number, "code": "cell_count"})
                    continue
                row = {mapping[h]: value.strip() for h, value in zip(headers, cells)}
                code = None
                if row["object_id"] not in allowed:
                    code = "object_not_allowed"
                elif not re.fullmatch(r"[1-4]", row["population_type"]):
                    code = "population_type"
                elif not re.fullmatch(r"\d{1,9}", row["population_count"]):
                    code = "population_count"
                else:
                    try:
                        parsed_date = date.fromisoformat(row["snapshot_date"])
                        if parsed_date.isoformat() != row["snapshot_date"]:
                            raise ValueError("noncanonical date")
                    except ValueError:
                        code = "snapshot_date"
                if code:
                    errors.append({"record_number": line_number, "code": code})
                    continue
                row["population_type"] = int(row["population_type"])
                row["population_count"] = int(row["population_count"])
                key = (row["object_id"], row["population_type"], row["snapshot_date"])
                if key in seen or key in existing:
                    errors.append({"record_number": line_number, "code": "duplicate_key"})
                    continue
                seen.add(key)
                accepted.append(row)
            if not accepted and not errors:
                raise ValueError("at least one record required")
            token = uuid.uuid4().hex
            plan = {"actor": actor, "grant_revision": revision,
                    "dataset_version": self.versions.get(actor.tenant, 0),
                    "file_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "mapping": dict(mapping), "rows": deepcopy(accepted), "errors": errors,
                    "created_at": now, "expires_at": now + 300}
            self.plans[token] = plan
            return {"plan_id": token, "file_sha256": plan["file_sha256"],
                    "dataset_version": plan["dataset_version"], "grant_revision": revision,
                    "status": "ready" if not errors else "invalid", "accepted_rows": len(accepted),
                    "errors": deepcopy(errors), "expires_at": plan["expires_at"]}

    def commit(self, actor, plan_id, now):
        self._clock(now)
        with self.lock:
            allowed, revision = self._grant(actor)
            plan = self.plans.get(plan_id)
            if plan is None or plan["actor"] != actor:
                raise ValueError("plan not found")
            if revision != plan["grant_revision"] or any(r["object_id"] not in allowed for r in plan["rows"]):
                raise ValueError("grant changed; preview again")
            if not plan["created_at"] <= now < plan["expires_at"]:
                raise ValueError("preview expired or not yet active")
            if plan["errors"]:
                raise ValueError("invalid preview; nothing written")
            if plan_id in self.receipts:
                return {**deepcopy(self.receipts[plan_id]), "replayed": True}
            if self.versions.get(actor.tenant, 0) != plan["dataset_version"]:
                raise ValueError("dataset changed; preview again")
            # All-or-nothing publication of a copied in-memory dataset under one lock.
            new_records = deepcopy(self.records.get(actor.tenant, {}))
            for row in plan["rows"]:
                key = (row["object_id"], row["population_type"], row["snapshot_date"])
                if key in new_records:
                    raise ValueError("existing key conflict")
                new_records[key] = deepcopy(row)
            next_version = plan["dataset_version"] + 1
            receipt = {"plan_id": plan_id, "tenant": actor.tenant, "status": "committed",
                       "rows_written": len(plan["rows"]), "dataset_version": next_version,
                       "file_sha256": plan["file_sha256"]}
            self.records[actor.tenant] = new_records
            self.versions[actor.tenant] = next_version
            self.receipts[plan_id] = receipt
            return {**deepcopy(receipt), "replayed": False}


MAPPING = {"地点": "object_id", "人群类型": "population_type", "日期": "snapshot_date", "人数": "population_count"}
CSV_TEXT = "地点,人群类型,日期,人数\narea-a,4,2026-09-30,100\narea-b,1,2026-09-30,50\n"


def examples():
    importer, actor = Importer(), Actor("tenant-demo", "operator-demo")
    importer.grant(actor, {"area-a", "area-b"})
    preview = importer.preview(actor, CSV_TEXT, MAPPING, 100)
    committed = importer.commit(actor, preview["plan_id"], 101)
    retried = importer.commit(actor, preview["plan_id"], 102)
    invalid = importer.preview(actor, "地点,人群类型,日期,人数\narea-b,4,2026-09-30,-5\n", MAPPING, 103)
    # Stable names for reproducible documentation; actual plan ids are random.
    for value in (preview, committed, retried):
        value["plan_id"] = "plan-demo-valid"
    invalid["plan_id"] = "plan-demo-invalid"
    return {"preview": preview, "committed": committed, "retry": retried,
            "invalid_preview": invalid}


if __name__ == "__main__":
    import json
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
