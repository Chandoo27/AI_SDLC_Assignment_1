# Tasks: Smart Todo API

**Input**: Design documents from `specs/001-smart-todo-api/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/tasks.openapi.yaml`

**Organization**: Tasks follow the user's selected `src/` layout and are grouped by the three prioritized user stories.

## Phase 1: Setup

- [X] T001 [P] Create `pyproject.toml` with Python 3.11+ metadata and FastAPI, Pydantic, Uvicorn, pytest, pytest-cov, httpx2, Ruff, Bandit, pip-audit, and detect-secrets dependencies (FR-001, NFR-005).
- [X] T002 [P] Create the requested modules `src/main.py`, `src/models.py`, `src/storage.py`, `src/services.py`, `src/routes.py`, and test files `tests/test_tasks.py`, `tests/test_filters.py`, and `tests/test_storage.py` (FR-001, FR-003, FR-009).
- [X] T003 [P] Configure Python ignores in `.gitignore`, lint rules in `ruff.toml`, Bandit settings in `.bandit`, and the secret-scan entry point in `scripts/check_secrets.py` (NFR-005).

## Phase 2: Foundational

**Purpose**: Establish validated task models, JSON persistence, isolated tests, and common API errors before story implementation.

- [X] T004 [P] Add model-validation cases in `tests/test_tasks.py` for trimmed titles of 1-200 characters, descriptions trimmed to 0-5,000 characters, priorities `High`, `Medium`, or `Low`, 0-20 case-insensitively unique tags of 1-32 characters, defaults, UTC timestamps, and rejected immutable/unknown fields (FR-001, FR-002, FR-004, FR-010, AC-001-005).
- [X] T005 Implement Pydantic enums and create/update/response/error models in `src/models.py`, including field constraints, case-insensitive tag de-duplication, immutable IDs/timestamps, and rejection of empty updates (FR-001, FR-002, FR-004, FR-006, FR-010, FR-011).
- [X] T006 [P] Add persistence tests in `tests/test_storage.py` for missing-file initialization, full-field round trips, malformed-file preservation, and serialized concurrent updates (FR-004, FR-009, NFR-001, NFR-003, NFR-004, AC-011, AC-013, AC-017).
- [X] T007 Implement configured local JSON persistence in `src/storage.py`; serialize read-modify-write operations, atomically replace completed writes, treat a missing file as an empty collection, and surface malformed/unreadable data without replacing it (FR-009, FR-011, NFR-001, NFR-003, NFR-004).
- [X] T008 Create isolated temporary-file and TestClient fixtures in `tests/conftest.py`, with the data-file path injected through `src/main.py` for tests (FR-009, NFR-003).
- [X] T009 [P] Add API error tests in `tests/test_tasks.py` for the stable JSON shape, field-specific 422 details, 404 errors, and sanitized persistence failures (FR-010, FR-011, AC-006, AC-012, AC-013).
- [X] T010 Implement FastAPI app creation and shared exception handling in `src/main.py`; return the common error schema without stack traces, secret values, or filesystem paths, using HTTP 422/404/500 for invalid input, missing tasks, and persistence failures (FR-010, FR-011).

## Phase 3: User Story 1 - Manage Tasks (Priority: P1) — MVP

**Goal**: Create, list, retrieve, partially update, and delete tasks.

**Independent Test**: Create and retrieve a task, list it, update only selected fields, delete it, and verify a later lookup returns 404.

- [X] T011 [P] [US1] Add service and concurrency tests in `tests/test_storage.py` and `tests/test_tasks.py` for CRUD behavior, immutable fields, not-found errors, and serialized updates where different fields persist and the last same-field update wins (FR-002-FR-005, FR-010, AC-002, AC-005-007, AC-017).
- [X] T012 [P] [US1] Add endpoint tests in `tests/test_tasks.py` for create/list/get/update/delete, defaults, validation boundaries, invalid requests leaving stored data unchanged, and HTTP 201/200/204/404/422 responses (FR-001-FR-005, FR-010, FR-011, NFR-003, AC-001-007, AC-012).
- [X] T013 [US1] Implement task creation, retrieval, partial updates, and deletion in `src/services.py`, preserving omitted fields and applying updates to the latest state (FR-002-FR-005, FR-010, AC-005-007, AC-017).
- [X] T014 [US1] Implement CRUD routes in `src/routes.py` using Pydantic request/response models and service methods; validate UUID path values and return specified status codes (FR-001-FR-005, FR-010, FR-011).
- [X] T015 [US1] Wire the JSON store and task service into `src/main.py`, register the router, and keep persistence paths outside request input (FR-003, FR-009, FR-012, NFR-001).

## Phase 4: User Story 2 - Organize and Find Tasks (Priority: P2)

**Goal**: Filter by one or more tags and sort by priority.

**Independent Test**: Verify case-insensitive match-any filtering, no-match results, deterministic priority order, and combined filtering/sorting.

- [X] T016 [P] [US2] Add filter and ordering tests in `tests/test_filters.py` for exact case-insensitive tag matching, match-any semantics, empty results, and priority/date/ID ordering (FR-007, FR-008, AC-009-010).
- [X] T017 [P] [US2] Add endpoint tests in `tests/test_filters.py` for repeated and comma-separated `tags`, `sort=priority`, invalid query values, and combined filters (FR-007, FR-008, FR-010, AC-009-010).
- [X] T018 [US2] Implement match-any tag filtering and deterministic priority sorting in `src/services.py`: High, Medium, Low, then `createdAt` ascending and ID ascending (FR-007, FR-008).
- [X] T019 [US2] Extend the list route in `src/routes.py` to validate and combine optional tag filters and priority sort while preserving the unfiltered default (FR-003, FR-007, FR-008, FR-010).

## Phase 5: User Story 3 - Complete Tasks and Keep Their Data (Priority: P3)

**Goal**: Complete/reopen tasks and preserve all task fields across application restarts.

**Independent Test**: Complete and reopen a task, repeat both operations, recreate the app against the same JSON file, and verify all fields and status persist.

- [X] T020 [P] [US3] Add status-transition tests in `tests/test_tasks.py` for Pending-to-Completed, Completed-to-Pending, idempotent repeats, and unknown IDs (FR-006, FR-010, AC-006, AC-008, AC-016).
- [X] T021 [P] [US3] Add restart and persistence endpoint tests in `tests/test_tasks.py` and `tests/test_storage.py` for missing files, full-field survival across app recreation, and malformed-file preservation with sanitized HTTP 500 responses (FR-006, FR-009-FR-011, NFR-001, NFR-004, AC-008, AC-011, AC-013, AC-016).
- [X] T022 [US3] Implement idempotent complete/reopen service operations in `src/services.py`, persisting only status changes (FR-006, FR-009, AC-008, AC-011, AC-016).
- [X] T023 [US3] Add `POST /tasks/{task_id}/complete` and `/reopen` routes in `src/routes.py` with HTTP 200 success and the shared HTTP 404 response (FR-006, FR-010, FR-011).

## Phase 6: Polish and Cross-Cutting Validation

- [X] T024 [P] Add a repeatable 1,000-task benchmark in `tests/test_filters.py`; record the test machine and verify at least 95 of 100 list/filter/sort requests finish under one second (NFR-002, AC-015).
- [X] T025 Verify the runnable setup and CRUD/filter/sort/status/restart scenarios in `specs/001-smart-todo-api/quickstart.md`, and keep `specs/001-smart-todo-api/contracts/tasks.openapi.yaml` aligned with generated OpenAPI response schemas (FR-010, FR-011).
- [X] T026 Run pytest with the 80% coverage gate, Ruff lint/format, Bandit, `pip-audit --skip-editable`, and `python scripts/check_secrets.py`; resolve failures and verify excluded product features remain out of scope (FR-012, NFR-005).
- [X] T027 Add `.github/workflows/ci.yml` to run pytest/coverage, Ruff, Bandit, pip-audit, and the secret scanner on supported Python versions, failing the workflow on any check failure (NFR-005, AC-018, SC-005).

## Requirement Traceability

- FR-001: T001-T005, T012-T014
- FR-002: T004-T005, T011-T013
- FR-003: T011-T015, T019
- FR-004: T006-T007, T011-T014
- FR-005: T011-T014
- FR-006: T005, T020-T023
- FR-007: T016-T019
- FR-008: T016-T019
- FR-009: T006-T008, T015, T021-T022
- FR-010: T004-T005, T009-T010, T012, T014, T017, T019-T021, T023, T025
- FR-011: T005, T007, T009-T010, T012, T014, T021, T023, T025
- FR-012: T015, T026
- NFR-001: T007, T015, T021
- NFR-002: T024
- NFR-003: T006-T008, T012
- NFR-004: T006-T007, T021-T022
- NFR-005: T001, T003, T026-T027

## Dependencies and Execution Order

- **Setup**: T001-T003 are independent.
- **Foundational**: Depends on Setup; tests precede the corresponding model, storage, and error-handler implementations.
- **US1**: Depends on the foundational models, store, and app; delivers the MVP.
- **US2**: Extends the US1 list service and route.
- **US3**: Uses the shared service and store from the foundation/US1.
- **Polish**: Requires all selected stories.

## Parallel Opportunities

- Setup tasks T001-T003 target separate files.
- Foundation test tasks T004, T006, and T009 target separate test behavior/files.
- US1 test tasks T011 and T012, US2 tasks T016 and T017, and US3 tasks T020 and T021 can be authored in parallel.
- T024 can run independently after the list endpoint is complete.

## Implementation Strategy

1. Complete setup and shared models/storage/error handling.
2. Deliver US1 CRUD as the MVP and verify its independent journey.
3. Add US2 filtering and priority sorting.
4. Add US3 completion/reopening and restart persistence.
5. Run benchmark, quickstart scenarios, coverage, lint, security, dependency, and secret checks.
