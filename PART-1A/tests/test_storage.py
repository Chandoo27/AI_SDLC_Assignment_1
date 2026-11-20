from concurrent.futures import ThreadPoolExecutor

import pytest
from src.models import TaskCreate, TaskUpdate
from src.services import TaskService
from src.storage import JsonTaskStore, PersistenceError


def test_missing_data_file_starts_with_empty_collection(tmp_path):
    store = JsonTaskStore(tmp_path / "missing.json")

    assert store.list_tasks() == []


def test_tasks_survive_store_recreation(tmp_path):
    data_file = tmp_path / "tasks.json"
    service = TaskService(JsonTaskStore(data_file))
    created = service.create_task(TaskCreate(title="Keep me", tags=["work"]))

    reloaded = JsonTaskStore(data_file).get_task(created.id)

    assert reloaded == created


def test_malformed_data_is_reported_and_left_unchanged(tmp_path):
    data_file = tmp_path / "tasks.json"
    original = "{not valid json"
    data_file.write_text(original, encoding="utf-8")

    with pytest.raises(PersistenceError):
        JsonTaskStore(data_file).list_tasks()

    assert data_file.read_text(encoding="utf-8") == original


def test_concurrent_different_field_updates_are_serialized(tmp_path):
    service = TaskService(JsonTaskStore(tmp_path / "tasks.json"))
    task = service.create_task(TaskCreate(title="Initial", description="Initial"))

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(
            executor.map(
                lambda update: service.update_task(task.id, update),
                [
                    TaskUpdate(title="Updated title"),
                    TaskUpdate(description="Updated description"),
                ],
            )
        )

    final = service.get_task(task.id)
    assert final.title == "Updated title"
    assert final.description == "Updated description"
