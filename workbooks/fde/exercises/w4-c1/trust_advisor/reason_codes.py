"""Halyard reason-code catalog (merchant-facing wording). Given."""

from __future__ import annotations

CATALOG: dict[str, tuple[str, str]] = {
    "ok": ("No risk signals above threshold.", "None."),
    "velocity_high": (
        "Unusually many cart or checkout actions from this session in a short window.",
        "Expected for bots; check whether a promotion drove a legitimate burst.",
    ),
    "device_mismatch": (
        "The device fingerprint differs from the one seen at sign-in.",
        "Confirm your web and app clients forward the same device id header.",
    ),
    "card_testing_pattern": (
        "Small repeated checkouts typical of stolen-card testing.",
        "Leave denied; consider rate limiting checkout per account.",
    ),
    "new_device_high_value": (
        "High cart value from a device not seen before for this customer.",
        "Route to step-up verification in the app.",
    ),
    "address_mismatch": (
        "Shipping and billing regions disagree.",
        "Route to step-up verification in the app.",
    ),
}

UNKNOWN = (
    "Reason code not in this catalog version.",
    "Upgrade trust-advisor or ask Halyard support for the code's meaning.",
)
