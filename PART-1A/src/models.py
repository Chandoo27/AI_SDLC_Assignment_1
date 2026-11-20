from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


class Priority(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(StrEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def _unique_tags(value: Any) -> Any:
    if not isinstance(value, list):
        return value

    tags: list[Any] = []
    seen: set[str] = set()
    for tag in value:
        key = tag.strip().casefold() if isinstance(tag, str) else None
        if key is None or key not in seen:
            tags.append(tag)
            if key is not None:
                seen.add(key)
    return tags


class TaskCreate(StrictModel):
    title: Title
    description: Description = ""
    priority: Priority = Priority.MEDIUM
    tags: list[Tag] = Field(default_factory=list, max_length=20)

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        return _unique_tags(value)


class TaskUpdate(StrictModel):
    title: Title | None = None
    description: Description | None = None
    priority: Priority | None = None
    tags: list[Tag] | None = Field(default=None, max_length=20)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, value: Any) -> Any:
        if isinstance(value, dict):
            for name, field_value in value.items():
                if field_value is None:
                    raise ValueError(f"{name} cannot be null")
        return value

    @model_validator(mode="after")
    def require_update_field(self) -> TaskUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one editable field must be provided")
        return self

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        return _unique_tags(value)


class Task(StrictModel):
    id: UUID
    title: Title
    description: Description = ""
    priority: Priority = Priority.MEDIUM
    tags: list[Tag] = Field(default_factory=list, max_length=20)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(alias="createdAt")

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        return _unique_tags(value)

    @field_validator("created_at")
    @classmethod
    def require_utc_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("createdAt must be a UTC timestamp")
        return value.astimezone(UTC)


class TagFilter(StrictModel):
    tags: list[Tag]

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        return _unique_tags(value)


class ErrorDetail(StrictModel):
    field: str
    message: str


class ErrorResponse(StrictModel):
    code: str
    message: str
    details: list[ErrorDetail]
