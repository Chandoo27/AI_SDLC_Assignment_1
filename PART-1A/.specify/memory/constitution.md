<!--
Sync Impact Report
Version change: unratified scaffold -> 1.0.0 (initial ratification)
Modified principles: placeholders -> I. Modular Architecture and Local JSON Storage;
  II. RESTful API and Complete Validation; III. Secure by Default;
  IV. Automated Quality and Testing; V. Traceability and Simplicity
Added sections: Engineering Quality Standards; Delivery and Documentation
Removed sections: none
Follow-up TODOs: none
-->

# Smart Todo API Constitution

## Core Principles

### I. Modular Architecture and Local JSON Storage
The backend MUST use Python and FastAPI. Modules MUST separate API routing, request and
response schemas, business logic, and JSON persistence so each concern can be tested
independently. Todo data MUST persist in local JSON files; database services MUST NOT be
introduced without an approved specification amendment. File locations MUST be controlled by
application configuration, never by untrusted request input. JSON writes MUST avoid leaving a
partially written data file. This structure keeps the application understandable and the data
store easy to inspect and back up.

### II. RESTful API and Complete Validation
Endpoints MUST use resource-oriented paths and HTTP methods, return appropriate HTTP status
codes, and use JSON representations. Every request value supplied through a path, query,
header, or body MUST be validated with explicit types and constraints before business logic
runs. Invalid input MUST receive HTTP 422; missing resources MUST receive HTTP 404; successful
creation MUST receive HTTP 201; successful deletion MUST receive HTTP 204. Responses MUST NOT
claim success when an operation failed.

### III. Secure by Default
Source code and committed configuration MUST contain no secrets, API keys, or credentials.
Sensitive configuration MUST be supplied outside source control. The API MUST NOT expose
internal paths, stack traces, or secret values in client-facing errors. Request data MUST NOT
be used to select arbitrary filesystem paths. Security issues MUST be reported with
consistent, actionable errors that disclose no implementation-sensitive details.

### IV. Automated Quality and Testing
Core business and persistence behavior MUST have unit tests. Every endpoint MUST have tests
for its successful behavior and applicable validation and error cases. Core modules MUST
maintain at least 80% line coverage. Before a change is accepted, automated CI checks MUST
pass: Ruff lint and format checks, the pytest suite with coverage enforcement, Bandit static
security analysis, pip-audit dependency checks, and an automated secret scan. No unresolved
high- or critical-severity security finding may be accepted without a documented, approved
exception.

### V. Traceability and Simplicity
Every implementation task and acceptance criterion MUST link to a uniquely identified
specification requirement. Each acceptance criterion MUST be objectively measurable and
verifiable by a test, a documented inspection, or a reproducible check. Changes MUST implement
only approved requirements; abstractions, dependencies, and configuration MUST be added only
when they solve a stated need. This keeps scope controlled and makes compliance auditable.

## Engineering Quality Standards

API errors MUST use one documented JSON shape with a stable machine-readable code and a
meaningful human-readable message. Validation details MUST identify the invalid field without
echoing unsafe input. Persistence behavior MUST be tested for valid reads and writes, malformed
or missing data files, and survival of saved todos across application restarts. Endpoint
documentation MUST describe inputs, constraints, response schemas, and status codes through
FastAPI's generated OpenAPI documentation.

## Delivery and Documentation

Each feature specification MUST state its requirement IDs, measurable acceptance criteria,
and corresponding test coverage. Implementation tasks MUST reference those requirement IDs.
Changes to endpoint behavior, validation, error responses, or persistence formats MUST update
the relevant documentation and tests in the same change. A change is complete only when its
automated checks pass and its requirements can be traced from specification to implementation
and verification.

## Governance

This constitution governs project specifications, plans, tasks, implementation, and reviews.
Amendments MUST document the reason, impact, and migration implications, update the version,
and record the amendment date. Versioning follows semantic versioning: MAJOR for incompatible
governance changes, MINOR for new or materially expanded principles, and PATCH for clarifications
that do not change obligations. Every specification and code review MUST verify compliance
with applicable principles and traceability requirements. Exceptions MUST be explicit,
justified, approved, and time-bounded; complexity that is not required by an approved
specification MUST be rejected.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
