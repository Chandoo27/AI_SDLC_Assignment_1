import string

from hypothesis import given
from hypothesis import strategies as st

from reminder_agent.engine import process_request
from reminder_agent.output import build_response, validate_response
from reminder_agent.validation import response_properties_valid


@given(st.text(alphabet=st.sampled_from([" ", "\t", "\n", "\r"]), min_size=1, max_size=100))
def test_whitespace_only_input_never_produces_action(request: str) -> None:
    response = process_request(request)

    assert response["intent"] == "clarification"
    assert response["needs_clarification"] is True
    assert validate_response(response)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=200))
def test_clarification_response_preserves_contract(question: str) -> None:
    response = build_response(
        intent="clarification",
        task="",
        datetime_value="",
        needs_clarification=True,
        clarification_question=question,
    )

    assert response["intent"] == "clarification"
    assert response["needs_clarification"] is True
    assert validate_response(response)


@given(
    intent=st.sampled_from(["create", "reschedule", "snooze"]),
    task=st.text(alphabet=string.ascii_letters, min_size=1, max_size=40),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
)
def test_action_response_preserves_contract(
    intent: str, task: str, month: int, day: int, hour: int, minute: int
) -> None:
    response = build_response(
        intent=intent,  # type: ignore[arg-type]
        task=task,
        datetime_value=f"2026-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00+05:30",
    )

    assert response["needs_clarification"] is False
    assert response["clarification_question"] == ""
    assert validate_response(response)
    assert response_properties_valid(response)
