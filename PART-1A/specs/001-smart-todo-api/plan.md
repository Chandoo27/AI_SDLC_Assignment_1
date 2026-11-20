# Implementation Plan: Smart Todo API

**Branch**: `001-smart-todo-api` | **Date**: 2026-11-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-smart-todo-api/spec.md`

## Summary

Implement a local FastAPI task service using Pydantic v2, a thread-safe JSON repository with
atomic replacement, resource-oriented routes, and automated tests and CI quality gates. The
source modules follow the requested flat `src/` layout.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Pydantic v2, Uvicorn; development dependencies include pytest,
pytest-cov, httpx2, Ruff, Bandit, pip-audit, and detect-secrets

**Storage**: Configured local JSON file; no database or remote persistence service

**Testing**: pytest with an 80% coverage minimum, FastAPI TestClient, and a 1,000-task latency test

**Target Platform**: Local HTTP server on Linux or Windows; bind to loopback by default

**Project Type**: Single-project REST API

**Performance Goals**: With 1,000 tasks, at least 95 of 100 list/filter/sort requests complete under 1 second

**Constraints**: No authentication, notifications, multi-user support, cloud database, or
user-selected persistence paths; serialize updates within one application process

**Scale/Scope**: One local task collection; 1,000-task documented performance dataset

## Constitution Check

- Modular routes, Pydantic schemas, services, and JSON storage: PASS
- RESTful paths, validation, status codes, and generated OpenAPI response schemas: PASS
- Configured local path only; sanitized API errors and atomic writes: PASS
- Unit/endpoint tests and at least 80% line coverage: PASS
- Ruff lint/format and Bandit checks: PASS
- CI dependency audit and secret scan: PASS
- Requirement IDs map from the specification to implementation and tests: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── tasks.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py
├── models.py
├── storage.py
├── services.py
└── routes.py

tests/
├── conftest.py
├── test_tasks.py
├── test_filters.py
└── test_storage.py

scripts/
└── check_secrets.py

.github/
└── workflows/
    └── ci.yml
```

**Structure Decision**: Use the user-selected flat `src/` layout, with separate model, storage,
service, route, and application modules. Tests use the requested three feature-oriented files,
with shared fixtures in `tests/conftest.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | No constitution violations identified | Not applicable |

