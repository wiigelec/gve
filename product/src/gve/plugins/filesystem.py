from __future__ import annotations
import hashlib
import subprocess
from pathlib import Path
from typing import Any
from ..authority import Authority
from ..errors import GVEError
from ..registry import TaskDefinition

class FilesystemError(GVEError): code = "filesystem"
class FilesystemAuthorityError(GVEError): code = "authority"
class FilesystemPreconditionError(GVEError): code = "state-precondition"

def fields(p, allowed, required):
    u=set(p)-allowed; m=required-set(p)
    if u or m: raise FilesystemError("invalid filesystem parameters", details={"unknown":sorted(u),"missing":sorted(m)})

def rel(v):
    if not isinstance(v,str) or not v: raise FilesystemError("path must be non-empty string")
    q=v.replace("\\","/")
    if Path(q).is_absolute(): raise FilesystemAuthorityError("path must be repository-relative")
    return q

def root(a): return a.repository.resolve()

def resolve(a,p):
    r=root(a); c=(r/p).resolve(strict=False)
    try: c.relative_to(r)
    except ValueError: raise FilesystemAuthorityError("path escapes repository", details={"path":p})
    return c

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576), b""): h.update(b)
    return h.hexdigest()

def digest(v):
    if not isinstance(v,str) or len(v)!=64 or any(c not in "0123456789abcdef" for c in v):
        raise FilesystemError("expected_sha256 must be lowercase SHA-256")
    return v

def kind(p):
    if p.is_symlink(): return "symlink"
    if p.is_file(): return "file"
    if p.is_dir(): return "directory"
    return "other"

def list_v(p,a):
    fields(p,{"path","recursive"},set()); q=rel(p.get("path","."))
    rec=p.get("recursive",False)
    if not isinstance(rec,bool): raise FilesystemError("recursive must be boolean")
    if not resolve(a,q).is_dir(): raise FilesystemPreconditionError("list target must be directory")
    return {"path":q,"recursive":rec}

def list_x(p,a):
    r=root(a); b=resolve(a,p["path"]); it=b.rglob("*") if p["recursive"] else b.iterdir(); obs=[]
    for x in it:
        rp=x.relative_to(r).as_posix()
        y=x.resolve(strict=False)
        try: y.relative_to(r)
        except ValueError: raise FilesystemAuthorityError("list encountered symlink escape",details={"path":rp})
        obs.append({"path":rp,"kind":kind(x)})
    obs.sort(key=lambda z:z["path"])
    return {"observations":{"entries":obs},"result":{"entries":[z["path"] for z in obs]}}

def read_v(p,a):
    fields(p,{"path","encoding"},{"path"}); q=rel(p["path"])
    if p.get("encoding","utf-8")!="utf-8": raise FilesystemError("only utf-8 supported")
    if not resolve(a,q).is_file(): raise FilesystemPreconditionError("read target must be regular file")
    return {"path":q}

def read_x(p,a):
    q=resolve(a,p["path"])
    try: content=q.read_text(encoding="utf-8")
    except UnicodeDecodeError as e: raise FilesystemError("file is not valid utf-8") from e
    d=sha(q)
    return {"observations":{"path":p["path"],"sha256":d},"result":{"content":content,"sha256":d}}

def stat_v(p,a):
    fields(p,{"path"},{"path"}); q=rel(p["path"]); resolve(a,q); return {"path":q}

def stat_x(p,a):
    r=root(a); raw=r/p["path"]; resolved=resolve(a,p["path"])
    if not raw.exists() and not raw.is_symlink():
        z={"path":p["path"],"kind":"missing","size":None}; return {"observations":dict(z),"result":z}
    z={"path":p["path"],"kind":kind(raw),"size":raw.lstat().st_size}
    if z["kind"]=="file" and resolved.is_file(): z["sha256"]=sha(resolved)
    return {"observations":dict(z),"result":z}

def hash_v(p,a):
    fields(p,{"path"},{"path"}); q=rel(p["path"])
    if not resolve(a,q).is_file(): raise FilesystemPreconditionError("hash target must be regular file")
    return {"path":q}

def hash_x(p,a):
    d=sha(resolve(a,p["path"])); return {"observations":{"path":p["path"],"sha256":d},"result":{"sha256":d}}

def create_v(p,a):
    fields(p,{"path","content"},{"path","content"}); q=rel(p["path"])
    if not isinstance(p["content"],str): raise FilesystemError("content must be string")
    raw=root(a)/q; target=resolve(a,q)
    if target.exists() or raw.is_symlink(): raise FilesystemPreconditionError("create target exists")
    return {"path":q,"content":p["content"]}

def create_x(p,a):
    r=root(a); t=resolve(a,p["path"]); missing=[]; d=t.parent
    while d!=r and not d.exists(): missing.append(d); d=d.parent
    if d.exists():
        try: d.resolve(strict=True).relative_to(r)
        except ValueError: raise FilesystemAuthorityError("create parent escapes repository")
    made=[]
    for d in reversed(missing): d.mkdir(); made.append(d.relative_to(r).as_posix())
    t.write_text(p["content"],encoding="utf-8"); h=sha(t)
    made.append(p["path"])
    return {"effects":{"created_paths":made},"result":{"path":p["path"],"sha256":h}}

def modify_v(p,a):
    fields(p,{"path","expected_sha256","content"},{"path","expected_sha256","content"})
    q=rel(p["path"]); d=digest(p["expected_sha256"])
    if not isinstance(p["content"],str): raise FilesystemError("content must be string")
    if not resolve(a,q).is_file(): raise FilesystemPreconditionError("modify target must be regular file")
    return {"path":q,"expected_sha256":d,"content":p["content"]}

def modify_x(p,a):
    t=resolve(a,p["path"]); before=sha(t)
    if before!=p["expected_sha256"]: raise FilesystemPreconditionError("modify digest mismatch",details={"expected":p["expected_sha256"],"observed":before})
    t.write_text(p["content"],encoding="utf-8"); after=sha(t)
    return {"effects":{"modified_paths":[p["path"]]},"result":{"path":p["path"],"previous_sha256":before,"sha256":after}}

def patch_v(p,a):
    fields(p,{"path","expected_sha256","diff"},{"path","expected_sha256","diff"})
    q=rel(p["path"]); d=digest(p["expected_sha256"]); diff=p["diff"]
    if not isinstance(diff,str) or not diff:
        raise FilesystemError("diff must be non-empty string")
    target=resolve(a,q)
    if not target.is_file():
        raise FilesystemPreconditionError("patch target must be regular file")
    try: target.read_text(encoding="utf-8")
    except UnicodeDecodeError as e: raise FilesystemError("patch target is not valid utf-8") from e
    observed=sha(target)
    if observed!=d:
        raise FilesystemPreconditionError("patch digest mismatch",details={"expected":d,"observed":observed})
    forbidden=("GIT binary patch","Binary files ","rename from ","rename to ","copy from ","copy to ","deleted file mode ","new file mode ","old mode ","new mode ","similarity index ","dissimilarity index ")
    if any(token in diff for token in forbidden):
        raise FilesystemError("unsupported patch form")
    lines=diff.splitlines()
    old_headers=[line[4:].split("\t",1)[0] for line in lines if line.startswith("--- ")]
    new_headers=[line[4:].split("\t",1)[0] for line in lines if line.startswith("+++ ")]
    if len(old_headers)!=1 or len(new_headers)!=1:
        raise FilesystemError("patch must contain exactly one file header pair")
    if old_headers[0] not in {q,"a/"+q} or new_headers[0] not in {q,"b/"+q}:
        raise FilesystemAuthorityError("patch target does not match declared path",details={"path":q,"old":old_headers[0],"new":new_headers[0]})
    git_headers=[line for line in lines if line.startswith("diff --git ")]
    if len(git_headers)>1:
        raise FilesystemError("patch contains multiple file sections")
    if git_headers and git_headers[0]!=f"diff --git a/{q} b/{q}":
        raise FilesystemAuthorityError("patch git header does not match declared path",details={"path":q})
    cp=subprocess.run(["git","-C",str(root(a)),"apply","--check","--whitespace=nowarn","-"],input=diff,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if cp.returncode!=0:
        raise FilesystemPreconditionError("patch does not apply cleanly",details={"stderr":cp.stderr.rstrip("\r\n")})
    return {"path":q,"expected_sha256":d,"diff":diff}

def patch_x(p,a):
    target=resolve(a,p["path"]); before=sha(target)
    if before!=p["expected_sha256"]:
        raise FilesystemPreconditionError("patch digest mismatch",details={"expected":p["expected_sha256"],"observed":before})
    cp=subprocess.run(["git","-C",str(root(a)),"apply","--whitespace=nowarn","-"],input=p["diff"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if cp.returncode!=0:
        raise FilesystemError("checked patch application failed",details={"stderr":cp.stderr.rstrip("\r\n")})
    after=sha(target)
    return {"effects":{"modified_paths":[p["path"]]},"result":{"path":p["path"],"previous_sha256":before,"sha256":after}}

def delete_v(p,a):
    fields(p,{"path","expected_sha256"},{"path","expected_sha256"}); q=rel(p["path"]); d=digest(p["expected_sha256"])
    raw=root(a)/q; target=resolve(a,q)
    if raw.is_symlink() or not target.is_file(): raise FilesystemPreconditionError("delete target must be regular file")
    return {"path":q,"expected_sha256":d}

def delete_x(p,a):
    raw=root(a)/p["path"]; t=resolve(a,p["path"])
    if raw.is_symlink() or not t.is_file(): raise FilesystemPreconditionError("delete target must be regular file")
    before=sha(t)
    if before!=p["expected_sha256"]: raise FilesystemPreconditionError("delete digest mismatch",details={"expected":p["expected_sha256"],"observed":before})
    t.unlink()
    return {"effects":{"deleted_paths":[p["path"]]},"result":{"path":p["path"],"previous_sha256":before}}


def move_v(p,a):
    fields(p,{"path","destination","expected_sha256"},{"path","destination","expected_sha256"})
    source=rel(p["path"]); destination=rel(p["destination"]); d=digest(p["expected_sha256"])
    source_target=resolve(a,source); destination_target=resolve(a,destination)
    raw_source=root(a)/source
    if source_target==destination_target:
        raise FilesystemPreconditionError("move source and destination must be distinct")
    if raw_source.is_symlink() or not source_target.is_file():
        raise FilesystemPreconditionError("move source must be regular file")
    raw_destination=root(a)/destination
    if destination_target.exists() or raw_destination.is_symlink():
        raise FilesystemPreconditionError("move destination exists")
    return {"path":source,"destination":destination,"expected_sha256":d}

def move_x(p,a):
    r=root(a); source=resolve(a,p["path"]); destination=resolve(a,p["destination"])
    raw_source=r/p["path"]
    if raw_source.is_symlink() or not source.is_file():
        raise FilesystemPreconditionError("move source must be regular file")
    before=sha(source)
    if before!=p["expected_sha256"]:
        raise FilesystemPreconditionError("move digest mismatch",details={"expected":p["expected_sha256"],"observed":before})
    raw_destination=r/p["destination"]
    if destination.exists() or raw_destination.is_symlink():
        raise FilesystemPreconditionError("move destination exists")
    missing=[]; d=destination.parent
    while d!=r and not d.exists():
        missing.append(d); d=d.parent
    if not d.is_dir():
        raise FilesystemPreconditionError("move destination parent must be directory")
    try: d.resolve(strict=True).relative_to(r)
    except ValueError: raise FilesystemAuthorityError("move destination parent escapes repository")
    made=[]
    for directory in reversed(missing):
        directory.mkdir(); made.append(directory.relative_to(r).as_posix())
    source.rename(destination)
    return {
        "effects":{"moved_paths":[p["path"],p["destination"]],"created_paths":made},
        "result":{"path":p["path"],"destination":p["destination"],"sha256":before,"created_paths":made},
    }

def recover_deleted_v(p,a):
    fields(p,{"path","expected_sha256","content"},{"path","expected_sha256","content"})
    q=rel(p["path"]); d=digest(p["expected_sha256"]); content=p["content"]
    if not isinstance(content,str): raise FilesystemError("content must be string")
    if hashlib.sha256(content.encode("utf-8")).hexdigest()!=d:
        raise FilesystemPreconditionError("delete recovery content digest mismatch")
    raw=root(a)/q; target=resolve(a,q)
    if target.exists() or raw.is_symlink():
        raise FilesystemPreconditionError("delete recovery target exists")
    if not target.parent.is_dir():
        raise FilesystemPreconditionError("delete recovery parent must be existing directory")
    return {"path":q,"expected_sha256":d,"content":content}

def recover_deleted_x(p,a):
    raw=root(a)/p["path"]; target=resolve(a,p["path"])
    if target.exists() or raw.is_symlink():
        raise FilesystemPreconditionError("delete recovery target exists")
    if not target.parent.is_dir():
        raise FilesystemPreconditionError("delete recovery parent must be existing directory")
    target.write_text(p["content"],encoding="utf-8")
    observed=sha(target)
    if observed!=p["expected_sha256"]:
        target.unlink()
        raise FilesystemPreconditionError("delete recovery recreated digest mismatch",details={"expected":p["expected_sha256"],"observed":observed})
    return {"effects":{"created_paths":[p["path"]]},"result":{"path":p["path"],"sha256":observed}}

def recover_moved_v(p,a):
    fields(p,{"path","destination","expected_sha256","created_paths"},{"path","destination","expected_sha256","created_paths"})
    source=rel(p["path"]); destination=rel(p["destination"]); d=digest(p["expected_sha256"]); paths=p["created_paths"]
    source_target=resolve(a,source); destination_target=resolve(a,destination)
    if source_target==destination_target:
        raise FilesystemPreconditionError("move recovery source and destination must be distinct")
    if not isinstance(paths,list) or any(not isinstance(x,str) or not x for x in paths):
        raise FilesystemError("created_paths must be a string array")
    normalized=[rel(x) for x in paths]
    if len(set(normalized))!=len(normalized): raise FilesystemError("created_paths must be unique")
    destination_parent=Path(destination).parent
    for item in normalized:
        resolve(a,item)
        item_path=Path(item)
        if item_path==Path(destination) or item_path not in destination_parent.parents and item_path!=destination_parent:
            raise FilesystemError("created_paths must be destination parent directories")
    raw_source=root(a)/source
    if source_target.exists() or raw_source.is_symlink():
        raise FilesystemPreconditionError("move recovery source exists")
    raw_destination=root(a)/destination
    if raw_destination.is_symlink() or not destination_target.is_file():
        raise FilesystemPreconditionError("move recovery destination must be regular file")
    return {"path":source,"destination":destination,"expected_sha256":d,"created_paths":normalized}

def recover_moved_x(p,a):
    r=root(a); source=resolve(a,p["path"]); destination=resolve(a,p["destination"])
    raw_source=r/p["path"]
    if source.exists() or raw_source.is_symlink():
        raise FilesystemPreconditionError("move recovery source exists")
    if not source.parent.is_dir():
        raise FilesystemPreconditionError("move recovery source parent must be existing directory")
    raw_destination=r/p["destination"]
    if raw_destination.is_symlink() or not destination.is_file():
        raise FilesystemPreconditionError("move recovery destination must be regular file")
    observed=sha(destination)
    if observed!=p["expected_sha256"]:
        raise FilesystemPreconditionError("move recovery destination digest mismatch",details={"expected":p["expected_sha256"],"observed":observed})
    created=set(p["created_paths"])
    for relpath in reversed(p["created_paths"]):
        directory=resolve(a,relpath)
        if not directory.is_dir():
            raise FilesystemPreconditionError("move recovery created parent is not directory",details={"path":relpath})
        children={child.relative_to(r).as_posix() for child in directory.iterdir()}
        allowed={p["destination"]} if Path(p["destination"]).parent.as_posix()==relpath else set()
        allowed|={item for item in created if Path(item).parent.as_posix()==relpath}
        if children-allowed:
            raise FilesystemPreconditionError("move recovery created parent contains unrelated content",details={"path":relpath,"unexpected":sorted(children-allowed)})
    destination.rename(source)
    removed=[]
    for relpath in reversed(p["created_paths"]):
        resolve(a,relpath).rmdir(); removed.append(relpath)
    return {
        "effects":{"moved_paths":[p["destination"],p["path"]],"deleted_paths":removed},
        "result":{"path":p["path"],"destination":p["destination"],"sha256":observed,"removed_paths":removed},
    }

def recover_created_v(p,a):
    fields(p,{"path","expected_sha256","created_paths"},{"path","expected_sha256","created_paths"})
    q=rel(p["path"]); d=digest(p["expected_sha256"]); paths=p["created_paths"]
    if not isinstance(paths,list) or not paths or any(not isinstance(x,str) or not x for x in paths):
        raise FilesystemError("created_paths must be a non-empty string array")
    normalized=[rel(x) for x in paths]
    if len(set(normalized))!=len(normalized): raise FilesystemError("created_paths must be unique")
    if normalized[-1]!=q: raise FilesystemError("created_paths must end with target path")
    for item in normalized: resolve(a,item)
    return {"path":q,"expected_sha256":d,"created_paths":normalized}

def recover_created_x(p,a):
    r=root(a); target=resolve(a,p["path"])
    if not target.is_file(): raise FilesystemPreconditionError("recovery target must be regular file")
    observed=sha(target)
    if observed!=p["expected_sha256"]: raise FilesystemPreconditionError("recovery target digest mismatch",details={"expected":p["expected_sha256"],"observed":observed})
    created=set(p["created_paths"]); parents=p["created_paths"][:-1]
    for relpath in reversed(parents):
        directory=resolve(a,relpath)
        if not directory.is_dir(): raise FilesystemPreconditionError("recovery created parent is not directory",details={"path":relpath})
        children={child.relative_to(r).as_posix() for child in directory.iterdir()}
        allowed={item for item in created if Path(item).parent.as_posix()==relpath}
        if children-allowed: raise FilesystemPreconditionError("recovery created parent is no longer empty of unrelated content",details={"path":relpath,"unexpected":sorted(children-allowed)})
    target.unlink(); removed=[p["path"]]
    for relpath in reversed(parents): resolve(a,relpath).rmdir(); removed.append(relpath)
    return {"effects":{"deleted_paths":removed},"result":{"path":p["path"],"previous_sha256":observed,"removed_paths":removed}}

def tasks():
    return (
      TaskDefinition("filesystem.list",list_v,list_x),
      TaskDefinition("filesystem.file-read",read_v,read_x),
      TaskDefinition("filesystem.file-stat",stat_v,stat_x),
      TaskDefinition("filesystem.file-hash",hash_v,hash_x),
      TaskDefinition("filesystem.file-create",create_v,create_x),
      TaskDefinition("filesystem.file-modify",modify_v,modify_x),
      TaskDefinition("filesystem.file-patch",patch_v,patch_x),
      TaskDefinition("filesystem.file-delete",delete_v,delete_x),
      TaskDefinition("filesystem.file-move",move_v,move_x),
      TaskDefinition("filesystem.file-delete-recover",recover_deleted_v,recover_deleted_x),
      TaskDefinition("filesystem.file-move-recover",recover_moved_v,recover_moved_x),
      TaskDefinition("filesystem.file-create-recover",recover_created_v,recover_created_x),
    )
