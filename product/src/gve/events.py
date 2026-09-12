from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable, Mapping

Observer = Callable[[Mapping[str, object]], None]
_CURRENT: ContextVar[Observer | None] = ContextVar("gve_execution_observer", default=None)


def emit_to(observer: Observer | None, event_type: str, **fields: object) -> None:
    if observer is None:
        return
    event = {"type": event_type}
    event.update(fields)
    observer(event)


def emit_current(event_type: str, **fields: object) -> None:
    emit_to(_CURRENT.get(), event_type, **fields)


@contextmanager
def bind_observer(observer: Observer | None):
    token = _CURRENT.set(observer)
    try:
        yield
    finally:
        _CURRENT.reset(token)
