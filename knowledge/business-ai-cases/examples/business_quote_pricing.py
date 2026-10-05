"""Fictional pre-tax graduated pricing. No billing, legal offer or payment."""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re


def decimal_text(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d{1,4})?", value):
        raise ValueError("plain nonnegative decimal string required")
    return Decimal(value)


def digest(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class RateCard:
    version: str
    currency: str
    start: str
    end: str
    # Each tier upper bound is cumulative; None denotes the final unbounded tier.
    skus: tuple[tuple[str, tuple[tuple[int | None, str], ...]], ...]


@dataclass(frozen=True)
class Policy:
    version: str
    automatic_discount_limit: str
    max_valid_days: int


class QuotePricing:
    def __init__(self, tenant, customer, card, policy):
        if not tenant or not customer or not card.version or card.currency not in {"CNY", "USD"}:
            raise ValueError("invalid scope or card")
        if date.fromisoformat(card.start) >= date.fromisoformat(card.end):
            raise ValueError("invalid card interval")
        if not policy.version or not 0 <= decimal_text(policy.automatic_discount_limit) <= 1:
            raise ValueError("invalid discount policy")
        if type(policy.max_valid_days) is not int or not 1 <= policy.max_valid_days <= 30:
            raise ValueError("invalid validity policy")
        if not card.skus or len({sku for sku, _ in card.skus}) != len(card.skus):
            raise ValueError("empty or duplicate SKU")
        for sku, tiers in card.skus:
            if not isinstance(sku, str) or not sku or not tiers or tiers[-1][0] is not None:
                raise ValueError("final unbounded tier required")
            previous = 0
            for index, (upper, price) in enumerate(tiers):
                p = decimal_text(price)
                if p <= 0 or p != p.quantize(Decimal("0.01")):
                    raise ValueError("positive two-decimal unit price required")
                if upper is None:
                    if index != len(tiers) - 1:
                        raise ValueError("unbounded tier must be last")
                elif type(upper) is not int or upper <= previous:
                    raise ValueError("tier bounds must increase")
                else:
                    previous = upper
        self.tenant, self.customer, self.card, self.policy = tenant, customer, card, policy
        self.prices = dict(card.skus)

    def build(self, lines, currency, as_of, valid_days):
        day = date.fromisoformat(as_of)
        if not date.fromisoformat(self.card.start) <= day < date.fromisoformat(self.card.end):
            raise ValueError("card not active")
        if currency != self.card.currency:
            raise ValueError("currency mismatch; no FX conversion")
        if type(valid_days) is not int or not 1 <= valid_days <= self.policy.max_valid_days:
            raise ValueError("invalid requested validity")
        if not isinstance(lines, list) or not 1 <= len(lines) <= 20:
            raise ValueError("1 to 20 quote lines required")
        seen, rows = set(), []
        with localcontext() as ctx:
            ctx.prec = 38
            for line in lines:
                if not isinstance(line, dict) or set(line) != {"sku", "quantity", "discount"}:
                    raise ValueError("line field mismatch")
                sku, quantity, discount = line["sku"], line["quantity"], decimal_text(line["discount"])
                if not isinstance(sku, str) or sku not in self.prices or sku in seen:
                    raise ValueError("unknown or duplicate SKU")
                if type(quantity) is not int or not 1 <= quantity <= 10000 or not 0 <= discount <= 1:
                    raise ValueError("invalid quantity or discount")
                seen.add(sku)
                previous, base, segments = 0, Decimal(0), []
                for upper, price_text in self.prices[sku]:
                    units = min(quantity, upper if upper is not None else quantity) - previous
                    if units > 0:
                        amount = units * Decimal(price_text)
                        base += amount
                        segments.append({"units": units, "unit_price": price_text,
                                         "amount": f"{amount:.2f}"})
                    if upper is None or quantity <= upper:
                        break
                    previous = upper
                net = (base * (1 - discount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                rows.append({"sku": sku, "quantity": quantity, "discount": str(discount),
                             "segments": segments, "base": f"{base:.2f}", "net": f"{net:.2f}"})
            rows.sort(key=lambda row: row["sku"])
            total = sum((Decimal(row["net"]) for row in rows), Decimal(0))
        needs_approval = any(Decimal(row["discount"]) > decimal_text(self.policy.automatic_discount_limit) for row in rows)
        expires = min(day + timedelta(days=valid_days), date.fromisoformat(self.card.end))
        body = {"tenant": self.tenant, "customer": self.customer, "currency": currency,
                "price_basis": "pre-tax; tax and fees not calculated", "pricing_mode": "graduated",
                "card_version": self.card.version, "policy_version": self.policy.version,
                "as_of": day.isoformat(), "valid_days": valid_days, "expires_at": expires.isoformat(),
                "status": "needs_discount_approval" if needs_approval else "pricing_checked",
                "lines": rows, "total": f"{total:.2f}"}
        return {"body": body, "digest": digest(body)}

    def recheck(self, quote, current_card_version, current_policy_version, now):
        if set(quote) != {"body", "digest"} or digest(quote["body"]) != quote["digest"]:
            raise ValueError("quote digest mismatch")
        body = quote["body"]
        inputs = [{k: row[k] for k in ("sku", "quantity", "discount")} for row in body["lines"]]
        if self.build(inputs, body["currency"], body["as_of"], body["valid_days"]) != quote:
            raise ValueError("quote differs from trusted card and customer")
        if current_card_version != self.card.version or current_policy_version != self.policy.version:
            raise ValueError("card or policy changed")
        if not date.fromisoformat(body["as_of"]) <= date.fromisoformat(now) < date.fromisoformat(body["expires_at"]):
            raise ValueError("quote expired or not active")
        if body["status"] != "pricing_checked":
            raise ValueError("discount requires separate approval")
        return {"status": "pricing_rechecked", "digest": quote["digest"], "total": body["total"],
                "currency": body["currency"]}


def fixture_pricing(card=None):
    card = card or RateCard("rate-demo-2", "CNY", "2026-09-01", "2026-11-01", (
        ("analysis-unit", ((100, "2.00"), (None, "1.50"))),
        ("setup-once", ((None, "50.00"),)),
    ))
    return QuotePricing("tenant-demo", "customer-demo", card, Policy("discount-demo-1", "0.10", 14))


def examples():
    pricing = fixture_pricing()
    normal = pricing.build([{"sku": "analysis-unit", "quantity": 150, "discount": "0.10"},
                            {"sku": "setup-once", "quantity": 1, "discount": "0"}], "CNY", "2026-10-05", 14)
    excessive = pricing.build([{"sku": "analysis-unit", "quantity": 150, "discount": "0.20"}],
                              "CNY", "2026-10-05", 14)
    return {"quote": normal, "recheck": pricing.recheck(normal, "rate-demo-2", "discount-demo-1", "2026-10-06"),
            "needs_approval": excessive}


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
