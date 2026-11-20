from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from src.main import create_app


def create_task(client, **values):
    return client.post("/tasks", json={"title": "Example task", **values})


def test_create_task_returns_defaults_and_utc_timestamp(client):
    response = create_task(client, title="  Example task  ")

    assert response.status_code == 201
    task = response.json()
    assert UUID(task["id"])
    assert task["title"] == "Example task"
    assert task["description"] == ""
    assert task["priority"] == "Medium"
    assert task["tags"] == []
    assert task["status"] == "Pending"
    created_at = datetime.fromisoformat(task["createdAt"].replace("Z", "+00:00"))
    assert created_at.utcoffset() == timedelta(0)


def test_create_task_accepts_documented_field_boundaries(client):
    response = create_task(
        client,
        title="x",
        description="d" * 5000,
        tags=[f"tag-{index}" for index in range(20)],
    )

    assert response.status_code == 201
    assert len(response.json()["description"]) == 5000
    assert len(response.json()["tags"]) == 20


def test_description_is_trimmed(client):
    response = create_task(client, description="  Keep this text  ")

    assert response.status_code == 201
    assert response.json()["description"] == "Keep this text"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "valid", "description": "x" * 5001},
        {"title": "valid", "priority": "Urgent"},
        {"title": "valid", "tags": [""]},
        {"title": "valid", "tags": ["x" * 33]},
        {"title": "valid", "tags": [f"tag-{index}" for index in range(21)]},
    ],
)
def test_invalid_create_returns_422_without_persisting(client, payload):
    before = client.get("/tasks").json()

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert client.get("/tasks").json() == before


def test_task_crud_and_partial_update(client):
    created = create_task(
        client,
        description="Initial description",
        priority="High",
        tags=["work", "work"],
    )
    assert created.status_code == 201
    task = created.json()
    task_id = task["id"]
    assert task["tags"] == ["work"]

    assert client.get(f"/tasks/{task_id}").json() == task
    assert [item["id"] for item in client.get("/tasks").json()] == [task_id]

    updated = client.patch(f"/tasks/{task_id}", json={"title": "Updated"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated"
    assert updated.json()["description"] == "Initial description"
    assert updated.json()["priority"] == "High"
    assert updated.json()["tags"] == ["work"]
    assert updated.json()["id"] == task["id"]
    assert updated.json()["createdAt"] == task["createdAt"]

    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    missing = client.get(f"/tasks/{task_id}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "TASK_NOT_FOUND"


def test_duplicate_tags_are_stored_once_case_insensitively(client):
    response = create_task(client, tags=["Work", "work", "Home"])

    assert response.status_code == 201
    assert response.json()["tags"] == ["Work", "Home"]


@pytest.mark.parametrize(
    "payload",
    [
        {"id": str(uuid4())},
        {"createdAt": "2026-01-01T00:00:00Z"},
        {"title": None},
        {},
    ],
)
def test_invalid_update_is_rejected(client, payload):
    task_id = create_task(client).json()["id"]
    before = client.get(f"/tasks/{task_id}").json()

    response = client.patch(f"/tasks/{task_id}", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert client.get(f"/tasks/{task_id}").json() == before


def test_unknown_task_operations_use_not_found(client):
    task_id = str(uuid4())

    responses = [
        client.get(f"/tasks/{task_id}"),
        client.patch(f"/tasks/{task_id}", json={"title": "Changed"}),
        client.delete(f"/tasks/{task_id}"),
        client.post(f"/tasks/{task_id}/complete"),
        client.post(f"/tasks/{task_id}/reopen"),
    ]

    assert [response.status_code for response in responses] == [404] * len(responses)
    assert all(response.json()["code"] == "TASK_NOT_FOUND" for response in responses)


def test_invalid_task_id_returns_422(client):
    response = client.get("/tasks/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_complete_and_reopen_are_idempotent(client):
    task_id = create_task(client).json()["id"]

    completed = client.post(f"/tasks/{task_id}/complete")
    completed_again = client.post(f"/tasks/{task_id}/complete")
    reopened = client.post(f"/tasks/{task_id}/reopen")
    reopened_again = client.post(f"/tasks/{task_id}/reopen")

    assert [
        item.status_code for item in (completed, completed_again, reopened, reopened_again)
    ] == [
        200,
        200,
        200,
        200,
    ]
    assert completed.json()["status"] == completed_again.json()["status"] == "Completed"
    assert reopened.json()["status"] == reopened_again.json()["status"] == "Pending"


def test_later_sequential_update_wins_for_same_field(client):
    task_id = create_task(client).json()["id"]

    first = client.patch(f"/tasks/{task_id}", json={"title": "First"})
    second = client.patch(f"/tasks/{task_id}", json={"title": "Second"})

    assert first.status_code == second.status_code == 200
    assert client.get(f"/tasks/{task_id}").json()["title"] == "Second"


def test_concurrent_updates_preserve_different_fields(client):
    task_id = create_task(client, description="Original").json()["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda payload: client.patch(f"/tasks/{task_id}", json=payload),
                [{"title": "Updated title"}, {"description": "Updated description"}],
            )
        )

    assert all(response.status_code == 200 for response in results)
    final = client.get(f"/tasks/{task_id}").json()
    assert final["title"] == "Updated title"
    assert final["description"] == "Updated description"


def test_malformed_data_file_returns_sanitized_500_and_is_preserved(tmp_path):
    data_file = tmp_path / "tasks.json"
    original = "{broken"
    data_file.write_text(original, encoding="utf-8")

    with TestClient(create_app(data_file)) as test_client:
        response = test_client.get("/tasks")

    assert response.status_code == 500
    assert response.json()["code"] == "DATA_FILE_ERROR"
    assert str(data_file) not in response.text
    assert response.json()["details"] == []
    assert data_file.read_text(encoding="utf-8") == original


def test_task_status_and_fields_survive_application_restart(tmp_path):
    data_file = tmp_path / "tasks.json"
    with TestClient(create_app(data_file)) as first_client:
        created = first_client.post(
            "/tasks",
            json={
                "title": "Persisted task",
                "description": "Keep all fields",
                "priority": "High",
                "tags": ["work"],
            },
        ).json()
        completed = first_client.post(f"/tasks/{created['id']}/complete").json()

    with TestClient(create_app(data_file)) as second_client:
        restored = second_client.get(f"/tasks/{created['id']}")

    assert restored.status_code == 200
    assert restored.json() == completed


def test_generated_openapi_documents_success_and_error_schemas(client):
    schema = client.get("/openapi.json").json()

    assert (
        schema["paths"]["/tasks"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["items"]["$ref"]
        == "#/components/schemas/Task"
    )
    assert "500" in schema["paths"]["/tasks"]["get"]["responses"]
    assert schema["components"]["schemas"]["ErrorResponse"]["required"] == [
        "code",
        "message",
        "details",
    ]
