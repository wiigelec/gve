from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.errors import PayloadError
from gve.product_macro_registry import product_macro_registry

def validate_macro_issue() -> bool:
    macros = product_macro_registry()
    if "issue" not in macros.identities():
        raise AssertionError("issue is not registered")
    d = macros.resolve("issue")
    assert d.stages == ("ISSUE",)

    assert dict(d.build({"operation":"read","number":7}).stages[0].tasks[0]) == {
        "id":"issue-read","task":"github.issue-read","parameters":{"number":7}
    }
    assert dict(d.build({"operation":"create","title":"x"}).stages[0].tasks[0]) == {
        "id":"issue-create","task":"github.issue-create",
        "parameters":{"title":"x","body":"","labels":[]}
    }
    assert dict(d.build({"operation":"modify","number":9,"state":"closed"}).stages[0].tasks[0]) == {
        "id":"issue-modify","task":"github.issue-modify",
        "parameters":{"number":9,"state":"closed"}
    }

    invalid = [
        {}, {"operation":"other"}, {"operation":"read"}, {"operation":"read","number":0},
        {"operation":"read","number":1,"x":1}, {"operation":"create"},
        {"operation":"create","title":""}, {"operation":"create","title":"x","labels":[""]},
        {"operation":"modify","number":1}, {"operation":"modify","number":True,"state":"closed"},
        {"operation":"modify","number":1,"state":"bad"},
    ]
    for p in invalid:
        try:
            d.build(p)
        except PayloadError:
            pass
        else:
            raise AssertionError(f"invalid issue parameters accepted: {p!r}")
    return True
