"""Executable Issue #99 processing-failure vector tests."""

from __future__ import annotations

import json
from pathlib import Path

from specs.tooling.stage2_processing_failure import processing_failure_process
from specs.tooling.stage2_processing_failure_runner import run_manifest


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "specs/tests/fixtures/issue_99"


def test_issue_99_manifest_runs_byte_exactly() -> None:
    assert run_manifest() == []


def test_processor_control_is_closed() -> None:
    input_bytes = (BASE / "processing-failure/input.json").read_bytes()
    control = json.loads(
        (BASE / "processing-failure/processor-control.json").read_text(
            encoding="utf-8"
        )
    )
    assert processing_failure_process(input_bytes, control).exit_status == 3

    for invalid in (
        {},
        {**control, "unexpected": True},
        {**control, "failure_stage": "result-construction"},
    ):
        try:
            processing_failure_process(input_bytes, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid processor control was accepted")
