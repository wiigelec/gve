from __future__ import annotations

from .macro import MacroRegistry
from .macros.discover import DISCOVER
from .macros.issue import ISSUE
from .macros.pr import PR
from .macros.modify import MODIFY

_PRODUCT_MACRO_REGISTRY = MacroRegistry((DISCOVER, ISSUE, PR, MODIFY))

def product_macro_registry() -> MacroRegistry:
    """Return the immutable registry of complete public product macros."""
    return _PRODUCT_MACRO_REGISTRY
