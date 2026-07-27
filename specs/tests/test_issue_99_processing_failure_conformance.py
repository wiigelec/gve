"""Issue #99 exact processing-failure conformance authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).parent / "fixtures" / "issue_99" / "processing-failure"


def _derived_identity(family: str, *parts: bytes) -> str:
    preimage = b"\\x00".join((family.encode("ascii"), *parts))
    return f"gve-{family}-sha256:{hashlib.sha256(preimage).hexdigest()}"


def test_processing_failure_fixture_is_exact_and_closed() -> None:
    input_bytes = (BASE / "input.json").read_bytes()
    control = json.loads((BASE / "processor-control.json").read_text(encoding="utf-8"))
    result_bytes = (BASE / "result.json").read_bytes()
    result = json.loads(result_bytes)
    authority = json.loads((BASE / "authority.json").read_text(encoding="utf-8"))

    assert control == {
        "schema_version": 1,
        "disposition": "processing-failure",
        "failure_stage": "no-op-disposition",
    }
    request_id = _derived_identity("request", input_bytes)
    result_id = _derived_identity("result", request_id.encode("ascii"), b"processing-failure")
    diagnostic_id = _derived_identity(
        "diagnostic",
        request_id.encode("ascii"),
        b"no-op-disposition",
        b"processing-failure",
    )

    assert result["request_id"] == request_id == authority["fixture"]["request_id"]
    assert result["result_id"] == result_id == authority["fixture"]["result_id"]
    assert result["diagnostics"][0]["diagnostic_id"] == diagnostic_id == authority["fixture"]["diagnostic_id"]
    assert result["processing"] == {"status": "failed", "failure_stage": "no-op-disposition"}
    assert result["workflow"]["status"] == "failed"
    assert [item["status"] for item in result["workflow"]["operations"]] == ["failed"]
    assert result["diagnostics"][0]["code"] == "GVE-S2-PROCESSING-FAILURE"
    assert result["process"] == {
        "exit_code": 3,
        "stdout": "authoritative-result",
        "stderr": "empty",
    }
    expected = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\\n"
    assert result_bytes == expected
    assert (BASE / "stdout.bin").read_bytes() == result_bytes
    assert (BASE / "stderr.bin").read_bytes() == b""


def test_control_is_not_embedded_in_request_bytes() -> None:
    input_value = json.loads((BASE / "input.json").read_text(encoding="utf-8"))
    assert "processor_control" not in input_value
    assert "disposition" not in input_value
    assert "failure_stage" not in input_value
