"""Deterministic parsing for the supported English reminder-request forms."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from datetime import time as datetime_time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateparser import parse as parse_datetime

from reminder_agent.models import (
    ParsedReminderRequest,
    ReminderRequest,
    ResolutionContext,
)
from reminder_agent.validation import (
    InputValidationError,
    match_reminder_target,
    validate_context,
)

_WEEKDAY = (
    r"(?:mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|"
    r"fri(?:day)?|sat(?:urday)?|sun(?:day)?)"
)
_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_DURATION = r"\d+\s+(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?)"
_CLOCK = (
    r"(?:\b\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)|"
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d|noon|midnight)"
)
_DATE = (
    rf"(?:day after tomorrow|tomorrow|today|tonight|"
    rf"(?:next|this|coming)\s+(?:{_WEEKDAY}|week|month|year)|"
    rf"(?:in|after|for)\s+{_DURATION}|"
    rf"\d{{4}}-\d{{2}}-\d{{2}}|"
    rf"{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?|"
    rf"\d{{1,2}}(?:st|nd|rd|th)?\s+of\s+{_MONTH}(?:\s+\d{{4}})?|"
    rf"\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?)"
)
_TEMPORAL_PATTERN = re.compile(
    rf"(?P<expression>(?:{_DATE})(?:\s+(?:at|around|by)\s+{_CLOCK})?|{_CLOCK})",
    re.IGNORECASE,
)
_NUMERIC_DATE = re.compile(r"(?<!\d)\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?(?!\d)")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_INVALID_TWELVE_HOUR_CLOCK = re.compile(
    r"\b\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b", re.IGNORECASE
)
_IANA_ZONE = re.compile(r"\b(?:[A-Za-z_+-]+/)+[A-Za-z_+-]+\b")
_AMBIGUOUS_ZONE = re.compile(r"\b(?:PST|PDT|EST|EDT|CST|CDT|MST|MDT|IST)\b", re.I)
_INTENT_PREFIX = re.compile(r"^\s*(?:(?:hey|please|can you|could you)\s+)?", re.IGNORECASE)
_CREATE_PREFIX = re.compile(
    r"^\s*(?:(?:hey|please|can\s+you|could\s+you)\s+)?"
    r"(?:remind\s+me|set\s+(?:a\s+)?reminder|create\s+(?:a\s+)?reminder|"
    r"add\s+(?:a\s+)?reminder)\b",
    re.IGNORECASE,
)
_GENERIC_TARGET = re.compile(r"\b(?:my|the)\s+reminder\b|\bit\b", re.IGNORECASE)


def classify_intent(text: str) -> str:
    normalized = _INTENT_PREFIX.sub("", text)
    if re.search(r"\bsnooze\b", normalized, re.IGNORECASE):
        return "snooze"
    if re.match(r"(?:reschedul\w*|postpone|move|change)\b", normalized, re.IGNORECASE):
        return "reschedule"
    if _CREATE_PREFIX.match(text):
        return "create"
    if re.search(r"\bremind\s+me\s+to\b", normalized, re.IGNORECASE):
        return "create"
    return "clarification"


def parse_request(request: ReminderRequest) -> ParsedReminderRequest:
    text = request.text.strip()
    intent = classify_intent(text)
    if intent == "clarification":
        return _clarification("What reminder would you like help with?")

    task = _extract_create_task(text) if intent == "create" else ""
    if intent in {"reschedule", "snooze"}:
        task = _extract_target(text, request.context.reminder_tasks)
        if not task:
            return _clarification("Which existing reminder should I update?")

    time_zone_name, time_zone_error = _resolve_timezone_name(text, request.context)
    if time_zone_error:
        return _clarification(time_zone_error, task=task)
    if time_zone_name is None:
        return _clarification("What time zone should I use?", task=task)

    try:
        effective_context = ResolutionContext(
            reference_time=request.context.reference_time,
            timezone=time_zone_name,
            reminder_tasks=request.context.reminder_tasks,
        )
        validate_context(effective_context, requires_reference=True)
    except InputValidationError as error:
        return _clarification(_context_question(error.code), task=task)

    time_zone = ZoneInfo(time_zone_name)
    expression, match_count = _extract_temporal_expression(text)
    if match_count > 1:
        return _clarification("Which date and time should I use?", task=task)
    if expression is None:
        return _clarification("What date and time should I use?", task=task)
    if _NUMERIC_DATE.search(expression) and not _ISO_DATE.search(expression):
        return _clarification("Which date format did you mean?", task=task)
    if _INVALID_TWELVE_HOUR_CLOCK.search(expression) and _requested_clock(expression) is None:
        return _clarification("What valid clock time should I use?", task=task)
    if not _has_explicit_clock(expression) and not _is_duration_expression(expression):
        return _clarification("What time should I use?", task=task)

    if intent == "create" and not task:
        return _clarification("What should I remind you about?")

    if intent == "reschedule" and _is_snooze_duration(expression):
        return _clarification("What replacement date and time should I use?", task=task)

    parse_expression = _normalize_temporal_expression(expression, intent)
    reference_time = request.context.reference_time
    if reference_time is None:
        return _clarification("What reference date and time should I use?")

    try:
        relative_base = reference_time.astimezone(time_zone)
        parsed_datetime = parse_datetime(
            parse_expression,
            settings={
                "RELATIVE_BASE": relative_base,
                "TIMEZONE": time_zone_name,
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
    except (OverflowError, TypeError, ValueError):
        parsed_datetime = None

    if parsed_datetime is None:
        return _clarification(
            "I couldn't resolve that date and time. What should I use?", task=task
        )

    local_datetime = parsed_datetime.astimezone(time_zone)
    requested_time = _requested_clock(expression)
    wall_time = (
        datetime.combine(local_datetime.date(), requested_time)
        if requested_time is not None
        else local_datetime.replace(tzinfo=None)
    )
    if _is_nonexistent_local_time(wall_time, time_zone):
        return _clarification(
            "That local time does not exist due to a clock change. What time should I use?",
            task=task,
        )
    if _is_ambiguous_local_time(wall_time, time_zone):
        return _clarification(
            "That local time occurs twice due to a clock change. Which occurrence do you mean?",
            task=task,
        )

    if local_datetime <= reference_time.astimezone(time_zone):
        return _clarification(
            "That date and time is not in the future. What future time should I use?", task=task
        )

    return ParsedReminderRequest(
        intent=intent,  # type: ignore[arg-type]
        task=task,
        temporal_expression=expression,
        resolved_datetime=local_datetime,
    )


def _extract_temporal_expression(text: str) -> tuple[str | None, int]:
    matches = list(_TEMPORAL_PATTERN.finditer(text))
    if not matches:
        return None, 0
    if len(matches) > 1:
        return None, len(matches)
    return matches[0].group("expression").strip(), 1


def _extract_create_task(text: str) -> str:
    without_time = _TEMPORAL_PATTERN.sub(" ", text)
    without_time = _IANA_ZONE.sub(" ", without_time)
    without_time = _AMBIGUOUS_ZONE.sub(" ", without_time)
    without_time = re.sub(r"\b(?:UTC|GMT)\b", " ", without_time, flags=re.IGNORECASE)
    without_prefix = _CREATE_PREFIX.sub("", without_time)
    task = re.sub(
        r"^\s*(?:(?:to|that|for|at|on)\s+)+",
        "",
        without_prefix,
        flags=re.IGNORECASE,
    )
    task = re.sub(r"\s+", " ", task).strip(" \t\r\n.,;:!?")
    task = re.sub(r"\s+(?:on|at|to|for)$", "", task, flags=re.IGNORECASE)
    return task


def _extract_target(text: str, candidates: tuple[str, ...]) -> str:
    if not candidates:
        return ""
    matched = match_reminder_target(text, candidates)
    if matched:
        return matched
    if len(candidates) == 1 and _GENERIC_TARGET.search(text):
        return candidates[0]
    return ""


def _resolve_timezone_name(text: str, context: ResolutionContext) -> tuple[str | None, str | None]:
    if _AMBIGUOUS_ZONE.search(text):
        return None, "That time-zone abbreviation is ambiguous. Which time zone should I use?"
    explicit = _IANA_ZONE.search(text)
    name: str | None
    if explicit:
        name = explicit.group(0)
    elif re.search(r"\b(?:UTC|GMT)\b", text, re.IGNORECASE):
        name = "UTC"
    else:
        name = context.timezone

    if name is None:
        return None, None
    try:
        ZoneInfo(name)
    except (ValueError, ZoneInfoNotFoundError):
        return None, "I couldn't identify that time zone. Which IANA time zone should I use?"
    return name, None


def _normalize_temporal_expression(expression: str, intent: str) -> str:
    normalized = re.sub(r"^\s*(?:to|on|at|until|by)\s+", "", expression, flags=re.IGNORECASE)
    if intent == "snooze":
        normalized = re.sub(r"^\s*for\s+", "in ", normalized, flags=re.IGNORECASE)
    return normalized


def _has_explicit_clock(expression: str) -> bool:
    return bool(re.search(_CLOCK, expression, re.IGNORECASE))


def _requested_clock(expression: str) -> datetime_time | None:
    lowered = expression.casefold()
    if "noon" in lowered:
        return datetime_time(12, 0)
    if "midnight" in lowered:
        return datetime_time(0, 0)

    twelve_hour = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b",
        expression,
        re.IGNORECASE,
    )
    if twelve_hour:
        hour = int(twelve_hour.group(1))
        minute = int(twelve_hour.group(2) or 0)
        suffix = twelve_hour.group(3).casefold().replace(".", "")
        if not 1 <= hour <= 12 or minute > 59:
            return None
        if suffix == "pm" and hour != 12:
            hour += 12
        elif suffix == "am" and hour == 12:
            hour = 0
        return datetime_time(hour, minute)

    twenty_four_hour = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", expression)
    if twenty_four_hour:
        return datetime_time(int(twenty_four_hour.group(1)), int(twenty_four_hour.group(2)))
    return None


def _is_duration_expression(expression: str) -> bool:
    return bool(re.search(r"\b(?:in|after|for)\s+" + _DURATION, expression, re.IGNORECASE))


def _is_snooze_duration(expression: str) -> bool:
    return bool(re.match(r"\s*for\s+" + _DURATION, expression, re.IGNORECASE))


def _is_ambiguous_local_time(value: datetime, time_zone: ZoneInfo) -> bool:
    first = value.replace(tzinfo=time_zone, fold=0)
    second = value.replace(tzinfo=time_zone, fold=1)
    return first.utcoffset() != second.utcoffset()


def _is_nonexistent_local_time(value: datetime, time_zone: ZoneInfo) -> bool:
    attached = value.replace(tzinfo=time_zone, fold=0)
    round_trip = attached.astimezone(UTC).astimezone(time_zone)
    return round_trip.replace(tzinfo=None) != value


def _context_question(code: str) -> str:
    if code.startswith("TIMEZONE"):
        return "What valid IANA time zone should I use?"
    if code.startswith("REFERENCE_TIME"):
        return "What reference date and time should I use?"
    return "Please provide valid reminder context."


def _clarification(
    question: str, *, task: str = "", datetime_value: str = ""
) -> ParsedReminderRequest:
    return ParsedReminderRequest(
        intent="clarification",
        task=task,
        temporal_expression="",
        resolved_datetime=None,
        clarification_reason="MISSING_OR_AMBIGUOUS_INFORMATION",
        clarification_question=question,
    )


__all__ = ["classify_intent", "parse_request"]
