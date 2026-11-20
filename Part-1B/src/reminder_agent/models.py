"""Typed data structures shared by the reminder agent and evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

Intent = Literal["create", "reschedule", "snooze", "clarification"]
Operation = Intent
JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ResolutionContext:
    reference_time: datetime | None = None
    timezone: str | None = None
    reminder_tasks: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReminderRequest:
    text: str
    context: ResolutionContext = field(default_factory=ResolutionContext)


@dataclass(frozen=True)
class ParsedReminderRequest:
    intent: Intent
    task: str
    temporal_expression: str = ""
    resolved_datetime: datetime | None = None
    clarification_reason: str | None = None
    clarification_question: str = ""


@dataclass(frozen=True)
class ReminderResponse:
    intent: Intent
    task: str
    datetime: str
    needs_clarification: bool
    clarification_question: str

    def to_dict(self) -> JsonObject:
        return {
            "intent": self.intent,
            "task": self.task,
            "datetime": self.datetime,
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
        }


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    dataset_version: str
    requirement_ids: tuple[str, ...]
    operation: Operation
    category: str
    request: str
    context: ResolutionContext
    expected: JsonObject


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    requirement_ids: tuple[str, ...]
    operation: Operation
    category: str
    schema_valid: bool
    property_valid: bool
    semantic_correct: bool
    passed: bool
    failure_codes: tuple[str, ...] = ()

    def to_dict(self) -> JsonObject:
        return {
            "case_id": self.case_id,
            "requirement_ids": list(self.requirement_ids),
            "operation": self.operation,
            "category": self.category,
            "schema_valid": self.schema_valid,
            "property_valid": self.property_valid,
            "semantic_correct": self.semantic_correct,
            "passed": self.passed,
            "failure_codes": list(self.failure_codes),
        }


@dataclass(frozen=True)
class EvaluationReport:
    schema_version: str
    dataset_version: str
    command: str
    timestamp_utc: str
    total_cases: int
    schema_valid_count: int
    property_valid_count: int
    semantic_correct_count: int
    clarification_required_count: int
    clarification_correct_count: int
    case_results: tuple[EvaluationResult, ...]
    operation_metrics: dict[str, JsonObject]
    thresholds: JsonObject
    passed: bool

    def to_dict(self) -> JsonObject:
        return {
            "schema_version": self.schema_version,
            "dataset_version": self.dataset_version,
            "command": self.command,
            "timestamp_utc": self.timestamp_utc,
            "total_cases": self.total_cases,
            "schema_valid": {
                "valid": self.schema_valid_count,
                "total": self.total_cases,
                "rate": self.schema_valid_count / self.total_cases,
            },
            "property_valid": {
                "valid": self.property_valid_count,
                "total": self.total_cases,
                "rate": self.property_valid_count / self.total_cases,
            },
            "semantic_correct": {
                "valid": self.semantic_correct_count,
                "total": self.total_cases,
                "rate": self.semantic_correct_count / self.total_cases,
            },
            "clarification_required": {
                "correct": self.clarification_correct_count,
                "total": self.clarification_required_count,
                "rate": (
                    self.clarification_correct_count / self.clarification_required_count
                    if self.clarification_required_count
                    else 1.0
                ),
            },
            "operation_metrics": self.operation_metrics,
            "thresholds": self.thresholds,
            "cases": [result.to_dict() for result in self.case_results],
            "passed": self.passed,
        }
