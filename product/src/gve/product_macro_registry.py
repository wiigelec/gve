from __future__ import annotations

from .macro import MacroRegistry


_PRODUCT_MACRO_REGISTRY = MacroRegistry()


def product_macro_registry() -> MacroRegistry:
    """Return the immutable registry of complete public product macros."""

    return _PRODUCT_MACRO_REGISTRY
