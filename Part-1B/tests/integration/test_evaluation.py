import json
from pathlib import Path

import pytest

from reminder_agent import evaluation

ACTIONABLE = {
    "create": "create task",
    "reschedule": "reschedule task",
    "snooze": "snooze task",
}


def _case(case_id: str, operation: str, index: int) -> dict[str, object]:
    clarification = operation == "clarification"
    expected: dict[str, object] = {
        "intent": "clarification" if clarification else operation,
        "task": "" if clarification else f"{operation} task {index}",
        "datetime": "" if clarification else "2026-11-20T18:00:00+05:30",
        "needs_clarification": clarification,
        "clarification_question": "What time should I use?" if clarification else "",
    }
    return {
        "case_id": case_id,
        "dataset_version": "test-v1",
        "requirement_ids": ["FR-001"],
        "operation": operation,
        "category": "missing" if clarification else "valid",
        "request": f"synthetic request {index}",
        "context": {
            "reference_time": "2026-11-19T09:00:00+05:30",
            "timezone": "Asia/Kolkata",
            "reminder_tasks": [],
        },
        "expected": expected,
    }


def _write_dataset(path: Path, count: int) -> list[dict[str, object]]:
    operations = ("create", "reschedule", "snooze", "clarification")
    cases = [
        _case(f"EV-TEST-{index:03d}", operations[index % len(operations)], index)
        for index in range(count)
    ]
    path.write_text(
        "".join(json.dumps(case) + "\n" for case in cases),
        encoding="utf-8",
    )
    return cases


def test_evaluation_runs_separate_stages_and_writes_redacted_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_path = tmp_path / "cases.jsonl"
    report_path = tmp_path / "report.json"
    cases = _write_dataset(dataset_path, 20)
    responses = {case["case_id"]: case["expected"] for case in cases}

    def fake_process_request(request: str, context: object) -> dict[str, object]:
        for case in cases:
            if case["request"] == request:
                return responses[str(case["case_id"])]  # type: ignore[return-value]
        raise AssertionError("Unexpected evaluation request")

    monkeypatch.setattr(evaluation, "process_request", fake_process_request)
    report = evaluation.run_evaluation(
        dataset_path,
        report_path,
        min_cases=15,
        validate_traceability=False,
    )

    assert report.passed is True
    assert report.total_cases == 20
    assert report.schema_valid_count == 20
    assert report.property_valid_count == 20
    assert report.semantic_correct_count == 20
    assert set(report.operation_metrics) == {
        "create",
        "reschedule",
        "snooze",
        "clarification",
    }
    saved_report = report_path.read_text(encoding="utf-8")
    assert "synthetic request" not in saved_report
    assert "2026-11-20T18:00:00+05:30" not in saved_report


def test_evaluation_rejects_dataset_below_minimum(tmp_path: Path) -> None:
    dataset_path = tmp_path / "small.jsonl"
    report_path = tmp_path / "report.json"
    _write_dataset(dataset_path, 14)

    with pytest.raises(evaluation.EvaluationInputError):
        evaluation.run_evaluation(
            dataset_path,
            report_path,
            min_cases=15,
            validate_traceability=False,
        )


def test_evaluation_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    dataset_path = tmp_path / "duplicate.jsonl"
    case = _case("EV-DUPLICATE", "create", 1)
    dataset_path.write_text(
        json.dumps(case) + "\n" + json.dumps(case) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(evaluation.EvaluationInputError):
        evaluation.load_cases(dataset_path)
