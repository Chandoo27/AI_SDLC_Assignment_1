# Data Model: Natural Language Reminder Agent

## Scope

The agent transforms one natural-language request and its resolution context into one
validated JSON response. It does not persist reminders, send notifications, or mutate
reminder state. Evaluation cases and reports are harness data, not application state.

## Entities

### ReminderRequest

One input request supplied to the agent.

| Field | Type | Constraints |
|---|---|---|
| `text` | string | 1–4,096 raw characters and non-empty after trimming; treated as untrusted text; over-limit input is not truncated |
| `context.reference_time` | timezone-aware datetime or absent | Required to resolve relative dates and durations; must include an offset |
| `context.timezone` | IANA time-zone string or absent | Used when the request does not name a time zone; invalid identifiers are rejected |
| `context.reminder_tasks` | list of strings | Optional task descriptions available for reschedule/snooze target matching |

Input longer than 4,096 characters is rejected safely with a schema-valid clarification response;
the original text is not silently truncated.

### ParsedReminderRequest

An internal, non-public parse result. It preserves the user's intended operation and extracted
values before output validation.

| Field | Type | Constraints |
|---|---|---|
| `intent` | enum | `create`, `reschedule`, `snooze`, or `clarification` |
| `task` | string | Extracted reminder description or matched target task; empty if not known |
| `temporal_expression` | string | Source temporal phrase, retained internally for validation and diagnostics |
| `resolved_datetime` | aware datetime or absent | Must be valid in the selected time zone; absent when unknown |
| `clarification_reason` | enum/string or absent | Missing field, ambiguous target/time, invalid date, or unsupported request |
| `clarification_question` | string | User-facing question when clarification is needed |

The parsed model is internal. It is never serialized directly as the public response.

### ReminderResponse

The only public result. Its JSON representation is validated against
[`reminder-response.schema.json`](./contracts/reminder-response.schema.json).

| Field | Type | Constraints |
|---|---|---|
| `intent` | enum | `create`, `reschedule`, `snooze`, or `clarification` |
| `task` | string | Non-empty for actionable output; empty if unavailable in a clarification |
| `datetime` | string | RFC 3339 date-time with UTC offset for actionable output; empty if unavailable |
| `needs_clarification` | boolean | `true` exactly when action cannot safely be produced |
| `clarification_question` | string | Non-empty when clarification is needed; empty for actionable output |

An actionable response has `needs_clarification: false`, an intent of `create`, `reschedule`,
or `snooze`, a non-empty task, a valid offset date-time, and an empty clarification question.
A clarification response has `intent: "clarification"`, `needs_clarification: true`, and a
non-empty clarification question. It is not an actionable operation.

### EvaluationCase

One versioned dataset row used to assess the complete request-to-response behavior.

| Field | Type | Constraints |
|---|---|---|
| `case_id` | string | Unique and stable, for example `EV-CREATE-VALID-001` |
| `requirement_ids` | list of strings | One or more FR/NFR IDs from the feature specification |
| `operation` | enum | Intended class: `create`, `reschedule`, `snooze`, or `clarification` |
| `category` | enum/string | Case kind, such as valid, missing, ambiguous, boundary, or invalid |
| `request` | string | Natural-language input |
| `context` | object | Fixed reference time, time zone, and candidate reminder tasks for reproducibility |
| `expected` | ReminderResponse | Gold response conforming to the active schema |

Dataset rows are immutable once used in a released evaluation version. Corrections create a
new dataset version and preserve the previous report's reproducibility.

### EvaluationResult and EvaluationReport

An `EvaluationResult` records a case ID, schema-valid flag, property-valid flag,
semantic-correctness flag, pass/fail result, and non-sensitive failure codes. It does not
include raw request text in aggregate output.

An `EvaluationReport` records schema and dataset versions, the command and timestamp used,
case-level results, aggregate metrics, operation-level metrics, threshold values, and the final
pass/fail status. Reports must not expose secrets or include reminder text by default.

## Validation and Relationships

- One `ReminderRequest` produces exactly one `ParsedReminderRequest` and one
  `ReminderResponse`.
- A request with missing/ambiguous mandatory fields produces a clarification response and no
  actionable result.
- When a request is relative, its resolved time is based on the supplied reference time and
  explicit or configured IANA time zone. Missing required context produces clarification.
- For an ambiguous or absent reschedule/snooze target among supplied `reminder_tasks`, the
  response is clarification. The agent does not look up or change persisted reminder records.
- A `ReminderResponse` must pass both semantic/property validation and JSON Schema validation
  before serialization.
- An `EvaluationCase` is executed once per dataset run and yields one `EvaluationResult`.
  Results are grouped into one report; no evaluation record changes reminder state.

## State Transitions

The product has no persisted reminder lifecycle. The request processing lifecycle is:

`received -> parsed -> validated -> response generated -> schema validated -> emitted`

Any invalid or ambiguous branch transitions to a schema-valid clarification response before
emission. A schema-validation failure is a harness/application error and must fail closed; it
must not be converted into a success-shaped response.
