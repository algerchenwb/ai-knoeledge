"""SQLite teaching ledger: idempotent ticket writes and human lifecycle actions."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    tenant: str
    human: bool


class Rejected(ValueError):
    pass


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


class Tickets:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL,
                category TEXT NOT NULL, priority TEXT NOT NULL, state TEXT NOT NULL,
                queue TEXT NOT NULL, version INTEGER NOT NULL, created_at INTEGER NOT NULL,
                due_at INTEGER NOT NULL, first_response_at INTEGER,
                escalated INTEGER NOT NULL DEFAULT 0, resolution_ref TEXT
            );
            CREATE TABLE IF NOT EXISTS receipts (
                tenant TEXT NOT NULL, request_key TEXT NOT NULL,
                fingerprint TEXT NOT NULL, response TEXT NOT NULL,
                PRIMARY KEY (tenant, request_key)
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL,
                kind TEXT NOT NULL, at INTEGER NOT NULL, version INTEGER NOT NULL
            );
        ''')

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def validate(self, actor, now):
        if not isinstance(actor, Actor) or not isinstance(actor.tenant, str) or not actor.tenant:
            raise Rejected("invalid actor")
        if type(actor.human) is not bool or type(now) is not int or now < 0:
            raise Rejected("invalid actor or clock")

    def get(self, actor, ticket_id):
        if type(ticket_id) is not int or ticket_id <= 0:
            raise Rejected("invalid ticket id")
        row = self.db.execute("SELECT * FROM tickets WHERE id=? AND tenant=?",
                              (ticket_id, actor.tenant)).fetchone()
        if row is None:
            raise Rejected("ticket not found")
        return dict(row)

    def replay(self, actor, key, payload):
        if not isinstance(key, str) or not key.strip():
            raise Rejected("request key required")
        row = self.db.execute("SELECT * FROM receipts WHERE tenant=? AND request_key=?",
                              (actor.tenant, key)).fetchone()
        if row:
            if row["fingerprint"] != fingerprint(payload):
                raise Rejected("idempotency key conflict")
            return {"replayed": True, "ticket": json.loads(row["response"])}
        return None

    def save(self, actor, key, payload, ticket):
        self.db.execute("INSERT INTO receipts VALUES (?,?,?,?)",
                        (actor.tenant, key, fingerprint(payload), json.dumps(ticket)))
        return {"replayed": False, "ticket": ticket}

    def event(self, ticket_id, kind, now, version):
        self.db.execute("INSERT INTO events(ticket_id,kind,at,version) VALUES (?,?,?,?)",
                        (ticket_id, kind, now, version))

    def create(self, actor, key, category, priority, now):
        self.validate(actor, now)
        if category not in {"data", "account"} or priority not in {"p1", "p2"}:
            raise Rejected("invalid category or priority")
        payload = {"op": "create", "category": category, "priority": priority}
        with self.transaction():
            replay = self.replay(actor, key, payload)
            if replay:
                return replay
            # Fictional continuous-clock first-response targets, not a contractual SLA.
            due = now + {"p1": 60, "p2": 300}[priority]
            row = self.db.execute('''INSERT INTO tickets
                (tenant,category,priority,state,queue,version,created_at,due_at)
                VALUES (?,?,?,'new',?,1,?,?)''',
                (actor.tenant, category, priority, category + "-support", now, due))
            self.event(row.lastrowid, "created", now, 1)
            return self.save(actor, key, payload, self.get(actor, row.lastrowid))

    def action(self, actor, key, ticket_id, expected_version, op, now, resolution_ref=None):
        self.validate(actor, now)
        if not actor.human:
            raise Rejected("human takeover required")
        if type(expected_version) is not int or expected_version < 1:
            raise Rejected("invalid version")
        if op not in {"assign", "respond", "wait_customer", "resume", "resolve"}:
            raise Rejected("invalid action")
        if op == "resolve":
            if not isinstance(resolution_ref, str) or not resolution_ref.strip():
                raise Rejected("resolution reference required")
        elif resolution_ref is not None:
            raise Rejected("unexpected resolution reference")
        payload = {"op": op, "ticket_id": ticket_id, "version": expected_version,
                   "resolution_ref": resolution_ref}
        with self.transaction():
            # Read current authorized object before returning even a persisted receipt.
            current = self.get(actor, ticket_id)
            replay = self.replay(actor, key, payload)
            if replay:
                return replay
            if current["version"] != expected_version:
                raise Rejected("stale version")
            last_at = self.db.execute("SELECT MAX(at) FROM events WHERE ticket_id=?",
                                      (ticket_id,)).fetchone()[0]
            if now < last_at:
                raise Rejected("clock before last event")
            allowed = {"assign": {"new"}, "respond": {"assigned"},
                       "wait_customer": {"assigned"}, "resume": {"waiting_customer"},
                       "resolve": {"assigned", "waiting_customer"}}
            if current["state"] not in allowed[op]:
                raise Rejected("invalid state transition")
            state = {"assign": "assigned", "respond": "assigned",
                     "wait_customer": "waiting_customer", "resume": "assigned",
                     "resolve": "resolved"}[op]
            response_at = current["first_response_at"]
            if op == "respond" and response_at is None:
                response_at = now
            self.db.execute('''UPDATE tickets SET state=?,version=version+1,
                               first_response_at=?,resolution_ref=? WHERE id=?''',
                            (state, response_at, resolution_ref, ticket_id))
            self.event(ticket_id, op, now, expected_version + 1)
            return self.save(actor, key, payload, self.get(actor, ticket_id))

    def escalate_due(self, actor, now):
        self.validate(actor, now)
        with self.transaction():
            rows = self.db.execute('''SELECT * FROM tickets WHERE tenant=?
                AND state!='resolved' AND first_response_at IS NULL
                AND escalated=0 AND due_at<=?''', (actor.tenant, now)).fetchall()
            for row in rows:
                last_at = self.db.execute("SELECT MAX(at) FROM events WHERE ticket_id=?",
                                          (row["id"],)).fetchone()[0]
                if now < last_at:
                    raise Rejected("clock before last event")
                self.db.execute('''UPDATE tickets SET escalated=1,queue='human-escalation',
                                   version=version+1 WHERE id=?''', (row["id"],))
                self.event(row["id"], "escalated", now, row["version"] + 1)
            return [self.get(actor, row["id"]) for row in rows]


def examples():
    ledger = Tickets()
    bot, human = Actor("tenant-demo", False), Actor("tenant-demo", True)
    created = ledger.create(bot, "create-1", "data", "p1", 100)
    duplicate = ledger.create(bot, "create-1", "data", "p1", 101)
    ticket_id = created["ticket"]["id"]
    escalation = ledger.escalate_due(bot, 160)
    assigned = ledger.action(human, "assign-1", ticket_id, 2, "assign", 161)
    responded = ledger.action(human, "respond-1", ticket_id, 3, "respond", 162)
    resolved = ledger.action(human, "resolve-1", ticket_id, 4, "resolve", 180, "review-demo-1")
    ledger.close()
    return {"created": created, "duplicate": duplicate, "escalation": escalation,
            "assigned": assigned, "responded": responded, "resolved": resolved}


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
