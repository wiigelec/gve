from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.errors import PayloadError
from gve.product_macro_registry import product_macro_registry

def validate_macro_pr() -> bool:
    macros = product_macro_registry()
    if "pr" not in macros.identities():
        raise AssertionError("pr is not registered")
    d = macros.resolve("pr")
    assert d.stages == ("PR",)

    assert dict(d.build({"operation":"read","number":7}).stages[0].tasks[0]) == {
        "id":"pr-read","task":"github.pull-request-read","parameters":{"number":7}
    }
    assert dict(d.build({
        "operation":"create","title":"x","base":"main","head":"topic"
    }).stages[0].tasks[0]) == {
        "id":"pr-create","task":"github.pull-request-create",
        "parameters":{"title":"x","body":"","base":"main","head":"topic","draft":False}
    }
    assert dict(d.build({
        "operation":"modify","number":9,"state":"closed"
    }).stages[0].tasks[0]) == {
        "id":"pr-modify","task":"github.pull-request-modify",
        "parameters":{"number":9,"state":"closed"}
    }

    invalid = [
        {}, {"operation":"other"}, {"operation":"read"}, {"operation":"read","number":0},
        {"operation":"read","number":1,"x":1}, {"operation":"create","title":"x","base":"main"},
        {"operation":"create","title":"","base":"main","head":"topic"},
        {"operation":"create","title":"x","base":"main","head":"topic","draft":"no"},
        {"operation":"modify","number":1}, {"operation":"modify","number":True,"state":"closed"},
        {"operation":"modify","number":1,"state":"bad"},
    ]
    for p in invalid:
        try:
            d.build(p)
        except PayloadError:
            pass
        else:
            raise AssertionError(f"invalid pr parameters accepted: {p!r}")
    return True
