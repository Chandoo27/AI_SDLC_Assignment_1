from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.models import Priority, Task, TaskCreate, TaskStatus, TaskUpdate
from src.storage import JsonTaskStore


class TaskService:
    _PRIORITY_ORDER = {
        Priority.HIGH: 0,
        Priority.MEDIUM: 1,
        Priority.LOW: 2,
    }

    def __init__(self, store: JsonTaskStore) -> None:
        self.store = store

    def create_task(self, task_data: TaskCreate) -> Task:
        task = Task(
            id=uuid4(),
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            tags=task_data.tags,
            status=TaskStatus.PENDING,
            createdAt=datetime.now(UTC),
        )
        return self.store.create_task(task)

    def list_tasks(
        self,
        tags: list[str] | None = None,
        sort: str | None = None,
    ) -> list[Task]:
        tasks = self.store.list_tasks()
        if tags:
            requested_tags = {tag.casefold() for tag in tags}
            tasks = [
                task for task in tasks if any(tag.casefold() in requested_tags for tag in task.tags)
            ]
        if sort == "priority":
            tasks.sort(
                key=lambda task: (
                    self._PRIORITY_ORDER[task.priority],
                    task.created_at,
                    str(task.id),
                )
            )
        return tasks

    def get_task(self, task_id: UUID) -> Task:
        return self.store.get_task(task_id)

    def update_task(self, task_id: UUID, task_data: TaskUpdate) -> Task:
        return self.store.update_task(task_id, task_data.model_dump(exclude_unset=True))

    def delete_task(self, task_id: UUID) -> None:
        self.store.delete_task(task_id)

    def complete_task(self, task_id: UUID) -> Task:
        return self.store.set_status(task_id, TaskStatus.COMPLETED)

    def reopen_task(self, task_id: UUID) -> Task:
        return self.store.set_status(task_id, TaskStatus.PENDING)
