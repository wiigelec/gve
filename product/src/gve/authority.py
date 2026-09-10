from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Authority:
    """Execution authority established outside a workflow payload."""

    repository: Path
    git_remotes: frozenset[str] = frozenset()
    github_repository: str | None = None
    execute_limits: tuple[tuple[str, int], ...] = ()

    @classmethod
    def for_repository(cls, repository: Path | str) -> "Authority":
        return cls(repository=Path(repository).resolve())

    def execute_limit_map(self) -> dict[str, int]:
        return dict(self.execute_limits)
