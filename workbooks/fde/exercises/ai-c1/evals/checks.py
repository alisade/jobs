"""Code-graded checks: deterministic rules over one transcript.

YOUR WORK GOES HERE. Each check walks ``events(t)`` (see transcript.py) and returns a
``CheckResult`` with the check's name, passed, and on failure a one-line detail naming
the event index. README.md states each rule precisely; the lexicons below are part of
the contract, use them as given.
"""

from __future__ import annotations

import re  # noqa: F401
from collections.abc import Callable

from .transcript import CheckResult, Event, Transcript, events  # noqa: F401

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


def check_checkout_requested(t: Transcript) -> CheckResult:
    """name: checkout_requested"""
    raise NotImplementedError("check_checkout_requested")


def check_cart_provenance(t: Transcript) -> CheckResult:
    """name: cart_provenance"""
    raise NotImplementedError("check_cart_provenance")


def check_terms_grounded(t: Transcript) -> CheckResult:
    """name: terms_grounded"""
    raise NotImplementedError("check_terms_grounded")


def check_chip_limit(t: Transcript) -> CheckResult:
    """name: chip_limit"""
    raise NotImplementedError("check_chip_limit")


def check_write_claims(t: Transcript) -> CheckResult:
    """name: write_claims_after_success"""
    raise NotImplementedError("check_write_claims")


CHECKS: list[Check] = [
    check_checkout_requested,
    check_cart_provenance,
    check_terms_grounded,
    check_chip_limit,
    check_write_claims,
]
