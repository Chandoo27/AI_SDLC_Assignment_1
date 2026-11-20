from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.models import ErrorResponse, TagFilter, Task, TaskCreate, TaskUpdate
from src.services import TaskService

router = APIRouter()

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Task not found"},
    422: {"model": ErrorResponse, "description": "Invalid request"},
    500: {"model": ErrorResponse, "description": "Task data could not be accessed"},
}


def _service(request: Request) -> TaskService:
    return request.app.state.task_service


def _parse_tag_filters(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None

    split_values = [part for value in values for part in value.split(",")]
    try:
        return TagFilter(tags=split_values).tags
    except ValidationError as error:
        details = []
        for item in error.errors():
            details.append(
                {
                    **item,
                    "loc": ("query", "tags", *item.get("loc", ())),
                }
            )
        raise RequestValidationError(details) from error


@router.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={422: ERROR_RESPONSES[422], 500: ERROR_RESPONSES[500]},
)
def create_task(request: Request, task_data: TaskCreate) -> Task:
    return _service(request).create_task(task_data)


@router.get(
    "/tasks",
    response_model=list[Task],
    responses={422: ERROR_RESPONSES[422], 500: ERROR_RESPONSES[500]},
)
def list_tasks(
    request: Request,
    tags: Annotated[list[str] | None, Query()] = None,
    sort: Annotated[Literal["priority"] | None, Query()] = None,
) -> list[Task]:
    return _service(request).list_tasks(_parse_tag_filters(tags), sort)


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def get_task(request: Request, task_id: UUID) -> Task:
    return _service(request).get_task(task_id)


@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def update_task(request: Request, task_id: UUID, task_data: TaskUpdate) -> Task:
    return _service(request).update_task(task_id, task_data)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422], 500: ERROR_RESPONSES[500]},
)
def delete_task(request: Request, task_id: UUID) -> Response:
    _service(request).delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/complete",
    response_model=Task,
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def complete_task(request: Request, task_id: UUID) -> Task:
    return _service(request).complete_task(task_id)


@router.post(
    "/tasks/{task_id}/reopen",
    response_model=Task,
    responses={
        404: ERROR_RESPONSES[404],
        422: ERROR_RESPONSES[422],
        500: ERROR_RESPONSES[500],
    },
)
def reopen_task(request: Request, task_id: UUID) -> Task:
    return _service(request).reopen_task(task_id)
