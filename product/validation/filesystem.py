from __future__ import annotations
import hashlib, os, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SRC=ROOT/"product"/"src"; sys.path.insert(0,str(SRC))
from gve.authority import Authority
from gve.product_registry import product_registry

def call(name,p,a):
    t=product_registry().resolve(name); return t.execute(t.validate(p,a),a)
def h(s): return hashlib.sha256(s.encode()).hexdigest()

def validate_filesystem_plugin():
    expected={"filesystem.list","filesystem.file-read","filesystem.file-stat","filesystem.file-hash","filesystem.file-create","filesystem.file-modify","filesystem.file-delete"}
    identities=set(product_registry().identities())
    if not expected.issubset(identities): raise AssertionError("filesystem registry mismatch")
    with tempfile.TemporaryDirectory() as td:
        r=Path(td).resolve(); a=Authority.for_repository(r)
        (r/"alpha.txt").write_text("alpha"); (r/"dir").mkdir(); (r/"dir"/"beta.txt").write_text("beta")
        x=call("filesystem.list",{"path":".","recursive":True},a)
        assert x["result"]["entries"]==["alpha.txt","dir","dir/beta.txt"]
        x=call("filesystem.file-read",{"path":"alpha.txt"},a); assert x["result"]=={"content":"alpha","sha256":h("alpha")}
        assert call("filesystem.file-stat",{"path":"missing"},a)["result"]["kind"]=="missing"
        assert call("filesystem.file-hash",{"path":"alpha.txt"},a)["result"]["sha256"]==h("alpha")
        x=call("filesystem.file-create",{"path":"new/deep/file.txt","content":"created"},a)
        assert x["effects"]["created_paths"]==["new","new/deep","new/deep/file.txt"]
        x=call("filesystem.file-modify",{"path":"new/deep/file.txt","expected_sha256":h("created"),"content":"modified"},a)
        assert x["result"]["previous_sha256"]==h("created") and x["result"]["sha256"]==h("modified")
        x=call("filesystem.file-delete",{"path":"new/deep/file.txt","expected_sha256":h("modified")},a)
        assert x["effects"]["deleted_paths"]==["new/deep/file.txt"]
        try: call("filesystem.file-stat",{"path":"../escape"},a)
        except Exception as e: assert getattr(e,"code",None)=="authority"
        else: raise AssertionError("traversal escape accepted")
        outside=r.parent/(r.name+"-outside"); outside.write_text("x")
        try:
            os.symlink(outside,r/"escape-link")
            try: call("filesystem.file-read",{"path":"escape-link"},a)
            except Exception as e: assert getattr(e,"code",None)=="authority"
            else: raise AssertionError("symlink escape accepted")
        finally: outside.unlink(missing_ok=True)
        (r/"guarded").write_text("current")
        try: call("filesystem.file-modify",{"path":"guarded","expected_sha256":"0"*64,"content":"bad"},a)
        except Exception as e: assert getattr(e,"code",None)=="state-precondition"
        else: raise AssertionError("wrong digest accepted")
        assert (r/"guarded").read_text()=="current"
    return True
