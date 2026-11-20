<!--
Sync Impact Report
Version change: unratified scaffold -> 1.0.0 (initial ratification)
Modified principles: placeholders -> I. Natural-Language Intent and Safe Clarification;
  II. Schema-First JSON Contract; III. Validate Before Acting;
  IV. Evaluation-Driven Quality; V. Traceable Simplicity
Added sections: Evaluation and Acceptance Standards; Security, Testing, and Documentation
Removed sections: none
Follow-up TODOs: none
-->

# Natural Language Reminder Agent Constitution

## Core Principles

### I. Natural-Language Intent and Safe Clarification
The agent MUST accept natural-language requests to create, reschedule, and snooze reminders.
It MUST identify the requested operation and extract only information supported by the request
and conversation context. It MUST ask a focused clarification question whenever a mandatory
field is missing or materially ambiguous; it MUST NOT invent a date, time, time zone, reminder
identity, or other required value. Each supported operation and its mandatory fields MUST be
defined in the feature specification and represented in the evaluation cases. These rules
prevent a plausible-sounding response from causing the wrong reminder change.

### II. Schema-First JSON Contract
Every agent response MUST be a single JSON object conforming to the project's versioned JSON
Schema, including successful actions, clarification requests, and validation or processing
errors. The schema MUST define the response kind, required fields, allowed values, and
operation-specific data; responses MUST NOT append prose outside the JSON object. Schema
validation MUST run in the evaluation harness and in automated tests. Schema changes MUST be
versioned and documented alongside their compatibility impact.

### III. Validate Before Acting
All parsed inputs and proposed actions MUST be validated against explicit types, allowed
operations, required fields, value constraints, and date/time rules before an action is
executed. Invalid or inconsistent values MUST result in a schema-conforming clarification or
error response and MUST NOT mutate reminder state. Tests MUST prove this no-mutation behavior
for invalid requests. Validation rules and their user-visible outcomes MUST be documented.

### IV. Evaluation-Driven Quality
An automated, repeatable evaluation harness is mandatory. Every functional requirement MUST
have one or more uniquely identified evaluation cases and a trace to the implementation that
satisfies it. The harness MUST measure JSON/schema validity, property validity, and semantic
correctness separately, and MUST report per-case results and aggregate scores. Acceptance
requires 100% schema-valid outputs, 100% correct clarification when mandatory information is
missing, 100% safe rejection or clarification of invalid inputs, at least 95% semantic
correctness overall, and at least 90% semantic correctness for each supported operation.
Results MUST be reproducible from a documented command and versioned evaluation data.

### V. Traceable Simplicity
Requirements, acceptance criteria, evaluation cases, tests, and implementation MUST be linked
by stable identifiers in a traceability record; no requirement is complete without a passing
evaluation case and corresponding implementation reference. The design MUST use the smallest
clear solution that satisfies approved requirements. New dependencies, abstractions, and
configuration MUST have a documented need, and unrelated behavior MUST NOT be added. This
keeps the agent auditable and maintainable as its contract evolves.

## Evaluation and Acceptance Standards

Each feature specification MUST assign stable IDs to requirements and measurable acceptance
criteria. The traceability record MUST map every requirement ID to at least one evaluation
case ID, relevant test ID, and implementation file or symbol. A requirement without all
three links blocks acceptance.

Evaluation cases MUST cover every supported operation, valid requests, missing mandatory
fields, ambiguous dates or reminder identity, invalid values, boundary values, and malformed
or unsupported requests. The harness MUST check:

- **Schema validity**: every response parses as exactly one JSON object and validates against
  the active schema; acceptance threshold is 100%.
- **Property validity**: required fields, types, enums, cross-field constraints, and
  operation-specific invariants are correct; invalid input never triggers a reminder mutation.
  Acceptance threshold is 100% on deterministic property cases.
- **Semantic validity**: the output action, extracted values, clarification, or rejection
  matches the user's intent and the documented rules. Acceptance threshold is at least 95%
  overall and at least 90% for each supported operation.
- **Clarification behavior**: every case missing or materially ambiguous on a mandatory field
  asks for the missing information without fabricating it; acceptance threshold is 100%.

The harness MUST fail the build when a threshold is missed, a required case is absent, or
traceability is incomplete. Evaluation reports MUST record the schema and dataset versions,
case-level outcomes, aggregate metrics, and the command used to run them.

## Security, Testing, and Documentation

Reminder text and user inputs MUST be treated as untrusted data, not executable instructions.
The implementation MUST validate lengths and types at its input boundary, avoid exposing
secrets or internal details in responses, and avoid logging reminder content unless explicitly
required and documented. Source control MUST contain no credentials or secrets. Automated
security and quality checks MUST include secret scanning, dependency vulnerability checking,
and the project's configured static analysis and lint/type checks. Acceptance requires all
required checks to pass and zero unresolved critical or high severity findings; any exception
MUST identify its owner, rationale, mitigation, and expiry.

Tests MUST include unit tests for parsing, validation, clarification decisions, and response
serialization; schema-validation tests for every response kind; property-based tests for
input and output invariants; and semantic evaluation cases for each operation and edge case.
The core decision, validation, and serialization code MUST maintain at least 90% line
coverage. All required tests MUST pass before acceptance.

Documentation MUST define the JSON Schema, operation-specific mandatory fields, date/time
and time-zone interpretation, validation and error behavior, evaluation commands, thresholds,
and traceability mapping. Any change to behavior, schema, validation, evaluation data, or
thresholds MUST update the relevant documentation and tests in the same change.

## Governance

This constitution governs specifications, plans, tasks, implementation, evaluation, and
reviews for the Natural Language Reminder Agent. Amendments MUST document the reason, impact,
and migration implications, update the version, and record the amendment date. Versioning
follows semantic versioning: MAJOR for incompatible changes to principles or obligations,
MINOR for new principles or materially expanded requirements, and PATCH for clarifications
that do not change obligations. Every specification and code review MUST verify compliance,
including complete requirement-to-evaluation-to-implementation traceability. Exceptions MUST
be explicit, justified, approved, and time-bounded; complexity not required by an approved
specification MUST be rejected.

**Version**: 1.0.0 | **Ratified**: 2026-11-19 | **Last Amended**: 2026-11-19
