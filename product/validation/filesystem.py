from __future__ import annotations
import hashlib, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SRC=ROOT/"product"/"src"; sys.path.insert(0,str(SRC))
from gve.authority import Authority
from gve.product_registry import product_registry

def call(name,p,a):
    t=product_registry().resolve(name); return t.execute(t.validate(p,a),a)
def h(s): return hashlib.sha256(s.encode()).hexdigest()
def sh(args,cwd):
    cp=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if cp.returncode: raise AssertionError(cp.stderr)
    return cp.stdout.rstrip("\r\n")

def validate_filesystem_plugin():
    expected={"filesystem.list","filesystem.file-read","filesystem.file-stat","filesystem.file-hash","filesystem.file-create","filesystem.file-modify","filesystem.file-patch","filesystem.file-delete","filesystem.file-move","filesystem.file-delete-recover","filesystem.file-move-recover","filesystem.file-create-recover"}
    identities=set(product_registry().identities())
    if not expected.issubset(identities): raise AssertionError("filesystem registry mismatch")
    with tempfile.TemporaryDirectory() as td:
        r=Path(td).resolve(); a=Authority.for_repository(r)
        sh(["git","init","-b","main"],r); sh(["git","config","user.email","x@example.invalid"],r); sh(["git","config","user.name","x"],r)
        (r/"alpha.txt").write_text("alpha\n"); (r/"dir").mkdir(); (r/"dir"/"beta.txt").write_text("beta")
        sh(["git","add","alpha.txt","dir/beta.txt"],r); sh(["git","commit","-m","base"],r)
        x=call("filesystem.list",{"path":".","recursive":True},a)
        assert [e for e in x["result"]["entries"] if not e.startswith(".git")] == ["alpha.txt","dir","dir/beta.txt"]
        x=call("filesystem.file-read",{"path":"alpha.txt"},a); assert x["result"]=={"content":"alpha\n","sha256":h("alpha\n")}
        assert call("filesystem.file-stat",{"path":"missing"},a)["result"]["kind"]=="missing"
        assert call("filesystem.file-hash",{"path":"alpha.txt"},a)["result"]["sha256"]==h("alpha\n")
        x=call("filesystem.file-create",{"path":"new/deep/file.txt","content":"created"},a)
        assert x["effects"]["created_paths"]==["new","new/deep","new/deep/file.txt"]
        x=call("filesystem.file-modify",{"path":"new/deep/file.txt","expected_sha256":h("created"),"content":"modified"},a)
        assert x["result"]["previous_sha256"]==h("created") and x["result"]["sha256"]==h("modified")
        x=call("filesystem.file-delete",{"path":"new/deep/file.txt","expected_sha256":h("modified")},a)
        assert x["effects"]["deleted_paths"]==["new/deep/file.txt"]

        (r/"delete-recover.txt").write_text("restore me")
        call("filesystem.file-delete",{"path":"delete-recover.txt","expected_sha256":h("restore me")},a)
        (r/"delete-recover.txt").write_text("unrelated")
        try: call("filesystem.file-delete-recover",{"path":"delete-recover.txt","expected_sha256":h("restore me"),"content":"restore me"},a)
        except Exception as e: assert getattr(e,"code",None)=="state-precondition"
        else: raise AssertionError("delete recovery overwrote unrelated content")
        assert (r/"delete-recover.txt").read_text()=="unrelated"
        (r/"delete-recover.txt").unlink()
        x=call("filesystem.file-delete-recover",{"path":"delete-recover.txt","expected_sha256":h("restore me"),"content":"restore me"},a)
        assert (r/"delete-recover.txt").read_text()=="restore me"
        assert x["result"]["sha256"]==h("restore me")

        for label,destination in [("file","occupied.txt"),("directory","occupied-dir")]:
            if label=="file": (r/destination).write_text("occupied")
            else: (r/destination).mkdir()
            try: call("filesystem.file-move",{"path":"dir/beta.txt","destination":destination,"expected_sha256":h("beta")},a)
            except Exception as e: assert getattr(e,"code",None)=="state-precondition"
            else: raise AssertionError("move replaced existing "+label)
        try: call("filesystem.file-move",{"path":"dir/beta.txt","destination":"dir/./beta.txt","expected_sha256":h("beta")},a)
        except Exception as e: assert getattr(e,"code",None)=="state-precondition"
        else: raise AssertionError("move accepted equivalent source and destination")
        try: call("filesystem.file-move",{"path":"dir/beta.txt","destination":"moved/deep/beta.txt","expected_sha256":"0"*64},a)
        except Exception as e: assert getattr(e,"code",None)=="state-precondition"
        else: raise AssertionError("move accepted stale digest")
        assert (r/"dir"/"beta.txt").read_text()=="beta" and not (r/"moved").exists()
        os.symlink("missing-target",r/"move-link")
        try:
            try: call("filesystem.file-move",{"path":"dir/beta.txt","destination":"move-link","expected_sha256":h("beta")},a)
            except Exception as e: assert getattr(e,"code",None)=="state-precondition"
            else: raise AssertionError("move replaced destination symlink")
        finally: (r/"move-link").unlink()
        os.symlink("dir/beta.txt",r/"delete-link")
        try:
            try: call("filesystem.file-delete",{"path":"delete-link","expected_sha256":h("beta")},a)
            except Exception as e: assert getattr(e,"code",None)=="state-precondition"
            else: raise AssertionError("delete accepted symlink target")
            assert (r/"dir"/"beta.txt").read_text()=="beta"
        finally: (r/"delete-link").unlink()

        x=call("filesystem.file-move",{"path":"dir/beta.txt","destination":"moved/deep/beta.txt","expected_sha256":h("beta")},a)
        assert x["effects"]["created_paths"]==["moved","moved/deep"]
        assert not (r/"dir"/"beta.txt").exists() and (r/"moved"/"deep"/"beta.txt").read_text()=="beta"
        (r/"moved"/"unrelated.txt").write_text("keep")
        try: call("filesystem.file-move-recover",{"path":"dir/beta.txt","destination":"moved/deep/beta.txt","expected_sha256":h("beta"),"created_paths":x["effects"]["created_paths"]},a)
        except Exception as e: assert getattr(e,"code",None)=="state-precondition"
        else: raise AssertionError("move recovery removed unrelated content")
        assert not (r/"dir"/"beta.txt").exists() and (r/"moved"/"deep"/"beta.txt").read_text()=="beta"
        (r/"moved"/"unrelated.txt").unlink()
        rx=call("filesystem.file-move-recover",{"path":"dir/beta.txt","destination":"moved/deep/beta.txt","expected_sha256":h("beta"),"created_paths":x["effects"]["created_paths"]},a)
        assert (r/"dir"/"beta.txt").read_text()=="beta" and not (r/"moved").exists()
        assert rx["result"]["removed_paths"]==["moved/deep","moved"]

        patch="--- a/alpha.txt\n+++ b/alpha.txt\n@@ -1 +1 @@\n-alpha\n+omega\n"
        x=call("filesystem.file-patch",{"path":"alpha.txt","expected_sha256":h("alpha\n"),"diff":patch},a)
        assert (r/"alpha.txt").read_text()=="omega\n"
        assert x["result"]["previous_sha256"]==h("alpha\n") and x["result"]["sha256"]==h("omega\n")

        bad_cases=[
            ("stale",{"path":"alpha.txt","expected_sha256":"0"*64,"diff":"--- a/alpha.txt\n+++ b/alpha.txt\n@@ -1 +1 @@\n-omega\n+x\n"}),
            ("wrong-target",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"--- a/other.txt\n+++ b/other.txt\n@@ -1 +1 @@\n-x\n+y\n"}),
            ("multi",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"--- a/alpha.txt\n+++ b/alpha.txt\n@@ -1 +1 @@\n-omega\n+x\n--- a/other.txt\n+++ b/other.txt\n@@ -1 +1 @@\n-a\n+b\n"}),
            ("delete",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"--- a/alpha.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-omega\n"}),
            ("rename",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"diff --git a/alpha.txt b/alpha.txt\nsimilarity index 100%\nrename from alpha.txt\nrename to renamed.txt\n"}),
            ("copy",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"diff --git a/alpha.txt b/alpha.txt\nsimilarity index 100%\ncopy from alpha.txt\ncopy to copied.txt\n"}),
            ("binary",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"diff --git a/alpha.txt b/alpha.txt\nGIT binary patch\nliteral 0\nHcmV?d00001\n"}),
            ("mode",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"diff --git a/alpha.txt b/alpha.txt\nold mode 100644\nnew mode 100755\n"}),
            ("not-applicable",{"path":"alpha.txt","expected_sha256":h("omega\n"),"diff":"--- a/alpha.txt\n+++ b/alpha.txt\n@@ -1 +1 @@\n-not-omega\n+x\n"}),
        ]
        for label,params in bad_cases:
            before=(r/"alpha.txt").read_text()
            try: call("filesystem.file-patch",params,a)
            except Exception: pass
            else: raise AssertionError("unsafe patch accepted: "+label)
            assert (r/"alpha.txt").read_text()==before

        x=call("filesystem.file-create",{"path":"recover/a/b.txt","content":"temporary"},a)
        made=x["effects"]["created_paths"]
        rx=call("filesystem.file-create-recover",{"path":"recover/a/b.txt","expected_sha256":h("temporary"),"created_paths":made},a)
        assert not (r/"recover").exists()
        assert rx["result"]["removed_paths"]==["recover/a/b.txt","recover/a","recover"]
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
    return True
