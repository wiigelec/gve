from __future__ import annotations

from .plugins.execute import tasks as execute_tasks
from .plugins.filesystem import tasks as filesystem_tasks
from .plugins.git import tasks as git_tasks
from .registry import Registry


def product_registry() -> Registry:
    """Return the static product-owned registry realized by the current Build."""

    return Registry(filesystem_tasks() + git_tasks() + execute_tasks())
