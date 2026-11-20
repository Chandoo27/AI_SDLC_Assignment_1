from pathlib import Path

from reminder_agent.evaluation import run_evaluation

ROOT = Path(__file__).parents[2]


def test_development_dataset_passes_schema_property_semantic_and_trace_gates(
    tmp_path: Path,
) -> None:
    report = run_evaluation(
        ROOT / "data" / "evaluation" / "v1.jsonl",
        tmp_path / "development-report.json",
    )

    assert report.passed is True
    assert report.total_cases >= 80
    assert report.schema_valid_count == report.total_cases
    assert report.property_valid_count == report.total_cases
    assert report.semantic_correct_count == report.total_cases


def test_heldout_dataset_is_versioned_and_passes_per_operation_gates(
    tmp_path: Path,
) -> None:
    report = run_evaluation(
        ROOT / "data" / "evaluation" / "heldout-v1.jsonl",
        tmp_path / "heldout-report.json",
    )

    assert report.passed is True
    assert report.dataset_version == "heldout-v1"
    assert all(float(metric["rate"]) >= 0.90 for metric in report.operation_metrics.values())
