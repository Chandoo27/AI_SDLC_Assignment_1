"""Public request-to-response orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from reminder_agent.models import ReminderRequest, ResolutionContext
from reminder_agent.output import action_response, clarification_response
from reminder_agent.parser import parse_request
from reminder_agent.validation import InputValidationError, validate_request_text


def process_request(text: str, context: ResolutionContext | None = None) -> dict[str, Any]:
    resolution_context = context or ResolutionContext()
    try:
        validate_request_text(text)
    except InputValidationError as error:
        return clarification_response(_request_question(error.code))

    parsed = parse_request(ReminderRequest(text=text, context=resolution_context))
    if parsed.intent == "clarification":
        return clarification_response(
            parsed.clarification_question,
            task=parsed.task,
            datetime_value=(
                parsed.resolved_datetime.isoformat() if parsed.resolved_datetime else ""
            ),
        )
    if parsed.resolved_datetime is None:
        return clarification_response("What date and time should I use?", task=parsed.task)
    return action_response(
        intent=parsed.intent,
        task=parsed.task,
        datetime_value=parsed.resolved_datetime.isoformat(timespec="seconds"),
    )


def context_from_mapping(data: object) -> ResolutionContext:
    if isinstance(data, ResolutionContext):
        return data
    if data is None:
        return ResolutionContext()
    if not isinstance(data, dict):
        raise ValueError("context must be an object")

    reference_value = data.get("reference_time")
    reference_time: datetime | None
    if reference_value is None:
        reference_time = None
    elif isinstance(reference_value, datetime):
        reference_time = reference_value
    elif isinstance(reference_value, str):
        try:
            reference_time = datetime.fromisoformat(reference_value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("reference_time must be an ISO 8601 date-time") from error
    else:
        raise ValueError("reference_time must be a date-time string")

    timezone_name = data.get("timezone")
    if timezone_name is not None and not isinstance(timezone_name, str):
        raise ValueError("timezone must be a string")
    tasks_value = data.get("reminder_tasks", ())
    if not isinstance(tasks_value, (list, tuple)) or any(
        not isinstance(task, str) for task in tasks_value
    ):
        raise ValueError("reminder_tasks must be an array of strings")

    return ResolutionContext(
        reference_time=reference_time,
        timezone=timezone_name,
        reminder_tasks=tuple(tasks_value),
    )


def _request_question(code: str) -> str:
    if code == "REQUEST_TOO_LONG":
        return "Please shorten the request to 4,096 characters or fewer."
    if code == "REQUEST_NOT_TEXT":
        return "Please provide the reminder request as text."
    return "Please provide a reminder request."


__all__ = ["context_from_mapping", "process_request"]
