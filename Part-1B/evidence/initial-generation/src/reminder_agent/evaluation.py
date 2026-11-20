"""Versioned JSONL evaluation, scoring, traceability, and report generation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reminder_agent.engine import context_from_mapping, process_request
from reminder_agent.models import (
    EvaluationCase,
    EvaluationReport,
    EvaluationResult,
    JsonObject,
)
from reminder_agent.validation import (
    InputValidationError,
    ResponseSchemaError,
    response_properties_valid,
    validate_response,
)

SCHEMA_VERSION = "1.0.0"
REQUIRED_REQUIREMENTS = {
    *(f"FR-{number:03d}" for number in range(1, 12)),
    *(f"NFR-{number:03d}" for number in range(1, 9)),
}
REQUIRED_OPERATIONS = {"create", "reschedule", "snooze", "clarification"}
REQUIRED_CATEGORIES = {
    "create": {
        "valid",
        "missing-task",
        "missing-time",
        "ambiguous-time",
        "invalid-time",
        "boundary",
    },
    "reschedule": {
        "valid",
        "missing-target",
        "ambiguous-target",
        "invalid-time",
        "boundary",
    },
    "snooze": {
        "valid",
        "missing-target",
        "ambiguous-target",
        "invalid-time",
        "duration",
        "boundary",
    },
    "clarification": {
        "missing-information",
        "ambiguous-time",
        "ambiguous-target",
        "malformed",
        "unsupported",
        "over-limit",
        "invalid-time",
    },
}
REQUIRED_TEMPORAL_CATEGORIES = {
    "explicit-timezone",
    "past-time",
    "dst-gap",
    "dst-overlap",
}
_ROOT = Path(__file__).parents[2]
DEFAULT_TRACEABILITY_PATH = _ROOT / "data" / "evaluation" / "traceability.json"
_CLARIFICATION_REQUIRED_CATEGORIES = {
    "ambiguous-target",
    "ambiguous-time",
    "dst-gap",
    "dst-overlap",
    "invalid-time",
    "malformed",
    "missing-information",
    "missing-task",
    "missing-target",
    "missing-time",
    "over-limit",
    "past-time",
    "unsupported",
}


class EvaluationInputError(ValueError):
    """Raised when an evaluation dataset or traceability manifest is invalid."""


def load_cases(path: str | Path) -> list[EvaluationCase]:
    dataset_path = Path(path)
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    versions: set[str] = set()

    try:
        lines = dataset_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise EvaluationInputError("DATASET_UNREADABLE") from error

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise EvaluationInputError(f"DATASET_EMPTY_LINE:{line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvaluationInputError(f"DATASET_INVALID_JSON:{line_number}") from error
        if not isinstance(row, dict):
            raise EvaluationInputError(f"DATASET_ROW_NOT_OBJECT:{line_number}")
        try:
            case = _case_from_row(row)
        except (
            KeyError,
            TypeError,
            ValueError,
            InputValidationError,
            ResponseSchemaError,
        ) as error:
            raise EvaluationInputError(f"DATASET_INVALID_CASE:{line_number}") from error
        if case.case_id in seen_ids:
            raise EvaluationInputError(f"DATASET_DUPLICATE_CASE_ID:{case.case_id}")
        seen_ids.add(case.case_id)
        versions.add(case.dataset_version)
        cases.append(case)

    if len(versions) > 1:
        raise EvaluationInputError("DATASET_MIXED_VERSIONS")
    return cases


def run_evaluation(
    dataset_path: str | Path,
    report_path: str | Path,
    *,
    traceability_path: str | Path | None = None,
    min_cases: int = 15,
    validate_traceability: bool = True,
) -> EvaluationReport:
    cases = load_cases(dataset_path)
    if len(cases) < min_cases:
        raise EvaluationInputError(f"DATASET_BELOW_MINIMUM:{min_cases}")
    _validate_operation_coverage(cases)
    _validate_required_categories(cases)

    if validate_traceability:
        manifest_path = Path(traceability_path) if traceability_path else DEFAULT_TRACEABILITY_PATH
        _validate_traceability(manifest_path, cases)

    results: list[EvaluationResult] = []
    clarification_required_count = 0
    clarification_correct_count = 0

    for case in cases:
        expected = case.expected
        expected_needs_clarification = (
            expected["needs_clarification"] is True
            or case.category in _CLARIFICATION_REQUIRED_CATEGORIES
        )
        if expected_needs_clarification:
            clarification_required_count += 1

        actual = process_request(case.request, case.context)
        try:
            validate_response(actual)
            schema_valid = True
        except ResponseSchemaError:
            schema_valid = False

        property_valid = response_properties_valid(actual)
        if expected_needs_clarification:
            property_valid = property_valid and actual.get("needs_clarification") is True
        if not case.request.strip() or len(case.request) > 4096:
            property_valid = property_valid and actual.get("needs_clarification") is True

        semantic_correct = schema_valid and _semantically_equal(actual, expected)
        if expected_needs_clarification and semantic_correct:
            clarification_correct_count += 1

        failure_codes: list[str] = []
        if not schema_valid:
            failure_codes.append("SCHEMA_INVALID")
        if not property_valid:
            failure_codes.append("PROPERTY_INVALID")
        if not semantic_correct:
            failure_codes.append("SEMANTIC_MISMATCH")

        results.append(
            EvaluationResult(
                case_id=case.case_id,
                requirement_ids=case.requirement_ids,
                operation=case.operation,
                category=case.category,
                schema_valid=schema_valid,
                property_valid=property_valid,
                semantic_correct=semantic_correct,
                passed=schema_valid and property_valid and semantic_correct,
                failure_codes=tuple(failure_codes),
            )
        )

    total_cases = len(cases)
    schema_valid_count = sum(result.schema_valid for result in results)
    property_valid_count = sum(result.property_valid for result in results)
    semantic_correct_count = sum(result.semantic_correct for result in results)
    operation_metrics = _operation_metrics(results)
    thresholds: JsonObject = {
        "schema_valid_rate": 1.0,
        "property_valid_rate": 1.0,
        "clarification_rate": 1.0,
        "semantic_overall_rate": 0.95,
        "semantic_per_operation_rate": 0.90,
        "minimum_cases": min_cases,
    }

    passed = (
        schema_valid_count == total_cases
        and property_valid_count == total_cases
        and clarification_required_count > 0
        and clarification_correct_count == clarification_required_count
        and semantic_correct_count / total_cases >= 0.95
        and all(float(metrics["rate"]) >= 0.90 for metrics in operation_metrics.values())
    )
    command = (
        f"python -m reminder_agent.evaluation --dataset {dataset_path} "
        f"--report {report_path} --traceability "
        f"{traceability_path or DEFAULT_TRACEABILITY_PATH} --min-cases {min_cases}"
    )
    report = EvaluationReport(
        schema_version=SCHEMA_VERSION,
        dataset_version=cases[0].dataset_version,
        command=command,
        timestamp_utc=datetime.now(UTC).isoformat(),
        total_cases=total_cases,
        schema_valid_count=schema_valid_count,
        property_valid_count=property_valid_count,
        semantic_correct_count=semantic_correct_count,
        clarification_required_count=clarification_required_count,
        clarification_correct_count=clarification_correct_count,
        case_results=tuple(results),
        operation_metrics=operation_metrics,
        thresholds=thresholds,
        passed=passed,
    )
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _case_from_row(row: dict[str, Any]) -> EvaluationCase:
    case_id = row.get("case_id")
    version = row.get("dataset_version")
    requirement_ids = row.get("requirement_ids")
    operation = row.get("operation")
    category = row.get("category")
    request = row.get("request")
    context_data = row.get("context")
    expected = row.get("expected")

    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("dataset_version")
    if (
        not isinstance(requirement_ids, list)
        or not requirement_ids
        or any(
            not isinstance(item, str) or item not in REQUIRED_REQUIREMENTS
            for item in requirement_ids
        )
    ):
        raise ValueError("requirement_ids")
    if operation not in REQUIRED_OPERATIONS:
        raise ValueError("operation")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category")
    if not isinstance(request, str):
        raise ValueError("request")
    if not isinstance(context_data, dict):
        raise ValueError("context")
    if not isinstance(expected, dict):
        raise ValueError("expected")
    validate_response(expected)

    context = context_from_mapping(context_data)
    return EvaluationCase(
        case_id=case_id,
        dataset_version=version,
        requirement_ids=tuple(requirement_ids),
        operation=operation,
        category=category,
        request=request,
        context=context,
        expected=expected,
    )


def _validate_operation_coverage(cases: list[EvaluationCase]) -> None:
    present = {case.operation for case in cases}
    missing = REQUIRED_OPERATIONS - present
    if missing:
        raise EvaluationInputError("DATASET_MISSING_OPERATIONS:" + ",".join(sorted(missing)))


def _validate_required_categories(cases: list[EvaluationCase]) -> None:
    if len(cases) < 80:
        return
    categories: dict[str, set[str]] = {operation: set() for operation in REQUIRED_OPERATIONS}
    for case in cases:
        categories[case.operation].add(case.category)
    missing = {
        operation: required - categories[operation]
        for operation, required in REQUIRED_CATEGORIES.items()
        if required - categories[operation]
    }
    if missing:
        codes = [
            f"{operation}={','.join(sorted(values))}"
            for operation, values in sorted(missing.items())
        ]
        raise EvaluationInputError("DATASET_MISSING_CATEGORIES:" + ";".join(codes))
    present_temporal_categories = {case.category for case in cases}
    missing_temporal_categories = REQUIRED_TEMPORAL_CATEGORIES - present_temporal_categories
    if missing_temporal_categories:
        raise EvaluationInputError(
            "DATASET_MISSING_TEMPORAL_CATEGORIES:" + ",".join(sorted(missing_temporal_categories))
        )


def _validate_traceability(path: Path, cases: list[EvaluationCase]) -> None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise EvaluationInputError("TRACEABILITY_UNREADABLE") from error
    except json.JSONDecodeError as error:
        raise EvaluationInputError("TRACEABILITY_INVALID_JSON") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("requirements"), dict):
        raise EvaluationInputError("TRACEABILITY_INVALID_SHAPE")

    requirements = manifest["requirements"]
    missing_requirements = REQUIRED_REQUIREMENTS - set(requirements)
    if missing_requirements:
        raise EvaluationInputError(
            "TRACEABILITY_MISSING_REQUIREMENTS:" + ",".join(sorted(missing_requirements))
        )
    cases_by_id = {case.case_id: case for case in cases}
    dataset_version = cases[0].dataset_version
    for requirement_id in sorted(REQUIRED_REQUIREMENTS):
        entry = requirements[requirement_id]
        if not isinstance(entry, dict):
            raise EvaluationInputError(f"TRACEABILITY_INVALID_ENTRY:{requirement_id}")
        case_ids_by_dataset = entry.get("evaluation_case_ids_by_dataset")
        if not isinstance(case_ids_by_dataset, dict):
            raise EvaluationInputError(f"TRACEABILITY_MISSING_LINK:{requirement_id}")
        primary_case_ids = case_ids_by_dataset.get("v1")
        if not _is_nonempty_string_list(primary_case_ids):
            raise EvaluationInputError(f"TRACEABILITY_MISSING_LINK:{requirement_id}")
        case_ids = case_ids_by_dataset.get(dataset_version)
        test_ids = entry.get("test_ids")
        implementation_refs = entry.get("implementation_refs")
        if not _is_nonempty_string_list(test_ids):
            raise EvaluationInputError(f"TRACEABILITY_MISSING_LINK:{requirement_id}")
        if not _is_nonempty_string_list(implementation_refs):
            raise EvaluationInputError(f"TRACEABILITY_MISSING_LINK:{requirement_id}")
        if case_ids is None or case_ids == []:
            if dataset_version == "v1":
                raise EvaluationInputError(f"TRACEABILITY_MISSING_LINK:{requirement_id}")
            continue
        if not _is_nonempty_string_list(case_ids):
            raise EvaluationInputError(f"TRACEABILITY_INVALID_ENTRY:{requirement_id}")
        if any(case_id not in cases_by_id for case_id in case_ids):
            raise EvaluationInputError(f"TRACEABILITY_UNKNOWN_CASE:{requirement_id}")
        for case_id in case_ids:
            if requirement_id not in cases_by_id[case_id].requirement_ids:
                raise EvaluationInputError(f"TRACEABILITY_CASE_MISMATCH:{requirement_id}")


def _is_nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() and "*" not in item for item in value)
    )


def _operation_metrics(results: list[EvaluationResult]) -> dict[str, JsonObject]:
    grouped: dict[str, list[EvaluationResult]] = {
        operation: [] for operation in sorted(REQUIRED_OPERATIONS)
    }
    for result in results:
        grouped[result.operation].append(result)
    metrics: dict[str, JsonObject] = {}
    for operation, operation_results in grouped.items():
        total = len(operation_results)
        correct = sum(result.semantic_correct for result in operation_results)
        metrics[operation] = {
            "semantic_correct": correct,
            "total": total,
            "rate": correct / total if total else 0.0,
        }
    return metrics


def _semantically_equal(actual: object, expected: object) -> bool:
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        return False
    if (
        actual.get("intent") != expected.get("intent")
        or actual.get("needs_clarification") != expected.get("needs_clarification")
        or _normalize_text(actual.get("task")) != _normalize_text(expected.get("task"))
    ):
        return False
    if actual.get("needs_clarification") is True:
        return _normalize_text(actual.get("clarification_question")) == _normalize_text(
            expected.get("clarification_question")
        )
    try:
        actual_time = datetime.fromisoformat(str(actual["datetime"]).replace("Z", "+00:00"))
        expected_time = datetime.fromisoformat(str(expected["datetime"]).replace("Z", "+00:00"))
        return actual_time.astimezone(UTC) == expected_time.astimezone(UTC)
    except (KeyError, OverflowError, TypeError, ValueError):
        return False


def _normalize_text(value: object) -> str:
    return " ".join(re.sub(r"\s+", " ", str(value or "")).casefold().split())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the reminder-agent JSONL evaluator.")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--traceability", type=Path, default=DEFAULT_TRACEABILITY_PATH)
    parser.add_argument("--min-cases", type=int, default=15)
    args = parser.parse_args(argv)
    try:
        report = run_evaluation(
            args.dataset,
            args.report,
            traceability_path=args.traceability,
            min_cases=args.min_cases,
        )
    except EvaluationInputError as error:
        print(json.dumps({"passed": False, "error_code": str(error)}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "passed": report.passed,
                "dataset_version": report.dataset_version,
                "total_cases": report.total_cases,
                "report": str(args.report),
            }
        )
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
