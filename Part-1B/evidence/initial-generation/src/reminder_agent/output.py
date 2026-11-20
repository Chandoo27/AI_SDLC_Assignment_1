"""Build and serialize schema-conforming public responses."""

from __future__ import annotations

import json
from typing import Any, Literal

from reminder_agent.models import Intent
from reminder_agent.validation import validate_response


def build_response(
    *,
    intent: Intent,
    task: str = "",
    datetime_value: str = "",
    needs_clarification: bool = False,
    clarification_question: str = "",
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "intent": intent,
        "task": task,
        "datetime": datetime_value,
        "needs_clarification": needs_clarification,
        "clarification_question": clarification_question,
    }
    validate_response(response)
    return response


def serialize_response(response: dict[str, Any]) -> str:
    validate_response(response)
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))


def clarification_response(
    question: str, *, task: str = "", datetime_value: str = ""
) -> dict[str, Any]:
    return build_response(
        intent="clarification",
        task=task,
        datetime_value=datetime_value,
        needs_clarification=True,
        clarification_question=question,
    )


def action_response(
    intent: Literal["create", "reschedule", "snooze"], task: str, datetime_value: str
) -> dict[str, Any]:
    return build_response(intent=intent, task=task, datetime_value=datetime_value)


__all__ = [
    "action_response",
    "build_response",
    "clarification_response",
    "serialize_response",
    "validate_response",
]
