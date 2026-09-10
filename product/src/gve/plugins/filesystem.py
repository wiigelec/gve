from __future__ import annotations
import hashlib
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

def delete_v(p,a):
    fields(p,{"path","expected_sha256"},{"path","expected_sha256"}); q=rel(p["path"]); d=digest(p["expected_sha256"])
    if not resolve(a,q).is_file(): raise FilesystemPreconditionError("delete target must be regular file")
    return {"path":q,"expected_sha256":d}

def delete_x(p,a):
    t=resolve(a,p["path"]); before=sha(t)
    if before!=p["expected_sha256"]: raise FilesystemPreconditionError("delete digest mismatch",details={"expected":p["expected_sha256"],"observed":before})
    t.unlink()
    return {"effects":{"deleted_paths":[p["path"]]},"result":{"path":p["path"],"previous_sha256":before}}

def tasks():
    return (
      TaskDefinition("filesystem.list",list_v,list_x),
      TaskDefinition("filesystem.file-read",read_v,read_x),
      TaskDefinition("filesystem.file-stat",stat_v,stat_x),
      TaskDefinition("filesystem.file-hash",hash_v,hash_x),
      TaskDefinition("filesystem.file-create",create_v,create_x),
      TaskDefinition("filesystem.file-modify",modify_v,modify_x),
      TaskDefinition("filesystem.file-delete",delete_v,delete_x),
    )
