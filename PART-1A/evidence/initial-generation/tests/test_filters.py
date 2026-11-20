import json
import platform
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from src.main import create_app


def test_tag_filter_is_case_insensitive_exact_and_match_any(client):
    client.post("/tasks", json={"title": "One", "tags": ["Work"]})
    client.post("/tasks", json={"title": "Two", "tags": ["home"]})
    client.post("/tasks", json={"title": "Three", "tags": ["workflow"]})

    response = client.get("/tasks?tags=work,home")

    assert response.status_code == 200
    assert {task["title"] for task in response.json()} == {"One", "Two"}


def test_repeated_tag_query_parameters_are_supported(client):
    client.post("/tasks", json={"title": "Work", "tags": ["work"]})
    client.post("/tasks", json={"title": "Home", "tags": ["home"]})

    response = client.get("/tasks", params=[("tags", "work"), ("tags", "home")])

    assert {task["title"] for task in response.json()} == {"Work", "Home"}


def test_filter_without_matches_returns_empty_list(client):
    client.post("/tasks", json={"title": "One", "tags": ["work"]})

    response = client.get("/tasks?tags=missing")

    assert response.status_code == 200
    assert response.json() == []


def test_priority_sort_orders_high_medium_low(client):
    client.post("/tasks", json={"title": "Low", "priority": "Low"})
    client.post("/tasks", json={"title": "High", "priority": "High"})
    client.post("/tasks", json={"title": "Medium", "priority": "Medium"})

    response = client.get("/tasks?sort=priority")

    assert [task["priority"] for task in response.json()] == ["High", "Medium", "Low"]


def test_priority_ties_use_created_at_then_id(tmp_path):
    data_file = tmp_path / "tasks.json"
    data_file.write_text(
        json.dumps(
            [
                {
                    "id": "00000000-0000-0000-0000-000000000003",
                    "title": "Later",
                    "description": "",
                    "priority": "High",
                    "tags": [],
                    "status": "Pending",
                    "createdAt": "2026-01-02T00:00:00Z",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "title": "B",
                    "description": "",
                    "priority": "High",
                    "tags": [],
                    "status": "Pending",
                    "createdAt": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "title": "A",
                    "description": "",
                    "priority": "High",
                    "tags": [],
                    "status": "Pending",
                    "createdAt": "2026-01-01T00:00:00Z",
                },
            ]
        ),
        encoding="utf-8",
    )
    with TestClient(create_app(data_file)) as client:
        response = client.get("/tasks?sort=priority")

    assert [task["title"] for task in response.json()] == ["A", "B", "Later"]


def test_filter_and_sort_can_be_combined(client):
    client.post("/tasks", json={"title": "Low work", "priority": "Low", "tags": ["work"]})
    client.post("/tasks", json={"title": "High home", "priority": "High", "tags": ["home"]})
    client.post("/tasks", json={"title": "High work", "priority": "High", "tags": ["work"]})

    response = client.get("/tasks?tags=work&sort=priority")

    assert [task["title"] for task in response.json()] == ["High work", "Low work"]


def test_invalid_filter_values_return_422(client):
    for query in ("tags=", "tags=" + ("x" * 33), "sort=unknown"):
        response = client.get(f"/tasks?{query}")
        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.performance
def test_1000_task_list_filter_and_sort_latency(tmp_path, record_property):
    data_file = tmp_path / "tasks.json"
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    tasks = [
        {
            "id": str(UUID(int=index + 1)),
            "title": f"Task {index}",
            "description": "",
            "priority": ("High", "Medium", "Low")[index % 3],
            "tags": [f"tag-{index % 5}"],
            "status": "Pending",
            "createdAt": (created_at + timedelta(seconds=index)).isoformat(),
        }
        for index in range(1000)
    ]
    data_file.write_text(json.dumps(tasks), encoding="utf-8")
    latencies = []

    with TestClient(create_app(data_file)) as test_client:
        for index in range(100):
            query = ("", "?tags=tag-1", "?tags=tag-1&sort=priority")[index % 3]
            started = time.perf_counter()
            response = test_client.get(f"/tasks{query}")
            latencies.append(time.perf_counter() - started)
            assert response.status_code == 200

    under_limit = sum(latency < 1.0 for latency in latencies)
    record_property(
        "benchmark_machine",
        f"{platform.platform()} | {platform.processor()} | Python {platform.python_version()}",
    )
    record_property("requests_under_one_second", under_limit)
    assert under_limit >= 95, (
        f"{under_limit}/100 requests completed under one second on "
        f"{platform.platform()} with Python {platform.python_version()}"
    )
