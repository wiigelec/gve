from __future__ import annotations

from .plugins.filesystem import tasks as filesystem_tasks
from .registry import Registry

def product_registry() -> Registry:
    return Registry(filesystem_tasks())
