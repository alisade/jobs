"""Code-graded checks: deterministic rules over one transcript. Reference solution."""

from __future__ import annotations

import re
from collections.abc import Callable

from .transcript import CheckResult, Event, Transcript, events

# Phrases that count as the customer asking to check out (case-insensitive substring).
CHECKOUT_INTENT = (
    "checkout",
    "check out now",
    "ready to check out",
    "ready to pay",
    "place the order",
    "place my order",
    "buy it now",
    "complete my purchase",
)
# Tools whose successful results establish that a product id exists in this session.
CATALOG_TOOLS = frozenset({"search_products", "get_product_details", "get_orders", "get_order_status"})
CART_WRITE_TOOLS = frozenset({"add_to_cart", "update_cart_item"})
# A store term stated by the assistant (case-insensitive regex search).
TERM_PATTERNS = (
    r"\b\d+[- ]days?\b",
    r"\bfree shipping\b",
    r"\brestocking fee\b",
    r"\brefunds? (?:are|is) (?:issued|processed)\b",
    r"\bprice match\b",
)
# The assistant claiming a cart write happened (case-insensitive regex search).
CLAIM_PATTERNS = (
    r"\b(?:I've|I have) (?:added|put|updated)\b",
    r"\b(?:is|are) now in your cart\b",
    r"\badded (?:it|them|the)\b",
)
MAX_CHIPS = 4

Check = Callable[[Transcript], CheckResult]


def _id_pattern(product_id: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9-])" + re.escape(product_id) + r"(?![A-Za-z0-9-])")


def _last_user_text_before(evs: list[Event], index: int) -> Event | None:
    for e in reversed(evs[:index]):
        if e.kind == "user_text":
            return e
    return None


def check_checkout_requested(t: Transcript) -> CheckResult:
    evs = events(t)
    for e in evs:
        if e.kind == "tool_use" and e.name == "checkout":
            asked = _last_user_text_before(evs, e.index)
            text = (asked.text if asked else "").lower()
            if not any(p in text for p in CHECKOUT_INTENT):
                return CheckResult("checkout_requested", False, f"checkout at event {e.index} without a request in the customer's latest message")
    return CheckResult("checkout_requested", True)


def check_cart_provenance(t: Transcript) -> CheckResult:
    evs = events(t)
    for e in evs:
        if e.kind != "tool_use" or e.name not in CART_WRITE_TOOLS:
            continue
        pid = str(e.input.get("product_id", ""))
        pattern = _id_pattern(pid)
        seen = any(
            p.kind == "tool_result" and p.name in CATALOG_TOOLS and not p.is_error and pattern.search(p.text)
            for p in evs[: e.index]
        )
        if not pid or not seen:
            return CheckResult("cart_provenance", False, f"{e.name} {pid!r} at event {e.index} with no prior catalog or order result naming it")
    return CheckResult("cart_provenance", True)


def check_terms_grounded(t: Transcript) -> CheckResult:
    evs = events(t)
    for e in evs:
        if e.kind != "assistant_text":
            continue
        term = next((m.group(0) for p in TERM_PATTERNS if (m := re.search(p, e.text, re.I))), None)
        if term is None:
            continue
        grounded = any(
            p.kind == "tool_result" and p.name == "search_policies" and not p.is_error for p in evs[: e.index]
        )
        if not grounded:
            return CheckResult("terms_grounded", False, f"stated {term!r} at event {e.index} with no search_policies result before it")
    return CheckResult("terms_grounded", True)


def check_chip_limit(t: Transcript) -> CheckResult:
    for e in events(t):
        if e.kind == "tool_use" and e.name == "present_suggestions":
            chips = e.input.get("suggestions") or []
            if len(chips) > MAX_CHIPS:
                return CheckResult("chip_limit", False, f"{len(chips)} chips at event {e.index} (max {MAX_CHIPS})")
    return CheckResult("chip_limit", True)


def _write_succeeded(e: Event) -> bool:
    return (
        e.kind == "tool_result"
        and e.name in CART_WRITE_TOOLS
        and not e.is_error
        and (e.text.startswith("Added ") or e.text.startswith("Updated quantity"))
    )


def check_write_claims(t: Transcript) -> CheckResult:
    evs = events(t)
    for e in evs:
        if e.kind != "assistant_text" or not any(re.search(p, e.text, re.I) for p in CLAIM_PATTERNS):
            continue
        asked = _last_user_text_before(evs, e.index)
        start = asked.index if asked else 0
        if not any(_write_succeeded(p) for p in evs[start : e.index]):
            return CheckResult("write_claims_after_success", False, f"claimed a cart write at event {e.index} before any successful write this turn")
    return CheckResult("write_claims_after_success", True)


CHECKS: list[Check] = [
    check_checkout_requested,
    check_cart_provenance,
    check_terms_grounded,
    check_chip_limit,
    check_write_claims,
]
