"""Backends merchants have actually wired, for list_hooks_covered. Given.

Each mixin method only delegates; what matters to the tool is which class in the MRO
defines each StorefrontBackend write hook.
"""

from __future__ import annotations

from typing import Any

from retail.api.mock_retail import MockRetail


class TrustMixin:
    """A complete trust mixin: both cart writes and checkout."""

    async def add_to_cart(self, *args: Any, **kwargs: Any) -> Any:
        return await super().add_to_cart(*args, **kwargs)  # type: ignore[misc]

    async def update_cart_item(self, *args: Any, **kwargs: Any) -> Any:
        return await super().update_cart_item(*args, **kwargs)  # type: ignore[misc]

    async def checkout_handoff(self, *args: Any, **kwargs: Any) -> Any:
        return await super().checkout_handoff(*args, **kwargs)  # type: ignore[misc]


class CartOnlyTrustMixin:
    """An early version that forgot checkout."""

    async def add_to_cart(self, *args: Any, **kwargs: Any) -> Any:
        return await super().add_to_cart(*args, **kwargs)  # type: ignore[misc]

    async def update_cart_item(self, *args: Any, **kwargs: Any) -> Any:
        return await super().update_cart_item(*args, **kwargs)  # type: ignore[misc]


class AuditMixin:
    """Logs reads; touches no write hook."""

    async def get_cart(self, *args: Any, **kwargs: Any) -> Any:
        return await super().get_cart(*args, **kwargs)  # type: ignore[misc]


class GoodTrusted(TrustMixin, MockRetail):
    pass


class StackedTrusted(AuditMixin, TrustMixin, MockRetail):
    pass


class WrongOrder(MockRetail, TrustMixin):
    """The mixin sits behind MockRetail, so MockRetail's methods win."""


class CartOnlyTrusted(CartOnlyTrustMixin, MockRetail):
    pass


class RetailWithHostedCheckout(MockRetail):
    async def checkout_handoff(self, *args: Any, **kwargs: Any) -> Any:
        return []


class CartOnlyOverHostedCheckout(CartOnlyTrustMixin, RetailWithHostedCheckout):
    """checkout_handoff comes from a backend subclass, not from a trust mixin."""


class InlineTrusted(MockRetail):
    """Trust checks pasted into the backend itself: not a mixin, so not covered."""

    async def add_to_cart(self, *args: Any, **kwargs: Any) -> Any:
        return await super().add_to_cart(*args, **kwargs)


class NotABackend:
    pass
