from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from threading import RLock
from typing import TypeVar
from uuid import UUID

from pydantic import ValidationError

from src.models import Task, TaskStatus

T = TypeVar("T")


class PersistenceError(Exception):
    pass


class TaskNotFound(Exception):
    pass


class JsonTaskStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return self._read()

    def get_task(self, task_id: UUID) -> Task:
        with self._lock:
            for task in self._read():
                if task.id == task_id:
                    return task
        raise TaskNotFound

    def create_task(self, task: Task) -> Task:
        def append(tasks: list[Task]) -> Task:
            if any(existing.id == task.id for existing in tasks):
                raise ValueError("Task ID already exists")
            tasks.append(task)
            return task

        return self._mutate(append)

    def update_task(self, task_id: UUID, changes: dict[str, object]) -> Task:
        def update(tasks: list[Task]) -> Task:
            for index, existing in enumerate(tasks):
                if existing.id == task_id:
                    updated_data = existing.model_dump()
                    updated_data.update(changes)
                    updated = Task.model_validate(updated_data)
                    tasks[index] = updated
                    return updated
            raise TaskNotFound

        return self._mutate(update)

    def set_status(self, task_id: UUID, status: TaskStatus) -> Task:
        return self.update_task(task_id, {"status": status})

    def delete_task(self, task_id: UUID) -> None:
        def delete(tasks: list[Task]) -> None:
            for index, task in enumerate(tasks):
                if task.id == task_id:
                    del tasks[index]
                    return
            raise TaskNotFound

        self._mutate(delete)

    def _mutate(self, operation: Callable[[list[Task]], T]) -> T:
        with self._lock:
            tasks = self._read()
            result = operation(tasks)
            self._write(tasks)
            return result

    def _read(self) -> list[Task]:
        try:
            with self.path.open("r", encoding="utf-8") as data_file:
                payload = json.load(data_file)
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PersistenceError("Could not read task data") from error

        if not isinstance(payload, list):
            raise PersistenceError("Task data must be a JSON array")
        try:
            return [Task.model_validate(item) for item in payload]
        except (ValidationError, TypeError) as error:
            raise PersistenceError("Task data is invalid") from error

    def _write(self, tasks: list[Task]) -> None:
        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f"{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    [task.model_dump(mode="json", by_alias=True) for task in tasks],
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
        except (OSError, TypeError, ValueError) as error:
            raise PersistenceError("Could not save task data") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
