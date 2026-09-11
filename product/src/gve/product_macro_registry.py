from __future__ import annotations

from .macro import MacroRegistry
from .macros.discover import DISCOVER

_PRODUCT_MACRO_REGISTRY = MacroRegistry((DISCOVER,))

def product_macro_registry() -> MacroRegistry:
    """Return the immutable registry of complete public product macros."""
    return _PRODUCT_MACRO_REGISTRY
