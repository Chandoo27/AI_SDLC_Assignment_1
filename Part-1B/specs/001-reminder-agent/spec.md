# Feature Specification: Natural Language Reminder Agent

**Feature Branch**: `001-reminder-agent`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: Build a Natural Language Reminder Agent that accepts natural language reminder requests and returns structured JSON for creating, rescheduling, snoozing, or clarifying reminders.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Reminder (Priority: P1)

A user asks in natural language to be reminded about a task at a date and time. The agent identifies the create intent, extracts the task and requested time, and returns a JSON action that a reminder consumer can use.

**Why this priority**: Creating a reminder is the primary use case and is demonstrated by all provided examples.

**Independent Test**: Submit a request containing an unambiguous task and time; verify the JSON expresses a create action with the extracted task and equivalent date and time.

**Acceptance Scenarios**:

1. **Given** a request such as “Remind me tomorrow at 6 PM to pay electricity bill” and a known reference date and time zone, **When** the agent processes it, **Then** it returns a schema-valid create action with the task and resolved date and time.
2. **Given** a request such as “Remind me in 30 minutes to submit the assignment” and a known reference time, **When** the agent processes it, **Then** the returned date and time is 30 minutes after that reference time.

### User Story 2 - Reschedule or Snooze a Reminder (Priority: P2)

A user asks to change the scheduled time of an existing reminder or to snooze it. The agent identifies the requested operation and returns the target reminder and requested new time, or asks for missing information.

**Why this priority**: Changing an existing reminder is a required capability, but depends on correctly identifying both the action and its target.

**Independent Test**: Submit separate unambiguous reschedule and snooze requests with a target reminder and a known time reference; verify each response identifies the correct intent, target task, and resulting date and time.

**Acceptance Scenarios**:

1. **Given** an existing reminder and a request to reschedule it to an unambiguous time, **When** the agent processes it, **Then** it returns a schema-valid reschedule action without changing the reminder task.
2. **Given** an existing reminder and an unambiguous snooze duration, **When** the agent processes it, **Then** it returns a schema-valid snooze action with the resulting date and time.
3. **Given** multiple reminders could match the target description, **When** the agent processes a reschedule or snooze request, **Then** it requests clarification rather than selecting a reminder arbitrarily.

### User Story 3 - Clarify Incomplete or Invalid Requests (Priority: P1)

A user provides a request with missing, ambiguous, or invalid mandatory information. The agent returns a schema-valid response indicating that clarification is needed and does not invent the missing value or request an unsafe action.

**Why this priority**: Safe clarification is essential to prevent incorrect reminders and is required by the project constitution.

**Independent Test**: Submit requests missing task, date/time, or target reminder information and verify each response follows the agreed clarification representation and does not fabricate values.

**Acceptance Scenarios**:

1. **Given** a create request with no task, **When** the agent processes it, **Then** it indicates that clarification is needed and asks for the task.
2. **Given** a request with a date but no required time, **When** the agent processes it, **Then** it indicates that clarification is needed and asks for the time.
3. **Given** malformed or unsupported input, **When** the agent processes it, **Then** it returns a schema-valid safe response and does not produce a reminder action.

### Edge Cases

- Relative dates such as “tomorrow” and weekdays are resolved using an explicit reference date and time zone; if either needed context is unavailable, the agent asks for clarification.
- A date in the past, an invalid calendar date, or a time made ambiguous by a daylight-saving transition is not silently adjusted; the agent requests clarification or returns a safe invalid-request response.
- A request with multiple tasks or multiple candidate reminders in the supplied context requires clarification before selecting one.
- An empty request, whitespace-only request, unsupported language, or unrelated request does not produce a create, reschedule, or snooze action.
- If clarification is required, the output continues to conform to the response schema and includes a clarification question.
- User-provided text is treated as data and cannot override the agent's validation rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST accept a natural-language request and identify whether it asks to create, reschedule, snooze, or clarify a reminder.
- **FR-002**: For a create request, the agent MUST extract the reminder task and requested date and time when both are present and unambiguous.
- **FR-003**: For a reschedule request, the agent MUST extract the target reminder and requested replacement date and time.
- **FR-004**: For a snooze request, the agent MUST extract the target reminder and snooze duration or requested replacement date and time, and resolve it to a date and time when the required reference context is available.
- **FR-005**: The agent MUST detect missing or materially ambiguous mandatory information and request clarification instead of inventing a value or selecting a reminder arbitrarily.
- **FR-006**: The agent MUST return exactly one JSON object with the required fields `intent` (string), `task` (string), `datetime` (string), `needs_clarification` (boolean), and `clarification_question` (string). The clarification question MUST be non-empty when clarification is needed and empty otherwise. It MUST NOT emit non-JSON prose alongside the object.
- **FR-007**: The JSON object MUST conform to a documented schema for successful actions, clarification responses, and safely handled invalid or unsupported requests.
- **FR-008**: The agent MUST validate input and proposed action properties, including request text that is non-empty after trimming and no longer than 4,096 characters before trimming, operation, required fields, task and target identity, date and time validity, and cross-field consistency, before returning an actionable result.
- **FR-009**: Invalid, malformed, or unsupported requests MUST NOT yield an actionable reminder operation or cause a reminder state change.
- **FR-010**: Each functional requirement MUST map to one or more uniquely identified evaluation cases and tests; its implementation mapping MUST be completed before implementation acceptance.
- **FR-011**: The evaluation harness MUST report schema validity, property validity, semantic correctness, per-case outcomes, and aggregate results, and MUST fail when a required threshold or traceability check is unmet.

### Response Contract

Every response MUST contain the five required fields below and no additional fields:

```json
{
  "intent": "create",
  "task": "pay electricity bill",
  "datetime": "2026-11-20T18:00:00+05:30",
  "needs_clarification": false,
  "clarification_question": ""
}
```

The active response contract MUST validate against this JSON Schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["intent", "task", "datetime", "needs_clarification", "clarification_question"],
  "properties": {
    "intent": {
      "type": "string",
      "enum": ["create", "reschedule", "snooze", "clarification"]
    },
    "task": { "type": "string" },
    "datetime": {
      "oneOf": [
        { "const": "" },
        { "type": "string", "format": "date-time" }
      ]
    },
    "needs_clarification": { "type": "boolean" },
    "clarification_question": { "type": "string" }
  },
  "allOf": [
    {
      "if": {
        "properties": { "needs_clarification": { "const": true } },
        "required": ["needs_clarification"]
      },
      "then": {
        "properties": {
          "intent": { "const": "clarification" },
          "clarification_question": { "minLength": 1 }
        }
      },
      "else": {
        "properties": {
          "intent": { "enum": ["create", "reschedule", "snooze"] },
          "task": { "minLength": 1 },
          "datetime": { "type": "string", "format": "date-time", "minLength": 1 },
          "clarification_question": { "maxLength": 0 }
        }
      }
    }
  ]
}
```

- `intent` MUST be one of `create`, `reschedule`, `snooze`, or `clarification`.
- `task` MUST contain the reminder description or target task when known; otherwise it MUST be an empty string.
- `datetime` MUST contain an ISO 8601 date-time with a UTC offset when known; otherwise it MUST be an empty string.
- `needs_clarification` MUST be `true` when required information is absent or ambiguous, and `false` only when the agent can return an actionable reminder request.
- `clarification_question` MUST be a non-empty string when `needs_clarification` is `true` and MUST be an empty string otherwise.
- A clarification response MUST use `intent: "clarification"` and MUST NOT represent an actionable create, reschedule, or snooze operation.

### Non-Functional Requirements

- **NFR-001**: 100% of evaluated responses MUST parse as exactly one JSON object and pass validation against the active response schema.
- **NFR-002**: 100% of deterministic property-validation cases MUST pass, including the requirement that invalid input produces no actionable result or state mutation.
- **NFR-003**: Semantic correctness MUST be at least 95% overall and at least 90% for each supported operation; clarification cases with missing mandatory information MUST be correct in 100% of evaluation cases.
- **NFR-004**: Evaluation data and schema MUST be versioned, and each evaluation report MUST identify their versions and the reproducible command used to run the harness.
- **NFR-005**: Automated security and quality checks MUST include secret scanning, dependency vulnerability checking, and configured static analysis and lint/type checks; acceptance requires all checks to pass and zero unresolved critical or high severity findings.
- **NFR-006**: Core decision, validation, and serialization behavior MUST maintain at least 90% line coverage, with unit, schema, property-based, and semantic evaluation tests.
- **NFR-007**: User inputs MUST be treated as untrusted data; responses MUST NOT disclose secrets or internal error details, and reminder content MUST NOT be logged unless explicitly required and documented.
- **NFR-008**: The schema, mandatory fields, date/time and time-zone interpretation, validation behavior, evaluation procedure, thresholds, and traceability mapping MUST be documented and kept in sync with changes.

### Acceptance Criteria

- **AC-001**: All output examples and evaluation responses validate against the single active schema, with a measured schema-valid rate of 100% (FR-006, FR-007, NFR-001; evaluation cases EV-SCHEMA-*).
- **AC-002**: Each of create, reschedule, and snooze has valid, missing-field, ambiguous, and invalid-input evaluation coverage; semantic correctness is at least 95% overall and at least 90% per operation (FR-001–FR-005; EV-CREATE-*, EV-RESCHEDULE-*, EV-SNOOZE-*, EV-CLARIFY-*; NFR-003).
- **AC-003**: Every missing or ambiguous mandatory-field case requests clarification without fabricating information; the pass rate is 100% (FR-005; EV-CLARIFY-*; NFR-003).
- **AC-004**: Every deterministic invalid-input property case passes, and no such case returns an actionable operation or mutates reminder state (FR-008, FR-009; EV-PROP-*; NFR-002).
- **AC-005**: The traceability record links every FR/NFR to evaluation cases, tests, and implementation references before implementation is accepted; the harness fails on any missing link (FR-010, FR-011; EV-TRACE-*).
- **AC-006**: All required security, quality, and test checks pass, core decision/validation/serialization coverage is at least 90%, and there are no unresolved critical or high severity security findings (NFR-005, NFR-006).
- **AC-007**: Documentation includes the response schema, date/time interpretation, evaluation command and thresholds, and traceability process (NFR-004, NFR-008).
- **AC-008**: User request content is not included in routine reports or logs, and invalid input cannot expose secrets or internal error details (NFR-007; EV-INPUT-UNTRUSTED, EV-ERROR-REDACTION, EV-LOGGING).

### Requirement-to-Evaluation Traceability

| Requirement | Evaluation case IDs | Test IDs | Implementation area to map during planning |
|---|---|---|---|
| FR-001 | EV-INTENT-CREATE, EV-INTENT-RESCHEDULE, EV-INTENT-SNOOZE, EV-INTENT-CLARIFY | TEST-INTENT | Intent classification |
| FR-002 | EV-CREATE-VALID, EV-CREATE-MISSING-TASK, EV-CREATE-MISSING-TIME | TEST-CREATE-EXTRACT | Request parsing and create action |
| FR-003 | EV-RESCHEDULE-VALID, EV-RESCHEDULE-MISSING-TARGET, EV-RESCHEDULE-AMBIGUOUS-TARGET | TEST-RESCHEDULE-EXTRACT | Request parsing and reschedule action |
| FR-004 | EV-SNOOZE-DURATION, EV-SNOOZE-UNTIL, EV-SNOOZE-MISSING-TARGET | TEST-SNOOZE-EXTRACT | Request parsing and snooze action |
| FR-005 | EV-CLARIFY-MISSING-TASK, EV-CLARIFY-MISSING-TIME, EV-CLARIFY-AMBIGUOUS-TARGET | TEST-CLARIFICATION | Required-field validation and clarification |
| FR-006 | EV-SCHEMA-CREATE, EV-SCHEMA-RESCHEDULE, EV-SCHEMA-SNOOZE, EV-SCHEMA-CLARIFY, EV-SCHEMA-ERROR | TEST-JSON-CONTRACT | Response serialization |
| FR-007 | EV-SCHEMA-* | TEST-SCHEMA-VALIDATION | Response schema and validation |
| FR-008 | EV-PROP-DATE, EV-PROP-TASK, EV-PROP-OPERATION, EV-PROP-CONSISTENCY, EV-PROP-REQUEST-LENGTH | TEST-PROPERTY-VALIDATION | Input and action validation |
| FR-009 | EV-INVALID-MALFORMED, EV-INVALID-UNSUPPORTED, EV-PROP-NO-MUTATION | TEST-SAFE-INVALID-INPUT | Invalid-request handling |
| FR-010 | EV-TRACE-COMPLETE, EV-TRACE-MISSING-LINK | TEST-TRACEABILITY | Traceability record |
| FR-011 | EV-HARNESS-REPORT, EV-HARNESS-THRESHOLD-FAIL | TEST-HARNESS-REPORT | Evaluation harness |
| NFR-001 | EV-SCHEMA-* | TEST-SCHEMA-THRESHOLD | Schema tests and evaluation |
| NFR-002 | EV-PROP-* | TEST-PROPERTY-THRESHOLD | Property tests |
| NFR-003 | EV-SEMANTIC-*, EV-CLARIFY-* | TEST-SEMANTIC-THRESHOLD | Semantic evaluation |
| NFR-004 | EV-REPORT-VERSION, EV-REPORT-COMMAND | TEST-EVALUATION-REPRODUCIBILITY | Evaluation reporting |
| NFR-005 | EV-SECURITY-* | TEST-SECURITY-QUALITY-GATES | Security and quality checks |
| NFR-006 | EV-COVERAGE, EV-UNIT-*, EV-PROP-* | TEST-COVERAGE-AND-CATEGORIES | Test suite |
| NFR-007 | EV-INPUT-UNTRUSTED, EV-ERROR-REDACTION, EV-LOGGING | TEST-INPUT-SECURITY | Input boundary and error handling |
| NFR-008 | EV-DOC-SCHEMA, EV-DOC-DATETIME, EV-DOC-EVAL, EV-DOC-TRACE | TEST-DOCUMENTATION-COMPLETENESS | User and evaluation documentation |

## Key Entities

- **Reminder request**: The user's natural-language instruction, including intended operation, task or target reminder, and temporal expression.
- **Reminder action**: The normalized operation and task/target with its requested date and time.
- **Resolution context**: Reference time, configured time zone, and optional existing reminder task descriptions supplied by the caller to resolve relative dates and target matching.
- **Clarification**: A response state indicating that required information is absent or ambiguous and must be obtained before an actionable reminder result is returned.
- **Evaluation case**: A versioned input and expected properties and meaning used to validate schema, property, semantic, and traceability behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of outputs in the required evaluation suite are valid JSON objects conforming to the active schema.
- **SC-002**: 100% of deterministic property cases pass, and no malformed, unsupported, or invalid request yields an actionable reminder result.
- **SC-003**: At least 95% of semantic evaluation cases are correct overall and at least 90% are correct for each supported operation.
- **SC-004**: 100% of test cases missing or materially ambiguous on a mandatory field request clarification without fabricating the missing value.
- **SC-005**: 100% of functional and non-functional requirements have evaluation-case and test links; every requirement also has an implementation reference before implementation acceptance.
- **SC-006**: At least 90% line coverage is achieved for core decision, validation, and serialization behavior, with all required security and quality checks passing.

## Assumptions

- The agent emits JSON actions only; actual notification delivery and reminder persistence are handled by an external consumer.
- The response contains the five fields in the current required output schema; `clarification_question` is empty for actionable results and non-empty for clarification results.
- The `task` field contains the reminder text for creation and identifies an existing reminder for reschedule or snooze. If task text matches multiple reminders or none can be identified, the agent asks for clarification.
- The caller supplies reference time, configured time zone, and available reminder task descriptions as resolution context when needed; the agent does not maintain reminder state.
- Date/time output uses an ISO 8601 representation with a UTC offset. An explicit time zone in the request takes precedence; otherwise, relative expressions use the configured user time zone and current clock. If the configured time zone or required reference time is unavailable, the agent asks for clarification.
- User-provided examples are illustrative, and the evaluation corpus will include equivalent paraphrases rather than only exact-string matching.
- Requirements will be linked to concrete implementation references during planning and implementation; those references do not exist yet.

## Resolved Design Decisions

1. Every response includes the five required fields; `clarification_question` is non-empty only when clarification is required.
2. The agent emits JSON actions only; it does not persist reminders or deliver notifications. Reschedule and snooze identify the target by task text and ask for clarification when the match is absent or ambiguous.
3. Explicit time zones in requests take precedence. Otherwise, use the configured user time zone and current clock; if either is unavailable, ask for clarification.
