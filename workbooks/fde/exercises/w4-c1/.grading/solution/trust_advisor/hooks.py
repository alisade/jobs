"""Which StorefrontBackend write hooks a trust mixin actually covers. Reference solution."""

from __future__ import annotations

import importlib
import re

from shopping_agent import StorefrontBackend

from .models import HookCoverage, HooksReport

WRITE_HOOKS = ("add_to_cart", "update_cart_item", "remove_from_cart", "checkout_handoff")
REQUIRED_HOOKS = ("add_to_cart", "update_cart_item", "checkout_handoff")
_TARGET = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*:[A-Za-z_][\w]*$")
_IGNORED = {object}


class HooksInputError(ValueError):
    """The target cannot be inspected (bad format, not allowed, not importable, not a backend)."""


def _name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


def _is_backend(cls: type) -> bool:
    return isinstance(cls, type) and issubclass(cls, StorefrontBackend)


def hooks_covered(target: str, allowed_modules: tuple[str, ...]) -> HooksReport:
    if len(target) > 200 or not _TARGET.match(target):
        raise HooksInputError("backend must look like 'package.module:ClassName'")
    module_name, class_name = target.split(":")
    if not any(module_name == m or module_name.startswith(m + ".") for m in allowed_modules):
        raise HooksInputError(f"module {module_name!r} is not in this server's allowed modules")
    try:
        module = importlib.import_module(module_name)
    except Exception:
        raise HooksInputError(f"module {module_name!r} could not be imported") from None
    cls = getattr(module, class_name, None)
    if not isinstance(cls, type):
        raise HooksInputError(f"{target!r} is not a class")
    if not _is_backend(cls):
        raise HooksInputError(f"{target!r} is not a StorefrontBackend")

    mro = [c for c in cls.__mro__ if c not in _IGNORED]

    def is_hook_mixin(c: type) -> bool:
        return not _is_backend(c) and any(h in vars(c) for h in WRITE_HOOKS)

    # The concrete backend: the first backend class in the MRO that implements a write hook
    # itself (a leaf that only composes mixins and a backend does not count). A hook mixin
    # in front of it wraps it; one behind it is shadowed by it.
    concrete = next(
        (i for i, c in enumerate(mro) if _is_backend(c) and any(h in vars(c) for h in WRITE_HOOKS)),
        len(mro),
    )
    front = {c for c in mro[:concrete] if is_hook_mixin(c)}
    misordered = [_name(c) for c in mro[concrete:] if is_hook_mixin(c)]

    coverage = []
    for hook in WRITE_HOOKS:
        owner = next(c for c in mro if hook in vars(c))
        coverage.append(HookCoverage(hook=hook, defined_by=_name(owner), covered=owner in front))
    missing = [h.hook for h in coverage if h.hook in REQUIRED_HOOKS and not h.covered]
    return HooksReport(
        backend=target,
        resolution_order=[_name(c) for c in mro],
        hooks=coverage,
        missing=missing,
        misordered_mixins=misordered,
        ok=not missing and not misordered,
    )
