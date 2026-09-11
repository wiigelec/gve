from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.engine import Engine
from gve.errors import PayloadError
from gve.macro_request import parse_macro_request
from gve.macro_runner import MacroRunner, RepositoryContext
from gve.product_macro_registry import product_macro_registry
from gve.product_registry import product_registry


def _request(parameters=None, repository=None):
    return parse_macro_request(
        {
            "schema_version": 1,
            "header": {"repository": repository or {}},
            "macro": {"name": "discover", "parameters": parameters or {}},
        }
    )


def validate_macro_discover() -> bool:
    macros = product_macro_registry()
    if "discover" not in macros.identities():
        raise AssertionError("discover is not registered")

    definition = macros.resolve("discover")
    if definition.stages != ("DISCOVER",):
        raise AssertionError("discover public stage contract mismatch")

    default_plan = definition.build({})
    default_tasks = [dict(task) for task in default_plan.stages[0].tasks]
    if [task["task"] for task in default_tasks] != [
        "git.repository", "git.branch", "git.head", "git.status"
    ]:
        raise AssertionError("discover default task composition mismatch")

    reordered = definition.build({"observations": ["root_entries", "head"]})
    reordered_tasks = [dict(task) for task in reordered.stages[0].tasks]
    if [task["task"] for task in reordered_tasks] != ["git.head", "filesystem.list"]:
        raise AssertionError("discover task order is caller-controlled")

    invalid = [
        {"extra": True},
        {"observations": []},
        {"observations": ["head", "head"]},
        {"observations": ["unknown"]},
        {"observations": [1]},
    ]
    for params in invalid:
        try:
            definition.build(params)
        except PayloadError:
            pass
        else:
            raise AssertionError(f"invalid discover parameters accepted: {params!r}")

    runner = MacroRunner(Engine(product_registry()), macros)
    context = RepositoryContext(ROOT, "wiigelec/gve", "fs002", None)
    authority = Authority.for_repository(ROOT)

    result = runner.execute(_request({"observations": ["head"]}), authority, context)
    if result["macro"] != "discover" or result["stages"][0]["label"] != "DISCOVER":
        raise AssertionError("discover macro result structure mismatch")
    if result["tasks"][0]["effects"] != {}:
        raise AssertionError("discover produced mutation effects")

    guarded = _request({}, {"identity": "other/repo"})
    try:
        runner.execute(guarded, authority, context)
    except PayloadError:
        pass
    else:
        raise AssertionError("repository identity mismatch was accepted")

    unknown = parse_macro_request(
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": "unknown", "parameters": {}},
        }
    )
    try:
        runner.execute(unknown, authority, RepositoryContext(ROOT, None, None, None))
    except PayloadError:
        pass
    else:
        raise AssertionError("unknown macro identity was accepted")

    with tempfile.TemporaryDirectory() as td:
        temp_root = Path(td)
        temp_authority = Authority.for_repository(temp_root)
        temp_context = RepositoryContext(temp_root, None, None, None)
        failed = runner.execute(_request(), temp_authority, temp_context)
        if failed["status"] != "failure":
            raise AssertionError("discover converted governed failure into success")
        statuses = [task["status"] for task in failed["stages"][0]["tasks"]]
        if statuses[0] != "failure" or any(status != "not-executed" for status in statuses[1:]):
            raise AssertionError(f"fail-fast regrouping mismatch: {statuses}")

    bad_envelopes = [
        {
            "schema_version": 2,
            "header": {"repository": {}},
            "macro": {"name": "discover", "parameters": {}},
        },
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": "discover", "parameters": {}},
            "extra": True,
        },
    ]
    for payload in bad_envelopes:
        try:
            parse_macro_request(payload)
        except PayloadError:
            pass
        else:
            raise AssertionError("invalid macro request envelope accepted")

    return True
