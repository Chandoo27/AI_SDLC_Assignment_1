import json
from pathlib import Path

import pytest

from reminder_agent.evaluation import (
    DEFAULT_TRACEABILITY_PATH,
    EvaluationInputError,
    _validate_traceability,
    load_cases,
)

ROOT = Path(__file__).parents[2]
DATASET = ROOT / "data" / "evaluation" / "v1.jsonl"


def test_all_requirements_have_concrete_case_test_and_implementation_links() -> None:
    cases = load_cases(DATASET)
    _validate_traceability(DEFAULT_TRACEABILITY_PATH, cases)


def test_traceability_fails_on_missing_test_link(tmp_path: Path) -> None:
    manifest = json.loads(DEFAULT_TRACEABILITY_PATH.read_text(encoding="utf-8"))
    manifest["requirements"]["FR-001"]["test_ids"] = []
    path = tmp_path / "traceability.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(EvaluationInputError, match="TRACEABILITY_MISSING_LINK"):
        _validate_traceability(path, load_cases(DATASET))


def test_traceability_fails_when_case_does_not_cover_requirement(tmp_path: Path) -> None:
    manifest = json.loads(DEFAULT_TRACEABILITY_PATH.read_text(encoding="utf-8"))
    manifest["requirements"]["FR-001"]["evaluation_case_ids_by_dataset"]["v1"] = ["EV-CLARIFY-001"]
    path = tmp_path / "traceability.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(EvaluationInputError, match="TRACEABILITY_CASE_MISMATCH"):
        _validate_traceability(path, load_cases(DATASET))
