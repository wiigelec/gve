from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

from validation.lib import build_family_registry, evaluate_request  # noqa: E402


def build_behavior_registry(
    declarations: Any,
    *,
    location: str,
) -> dict[str, dict[str, Any]]:
    return build_family_registry(declarations, location=location)


def evaluate_behavior(
    request: Any,
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return evaluate_request(request, registry)
