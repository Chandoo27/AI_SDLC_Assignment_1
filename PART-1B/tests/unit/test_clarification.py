from reminder_agent.engine import process_request


def test_empty_and_unsupported_requests_are_safe_clarifications() -> None:
    for request in ("", "   ", "What is the weather today?"):
        response = process_request(request)
        assert response["intent"] == "clarification"
        assert response["needs_clarification"] is True
        assert response["clarification_question"]
        assert response["task"] == ""
        assert response["datetime"] == ""


def test_overlong_request_is_not_processed_or_echoed() -> None:
    request = "x" * 4097
    response = process_request(request)

    assert response["intent"] == "clarification"
    assert response["needs_clarification"] is True
    assert request not in response["clarification_question"]
