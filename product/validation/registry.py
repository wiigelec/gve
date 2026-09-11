from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.product_registry import product_registry


def validate_registry() -> bool:
    expected = {
        "filesystem.list", "filesystem.file-read", "filesystem.file-stat",
        "filesystem.file-hash", "filesystem.file-create", "filesystem.file-modify",
        "filesystem.file-delete",
        "git.repository", "git.branch", "git.head", "git.status", "git.status-scope", "git.diff",
        "git.diff-check", "git.branch-create", "git.branch-switch", "git.add",
        "git.commit", "git.fetch", "git.remote-head", "git.push",
        "execute.script",
        "github.issue-read", "github.issue-create", "github.issue-modify",
        "github.pull-request-read", "github.pull-request-create",
        "github.pull-request-modify",
    }
    observed = set(product_registry().identities())
    if observed != expected:
        raise AssertionError(
            f"product registry mismatch missing={sorted(expected-observed)} extra={sorted(observed-expected)}"
        )
    namespaces = {identity.split(".", 1)[0] for identity in observed}
    if namespaces != {"filesystem", "git", "execute", "github"}:
        raise AssertionError(f"plugin namespace mismatch: {sorted(namespaces)}")
    return True
