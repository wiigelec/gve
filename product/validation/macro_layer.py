from __future__ import annotations

import tempfile
from pathlib import Path
import sys

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

DESIGN_REVISION = "bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b"


def _request(name, parameters):
    return parse_macro_request(
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": name, "parameters": parameters},
        }
    )


def validate_macro_layer() -> bool:
    for relative in (
        "product/planning/FS-002-plan.md",
        "product/specs/FS-002-product-macro-layer-and-cli.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if DESIGN_REVISION not in text:
            raise AssertionError(
                f"{relative} does not bind reviewed FS-002 Product Design revision"
            )

    macros = product_macro_registry()
    if macros.identities() != ("discover", "issue", "pr", "modify"):
        raise AssertionError(
            f"final macro registry mismatch: {macros.identities()!r}"
        )

    for identity in macros.identities():
        schema = macros.resolve(identity).parameter_schema
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise AssertionError(f"{identity} public parameter contract is not closed")

    bad_requests = [
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": "discover", "parameters": {}},
            "tasks": [],
        },
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {
                "name": "discover",
                "parameters": {},
                "stages": [],
            },
        },
    ]
    for payload in bad_requests:
        try:
            parse_macro_request(payload)
        except PayloadError:
            pass
        else:
            raise AssertionError("caller-authored macro orchestration was accepted")

    generic_behavior_fields = (
        {"tasks": []},
        {"stages": []},
        {"condition": True},
        {"loop": {}},
        {"template": {}},
        {"continuation": {}},
    )
    for identity in macros.identities():
        definition = macros.resolve(identity)
        for params in generic_behavior_fields:
            try:
                definition.build(params)
            except (PayloadError, KeyError, TypeError):
                pass
            else:
                raise AssertionError(
                    f"{identity} accepted generic behavior field(s): {sorted(params)}"
                )

    modify_plan = macros.resolve("modify").build(
        {
            "changes": [
                {"operation": "create", "path": "generated.txt", "content": "x\n"}
            ],
            "commit_message": "generated",
            "validate": False,
        }
    )
    tasks = {
        task["id"]: task
        for stage in modify_plan.stages
        for task in stage.tasks
    }
    expected_refs = {
        ("modify-remote-before", "branch"): "modify-branch.result.branch",
        ("modify-branch-guard", "expected"): "modify-branch.result.branch",
        ("modify-head-guard", "expected"): "modify-head.result.commit",
        ("modify-push", "local_branch"): "modify-branch.result.branch",
        ("modify-push", "remote_branch"): "modify-branch.result.branch",
        ("modify-push", "expected_remote_head"): "modify-remote-before.result.commit",
        ("modify-verify", "branch"): "modify-branch.result.branch",
        ("modify-verify", "expected"): "modify-commit.result.commit",
    }
    for (task_id, field), reference in expected_refs.items():
        if tasks[task_id]["parameters"][field] != {"$ref": reference}:
            raise AssertionError(f"non-native result binding for {task_id}.{field}")

    runner = MacroRunner(Engine(product_registry()), macros)
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td).resolve()
        authority = Authority.for_repository(repo)
        context = RepositoryContext(repo, "owner/repo", "main", None)
        for name, params in (
            ("issue", {"operation": "read", "number": 1}),
            ("pr", {"operation": "read", "number": 1}),
        ):
            result = runner.execute(_request(name, params), authority, context)
            if result["status"] != "failure":
                raise AssertionError(f"{name} widened missing GitHub authority")
            failed = next(task for task in result["tasks"] if task["status"] == "failure")
            if failed["error"]["code"] != "authority":
                raise AssertionError(f"{name} did not fail at authority boundary")

    cli_text = (ROOT / "product/src/gve/cli.py").read_text(encoding="utf-8")
    if '["gh", "auth", "status", "--hostname", "github.com"]' not in cli_text:
        raise AssertionError("GitHub macro authority check is not bound to github.com")

    return True
