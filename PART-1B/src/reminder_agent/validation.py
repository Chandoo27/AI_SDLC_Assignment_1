"""Input, response-property, and JSON Schema validation."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from reminder_agent.models import ResolutionContext

MAX_REQUEST_LENGTH = 4096
RESPONSE_FIELDS = frozenset(
    {
        "intent",
        "task",
        "datetime",
        "needs_clarification",
        "clarification_question",
    }
)
_SCHEMA_PATH = (
    Path(__file__).parents[2]
    / "specs"
    / "001-reminder-agent"
    / "contracts"
    / "reminder-response.schema.json"
)


class InputValidationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ResponseSchemaError(ValueError):
    def __init__(self) -> None:
        super().__init__("RESPONSE_SCHEMA_INVALID")


@lru_cache(maxsize=1)
def get_schema_validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_request_text(text: object) -> None:
    if not isinstance(text, str):
        raise InputValidationError("REQUEST_NOT_TEXT")
    if not text.strip():
        raise InputValidationError("REQUEST_EMPTY")
    if len(text) > MAX_REQUEST_LENGTH:
        raise InputValidationError("REQUEST_TOO_LONG")


def validate_context(context: ResolutionContext, *, requires_reference: bool) -> None:
    if context.timezone is not None:
        try:
            ZoneInfo(context.timezone)
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise InputValidationError("TIMEZONE_INVALID") from error

    if requires_reference and context.timezone is None:
        raise InputValidationError("TIMEZONE_MISSING")

    reference_time = context.reference_time
    if reference_time is not None:
        if not isinstance(reference_time, datetime):
            raise InputValidationError("REFERENCE_TIME_INVALID")
        try:
            aware = reference_time.tzinfo is not None and reference_time.utcoffset() is not None
        except (OverflowError, ValueError):
            aware = False
        if not aware:
            raise InputValidationError("REFERENCE_TIME_NAIVE")
    elif requires_reference:
        raise InputValidationError("REFERENCE_TIME_MISSING")

    if any(not isinstance(task, str) or not task.strip() for task in context.reminder_tasks):
        raise InputValidationError("REMINDER_TASK_INVALID")


def match_reminder_target(query: str, candidates: tuple[str, ...]) -> str | None:
    normalized_query = _normalize_words(query)
    query_tokens = set(normalized_query.split())
    if not query_tokens:
        return None

    scores: list[tuple[float, str]] = []
    for candidate in candidates:
        normalized_candidate = _normalize_words(candidate)
        candidate_tokens = set(normalized_candidate.split())
        if not candidate_tokens:
            continue
        overlap = len(query_tokens.intersection(candidate_tokens))
        score = overlap / len(candidate_tokens)
        if score >= 0.5:
            scores.append((score, candidate))

    if not scores:
        return None
    best_score = max(score for score, _ in scores)
    best_matches = [candidate for score, candidate in scores if score == best_score]
    return best_matches[0] if len(best_matches) == 1 else None


def validate_response(response: object) -> bool:
    if not isinstance(response, dict):
        raise ResponseSchemaError()
    try:
        get_schema_validator().validate(response)
    except ValidationError as error:
        raise ResponseSchemaError() from error
    return True


def response_properties_valid(response: object) -> bool:
    if not isinstance(response, dict) or set(response) != RESPONSE_FIELDS:
        return False
    if not isinstance(response["intent"], str) or not isinstance(response["task"], str):
        return False
    if not isinstance(response["datetime"], str):
        return False
    if not isinstance(response["needs_clarification"], bool):
        return False
    if not isinstance(response["clarification_question"], str):
        return False

    if response["needs_clarification"]:
        return response["intent"] == "clarification" and bool(
            response["clarification_question"].strip()
        )

    if (
        response["intent"] not in {"create", "reschedule", "snooze"}
        or not response["task"].strip()
        or response["clarification_question"] != ""
    ):
        return False
    try:
        parsed_datetime = datetime.fromisoformat(response["datetime"].replace("Z", "+00:00"))
    except ValueError:
        return False
    try:
        return parsed_datetime.tzinfo is not None and parsed_datetime.utcoffset() is not None
    except (OverflowError, ValueError):
        return False


def _normalize_words(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))
