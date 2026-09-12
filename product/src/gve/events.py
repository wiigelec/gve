from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable, Mapping

Observer = Callable[[Mapping[str, object]], None]
_CURRENT: ContextVar[Observer | None] = ContextVar("gve_execution_observer", default=None)


def emit_event(observer: Observer | None, event: Mapping[str, object]) -> None:
    if observer is None:
        return
    try:
        observer(event)
    except Exception:
        # Presentation is observational and must not alter governed execution.
        return


def emit_to(observer: Observer | None, event_type: str, **fields: object) -> None:
    event = {"type": event_type}
    event.update(fields)
    emit_event(observer, event)


def emit_current(event_type: str, **fields: object) -> None:
    emit_to(_CURRENT.get(), event_type, **fields)


@contextmanager
def bind_observer(observer: Observer | None):
    token = _CURRENT.set(observer)
    try:
        yield
    finally:
        _CURRENT.reset(token)
