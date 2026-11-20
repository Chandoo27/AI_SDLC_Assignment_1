import json

from reminder_agent.output import build_response, serialize_response


def test_action_has_exact_five_fields_and_empty_question() -> None:
    response = build_response(
        intent="create",
        task="pay electricity bill",
        datetime_value="2026-11-20T18:00:00+05:30",
    )

    assert set(response) == {
        "intent",
        "task",
        "datetime",
        "needs_clarification",
        "clarification_question",
    }
    assert response["clarification_question"] == ""
    assert response["needs_clarification"] is False


def test_clarification_has_non_empty_question_and_can_round_trip() -> None:
    response = build_response(
        intent="clarification",
        task="",
        datetime_value="",
        needs_clarification=True,
        clarification_question="What time should I use?",
    )

    assert response["clarification_question"] == "What time should I use?"
    assert json.loads(serialize_response(response)) == response
