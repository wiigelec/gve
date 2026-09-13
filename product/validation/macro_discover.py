from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"product"/"src"
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))

from gve.authority import Authority
from gve.engine import Engine
from gve.errors import PayloadError
from gve.macro_request import parse_macro_request
from gve.macro_runner import MacroRunner, RepositoryContext
from gve.product_macro_registry import product_macro_registry
from gve.product_registry import product_registry

def request(parameters=None,repository=None):
    return parse_macro_request({"schema_version":1,"header":{"repository":repository or {}},"macro":{"name":"discover","parameters":parameters or {}}})
def sh(args,cwd):
    cp=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if cp.returncode: raise AssertionError(cp.stderr)
    return cp.stdout.rstrip("\r\n")

def validate_macro_discover():
    macros=product_macro_registry(); definition=macros.resolve("discover")
    assert definition.stages==("DISCOVER",)
    default=[dict(x)["task"] for x in definition.build({}).stages[0].tasks]
    assert default==["git.repository","git.branch","git.head","git.status"]
    reordered=[dict(x)["task"] for x in definition.build({"observations":["root_entries","head"]}).stages[0].tasks]
    assert reordered==["git.head","filesystem.list"]
    plan=definition.build({"observations":["tree_status"],"list_folder":[{"path":"product/src"}],"read_file":{"paths":["README.md","AGENTS.md"]}})
    names=[dict(x)["task"] for x in plan.stages[0].tasks]
    assert names==["git.tree-status","filesystem.list","filesystem.file-read","filesystem.file-read"]
    invalid=[
        {"extra":True},{"observations":[]},{"observations":["head","head"]},{"observations":["unknown"]},{"observations":[1]},
        {"list_folder":[]},{"list_folder":[{"path":"a"},{"path":"./a"}]},
        {"read_file":{"paths":[]}},{"read_file":{"paths":["a","./a"]}},{"read_file":{"other":[]}},
    ]
    for p in invalid:
        try: definition.build(p)
        except PayloadError: pass
        else: raise AssertionError(f"invalid discover parameters accepted: {p!r}")

    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)/"repo"; repo.mkdir()
        sh(["git","init","-b","main"],repo); sh(["git","config","user.email","x@example.invalid"],repo); sh(["git","config","user.name","x"],repo)
        (repo/"one.txt").write_text("one\n"); (repo/"folder").mkdir(); (repo/"folder"/"two.txt").write_text("two\n")
        sh(["git","add","."],repo); sh(["git","commit","-m","base"],repo)
        head=sh(["git","rev-parse","HEAD"],repo)
        (repo/"one.txt").write_text("ONE\n"); (repo/"untracked.txt").write_text("secret-untracked\n")
        authority=Authority.for_repository(repo)
        context=RepositoryContext(repo,None,"main",head)
        result=MacroRunner(Engine(product_registry()),macros).execute(
            request({"observations":["tree_status"],"list_folder":[{"path":"folder"}],"read_file":{"paths":["one.txt","folder/two.txt"]}}),
            authority,context,
        )
        assert result["status"]=="success"
        projected=result["result"]
        assert [x["path"] for x in projected["folders"][0]["entries"]]==["folder/two.txt"]
        assert [x["path"] for x in projected["files"]]==["one.txt","folder/two.txt"]
        tree=projected["observations"]["tree_status"]
        assert tree["head"]==head and tree["branch"]=="main" and tree["detached"] is False
        assert any(x["path"]=="untracked.txt" for x in tree["status"]["entries"])
        assert "ONE" in tree["diff"]["unstaged"] and "ONE" in tree["diff"]["tracked_tree"]
        assert "secret-untracked" not in json.dumps(tree,sort_keys=True)

        failed=MacroRunner(Engine(product_registry()),macros).execute(
            request({"observations":["head"],"read_file":{"paths":["missing.txt","one.txt"]}}),
            authority,context,
        )
        assert failed["status"]=="failure"
        statuses=[x["status"] for x in failed["tasks"]]
        assert "failure" in statuses and statuses[-1]=="not-executed"
    return True
