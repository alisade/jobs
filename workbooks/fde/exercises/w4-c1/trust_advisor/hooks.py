"""Which StorefrontBackend write hooks a trust mixin actually covers (see README)."""

from __future__ import annotations

from shopping_agent import StorefrontBackend  # noqa: F401

from .models import HookCoverage, HooksReport  # noqa: F401

WRITE_HOOKS = ("add_to_cart", "update_cart_item", "remove_from_cart", "checkout_handoff")
REQUIRED_HOOKS = ("add_to_cart", "update_cart_item", "checkout_handoff")


class HooksInputError(ValueError):
    """The target cannot be inspected (bad format, not allowed, not importable, not a backend)."""


def hooks_covered(target: str, allowed_modules: tuple[str, ...]) -> HooksReport:
    """Import ``target`` ('package.module:ClassName') only if its module is allowed, then
    walk the class's MRO to find which class defines each write hook."""
    # TODO
    raise NotImplementedError("hooks_covered")
