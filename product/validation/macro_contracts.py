from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"product"/"src"
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from gve.product_macro_registry import product_macro_registry

def validate_macro_contracts():
    macros=product_macro_registry()
    discover=macros.resolve("discover").parameter_schema
    assert discover["type"]=="object" and discover["additionalProperties"] is False
    assert set(discover["properties"])=={"observations","list_folder","read_file"}
    assert "tree_status" in discover["properties"]["observations"]["items"]["enum"]

    modify=macros.resolve("modify").parameter_schema
    assert modify["type"]=="object" and modify["additionalProperties"] is False
    variants=modify["properties"]["changes"]["items"]["oneOf"]
    create=[v for v in variants if v["properties"]["operation"]["enum"]==["create"]]
    mods=[v for v in variants if v["properties"]["operation"]["enum"]==["modify"]]
    assert len(create)==1 and len(mods)==2
    assert set(create[0]["required"])=={"operation","path","content"}
    assert {frozenset(v["required"]) for v in mods}=={
        frozenset({"operation","path","content","expected_sha256"}),
        frozenset({"operation","path","diff","expected_sha256"}),
    }
    assert modify["properties"]["changes"]["x-gve-unique-path-field-after-normalization"]=="path"

    issue=macros.resolve("issue").parameter_schema
    pr=macros.resolve("pr").parameter_schema
    assert issue["type"]=="object" and pr["type"]=="object"
    return True
