from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.models import ErrorResponse
from src.routes import router
from src.services import TaskService
from src.storage import JsonTaskStore, PersistenceError, TaskNotFound

logger = logging.getLogger(__name__)


def _validation_details(error: RequestValidationError) -> list[dict[str, str]]:
    details = []
    for item in error.errors():
        location = item.get("loc", ())
        field = ".".join(str(part) for part in location if part not in {"body", "query", "path"})
        error_type = item.get("type", "")
        message = {
            "string_too_long": "Value is longer than permitted.",
            "string_too_short": "Value is shorter than permitted.",
            "missing": "Field is required.",
            "extra_forbidden": "Field is not allowed.",
            "enum": "Value is not one of the supported options.",
        }.get(error_type, "Invalid value.")
        details.append({"field": field or "request", "message": message})
    return details


def create_app(data_file: Path | None = None) -> FastAPI:
    default_path = Path(__file__).resolve().parent.parent / "data" / "tasks.json"
    configured_path = data_file or Path(os.environ.get("SMART_TODO_DATA_FILE", default_path))

    app = FastAPI(title="Smart Todo API", version="1.0.0")
    app.state.task_service = TaskService(JsonTaskStore(configured_path))
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        del request
        response = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=_validation_details(error),
        )
        return JSONResponse(status_code=422, content=response.model_dump(mode="json"))

    @app.exception_handler(TaskNotFound)
    async def not_found_handler(request: Request, error: TaskNotFound) -> JSONResponse:
        del request, error
        response = ErrorResponse(code="TASK_NOT_FOUND", message="Task not found", details=[])
        return JSONResponse(status_code=404, content=response.model_dump(mode="json"))

    @app.exception_handler(PersistenceError)
    async def persistence_error_handler(request: Request, error: PersistenceError) -> JSONResponse:
        del request
        logger.error("Task persistence failed: %s", error)
        response = ErrorResponse(
            code="DATA_FILE_ERROR",
            message="Task data is unavailable",
            details=[],
        )
        return JSONResponse(status_code=500, content=response.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException) -> JSONResponse:
        del request
        if error.status_code == 422:
            code, message = "VALIDATION_ERROR", "Request validation failed"
        elif error.status_code == 404:
            code, message = "NOT_FOUND", "Resource not found"
        else:
            code, message = "HTTP_ERROR", "Request could not be completed"
        response = ErrorResponse(code=code, message=message, details=[])
        return JSONResponse(status_code=error.status_code, content=response.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
        del request
        logger.exception("Unhandled API error", exc_info=error)
        response = ErrorResponse(
            code="INTERNAL_ERROR",
            message="An internal error occurred",
            details=[],
        )
        return JSONResponse(status_code=500, content=response.model_dump(mode="json"))

    return app


app = create_app()
