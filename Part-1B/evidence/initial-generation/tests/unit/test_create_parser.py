from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from reminder_agent.engine import process_request
from reminder_agent.models import ResolutionContext


@pytest.fixture
def fixed_context() -> ResolutionContext:
    return ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        timezone="Asia/Kolkata",
    )


@pytest.mark.parametrize(
    ("case_text", "expected_task", "expected_datetime"),
    [
        (
            "Remind me tomorrow at 6 PM to pay electricity bill.",
            "pay electricity bill",
            "2026-11-20T18:00:00+05:30",
        ),
        (
            "Remind me next Monday at 10 AM to attend project review.",
            "attend project review",
            "2026-11-23T10:00:00+05:30",
        ),
        (
            "Remind me in 30 minutes to submit the assignment.",
            "submit the assignment",
            "2026-11-19T09:30:00+05:30",
        ),
        (
            "Please remind me to submit the report tomorrow at 6 PM.",
            "submit the report",
            "2026-11-20T18:00:00+05:30",
        ),
    ],
)
def test_create_requests_extract_task_and_resolve_time(
    case_text: str,
    expected_task: str,
    expected_datetime: str,
    fixed_context: ResolutionContext,
) -> None:
    response = process_request(case_text, fixed_context)

    assert response["intent"] == "create"
    assert response["task"] == expected_task
    assert response["datetime"] == expected_datetime
    assert response["needs_clarification"] is False
    assert response["clarification_question"] == ""


@pytest.mark.parametrize(
    "case_text",
    [
        "Remind me tomorrow to pay electricity bill.",
        "Remind me at 6 PM.",
        "Remind me on 03/04 at 6 PM to pay the bill.",
    ],
)
def test_create_missing_or_ambiguous_values_request_clarification(
    case_text: str, fixed_context: ResolutionContext
) -> None:
    response = process_request(case_text, fixed_context)

    assert response["intent"] == "clarification"
    assert response["needs_clarification"] is True
    assert response["clarification_question"]


def test_explicit_iana_timezone_overrides_context_and_is_not_task_text() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("America/New_York")),
        timezone="Asia/Kolkata",
    )

    response = process_request(
        "Remind me tomorrow at 6 PM America/New_York to call parents.",
        context,
    )

    assert response["intent"] == "create"
    assert response["task"] == "call parents"
    assert response["datetime"] == "2026-11-20T18:00:00-05:00"


@pytest.mark.parametrize(
    "case_text",
    [
        "Remind me tomorrow at 6 PM PST to call parents.",
        "Remind me tomorrow at 6 PM Mars/Nowhere to call parents.",
    ],
)
def test_ambiguous_or_invalid_explicit_time_zone_clarifies(
    case_text: str, fixed_context: ResolutionContext
) -> None:
    response = process_request(case_text, fixed_context)

    assert response["needs_clarification"] is True
    assert response["intent"] == "clarification"


def test_dst_gap_is_not_silently_normalized() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 3, 7, 9, 0, tzinfo=ZoneInfo("America/New_York")),
        timezone="America/New_York",
    )

    response = process_request(
        "Remind me March 8, 2026 at 2:30 AM to test DST.",
        context,
    )

    assert response["needs_clarification"] is True
    assert response["intent"] == "clarification"
    assert "does not exist" in response["clarification_question"]


def test_dst_overlap_requires_clarification() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 10, 31, 9, 0, tzinfo=ZoneInfo("America/New_York")),
        timezone="America/New_York",
    )

    response = process_request(
        "Remind me November 1, 2026 at 1:30 AM to test DST.",
        context,
    )

    assert response["needs_clarification"] is True
    assert "occurs twice" in response["clarification_question"]


def test_past_month_day_without_year_is_not_rolled_forward() -> None:
    response = process_request(
        "Remind me November 18 at 6 PM to review the plan.",
        ResolutionContext(
            reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
            timezone="Asia/Kolkata",
        ),
    )

    assert response["needs_clarification"] is True
    assert "not in the future" in response["clarification_question"]
