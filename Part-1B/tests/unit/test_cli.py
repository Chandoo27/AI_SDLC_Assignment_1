import json

from reminder_agent.main import main


def test_cli_emits_one_json_response(capsys) -> None:
    exit_code = main(
        [
            "Remind me tomorrow at 6 PM to pay electricity bill.",
            "--reference-time",
            "2026-11-19T09:00:00+05:30",
            "--timezone",
            "Asia/Kolkata",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    response = json.loads(output)
    assert response["intent"] == "create"
    assert response["task"] == "pay electricity bill"
    assert response["datetime"] == "2026-11-20T18:00:00+05:30"
