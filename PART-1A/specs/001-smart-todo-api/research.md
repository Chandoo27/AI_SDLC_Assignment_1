# Research

## Decision: Python 3.11+ with FastAPI

**Rationale**: The project constitution requires Python and FastAPI. Python 3.11 provides modern typing and broad package compatibility, while FastAPI supplies OpenAPI generation, Pydantic validation, and async HTTP handlers.

**Alternatives considered**:
- Flask: simpler, but lacks the constitution-aligned FastAPI schema and validation integration.
- Django REST Framework: stronger framework defaults but unnecessary for this single-resource API.

## Decision: Pydantic v2 request and response models

**Rationale**: Pydantic v2 provides explicit field constraints, trim-aware validation, and clear 422 responses for malformed or invalid input.

**Alternatives considered**:
- Pydantic v1: compatible with older FastAPI releases, but v2 is preferred for current maintained dependencies.
- Manual validation: would duplicate framework behavior and increase implementation and test burden.

## Decision: UUIDs and UTC ISO 8601 creation dates

**Rationale**: UUID strings provide unique task IDs without coordination. UTC ISO 8601 timestamps provide stable persistence and lexical/chronological ordering.

**Alternatives considered**:
- Integer IDs: easy to implement but do not provide the globally unique behavior assumed by the specification.
- Local timestamps: can be ambiguous across restarts and machines.

## Decision: JSON repository with an in-process lock and atomic replacement

**Rationale**: A repository module is the narrowest abstraction that separates JSON persistence from HTTP behavior. An async-safe or thread-safe lock serializes read-modify-write operations. Atomic temp-file replacement prevents partially written JSON after a process interruption.

**Alternatives considered**:
- SQLite: violates the no-database/no-cloud-storage scope and adds an unnecessary schema dependency.
- Direct writes to the configured JSON file: risks truncated or malformed persisted data.

## Decision: Stable JSON error shape

**Rationale**: A shared FastAPI exception handler will return `{"code": "...", "message": "...", "details": [...]}` consistently. Validation errors will identify fields without echoing unsafe values; internal data-file errors will use generic 500 codes.

**Alternatives considered**:
- FastAPI's default validation shape: not one shared shape and not suitable for stable machine-readable error codes.
- Stack-trace or exception-detail responses: prohibited by the constitution and specification.

## Decision: Locking and update serialization

**Rationale**: The service will hold one lock while loading the latest collection, applying a partial update, and persisting it. This makes concurrent updates sequential and gives the last serialized request state for same-field conflicts.

**Alternatives considered**:
- Optimistic versioning: not requested and would reject conflicting updates, contrary to the clarified behavior.
- File locking alone: insufficient for coordinating separate in-memory operations without stale overwrites.

## Decision: Test stack

**Rationale**: pytest and FastAPI's TestClient cover endpoint behavior, while unit tests cover validation and persistence. Ruff handles lint/format, pytest-cov enforces coverage, Bandit checks source security, pip-audit checks dependencies, and a secret scanner is required by CI.

**Alternatives considered**:
- unittest only: less consistent with the existing Python ecosystem and offers weaker fixture/plugin support.

