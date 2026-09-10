from __future__ import annotations

from .plugins.execute import tasks as execute_tasks
from .plugins.filesystem import tasks as filesystem_tasks
from .plugins.git import tasks as git_tasks
from .plugins.github import tasks as github_tasks
from .registry import Registry


def product_registry() -> Registry:
    """Return the static product-owned task registry."""

    return Registry(
        filesystem_tasks()
        + git_tasks()
        + execute_tasks()
        + github_tasks()
    )
