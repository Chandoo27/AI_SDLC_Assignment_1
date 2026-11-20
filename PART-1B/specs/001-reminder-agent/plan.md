# Implementation Plan: Natural Language Reminder Agent

**Branch**: `001-reminder-agent` | **Date**: 2026-11-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-reminder-agent/spec.md` and the planning
constraints supplied on 2026-11-20.

## Summary

Build a small Python request-to-JSON agent with four explicit layers: natural-language
parsing, input/action validation, response generation, and a dataset-driven evaluation
harness. Use deterministic parsing with an explicit reference time and IANA time zone; do not
add an LLM, database, network service, or notification delivery. Validate every five-field
response against the versioned Draft 2020-12 JSON Schema. A reproducible JSONL evaluation run
reports schema, property, semantic, and traceability results against the constitution's
thresholds.

## Technical Context

**Language/Version**: Python 3.11 or newer.

**Primary Dependencies**: `dateparser` for natural-language date/time expressions;
`jsonschema[format-nongpl]` for Draft 2020-12 response validation with date-time format
support; `tzdata` for portable IANA time-zone data, including Windows.

**Storage**: None for application reminders. Evaluation input is versioned JSONL and reports
are generated JSON; no user reminder state is persisted.

**Testing**: `pytest`, `hypothesis`, and `pytest-cov`; require at least 90% line coverage of
core parsing, validation, and response generation.

**Target Platform**: Local Python CLI/library on Windows, Linux, and macOS. No hosted service
or external model is required.

**Project Type**: Single Python package with a small CLI entry point and evaluation runner.

**Performance Goals**: No response-latency or throughput target is specified. The local
evaluation runner must complete the versioned test dataset as one reproducible command;
runtime is reported but is not an acceptance threshold.

**Constraints**: Exactly one JSON response object per request; five required fields; schema
validation before emission; no reminder persistence or notification side effects; no
fabricated required values; request text is limited to 4,096 characters and is never silently
truncated; all temporal tests use fixed reference times and time zones.

**Scale/Scope**: One request is processed independently. The development corpus contains 86
curated cases across create, reschedule, snooze, and clarification; a separate 20-case
held-out corpus covers regression behavior. Both include temporal boundaries and invalid-input
coverage. The agent does not manage a reminder database.

## Constitution Check

| Principle or gate | Plan decision | Status |
|---|---|---|
| Natural-language intent and safe clarification | Parser returns a clarification response if mandatory information, time context, or a unique target cannot be established. | PASS |
| Schema-first JSON contract | One Draft 2020-12 schema defines the five required fields, conditional clarification behavior, valid intents, and RFC 3339 date-time output. | PASS |
| Validate before acting | Validate request length/context, parsed values, cross-field invariants, and final serialized response. The agent emits no state mutation. | PASS |
| Evaluation-driven quality | Versioned dataset and runner measure schema, property, semantic, per-operation, and traceability results; thresholds fail the run. | PASS |
| Traceable simplicity | Each FR/NFR retains its stable evaluation and test IDs; concrete module references are assigned during implementation. No LLM, DB, service framework, or unrelated features are added. | PASS |
| Security, tests, and docs | Input is untrusted; request text is omitted from routine reports; secret/dependency/static checks and the required test categories are included. | PASS |

No constitution violations or complexity exceptions are proposed. Recheck all gates after
contracts and evaluation design are complete.

## Architecture

```text
Natural-language request + resolution context
                    |
                    v
1. Parser layer -> internal parsed request
                    |
                    v
2. Validation layer -> validated action or clarification
                    |
                    v
3. Output generation layer -> five-field JSON object
                    |
                    v
          Draft 2020-12 schema validation
                    |
                    v
              JSON response

Versioned JSONL dataset -> 4. Evaluation harness -> case results, scores, pass/fail report
```

1. **Parser** classifies create/reschedule/snooze intent, separates task/target text from
   temporal expressions, and resolves dates relative to the supplied reference time. Keep
   operation patterns explicit and bounded; delegate date-expression interpretation to the
   selected parser library with a fixed relative base and explicit time zone. Do not accept
   parser defaults for omitted clock times or select an arbitrary target when context provides
   multiple matches.
2. **Validation** enforces the 4,096-character input limit, supported intent, task/time
   presence, supplied IANA zone validity, future/valid date-time behavior, target uniqueness,
   and cross-field rules. Missing or ambiguous data becomes a clarification decision, not a
   guessed action.
3. **Output generation** maps internal results to exactly `intent`, `task`, `datetime`,
   `needs_clarification`, and `clarification_question`. Use empty strings for unavailable
   task/date values and for the question on actionable responses. Validate the response with
   the shared schema and a date-time `FormatChecker` before JSON serialization; never emit
   prose around it.
4. **Evaluation harness** loads immutable versioned JSONL cases, calls the same public request
   pipeline, applies schema/property/semantic checks, verifies requirement coverage, reports
   aggregate and per-operation scores, and exits non-zero on any failed gate.

The request engine orchestrates parsing, validation, and response generation behind a pure
request/context-to-response function. The package also provides a one-request JSON CLI and a
separate dataset-evaluation CLI; there is no reminder storage or delivery adapter in this
feature.

## Evaluation Strategy

Each result records `case_id`, requirement IDs, schema validity, property validity, semantic
correctness, pass/fail, and non-sensitive failure codes. The report records schema and dataset
versions, command, per-case results, aggregate and per-operation metrics, threshold values,
and final status.

- **Schema**: parse exactly one JSON object and validate every output against the active
  Draft 2020-12 schema with format checking enabled.
- **Property**: check field types, allowed intent values, clarification invariants, required
  task/date for actions, date/time offset validity, input-length bounds, and that invalid
  inputs cannot yield actions or mutate state.
- **Semantic**: compare extracted intent, task/target, and normalized time to the gold
  expected response under the case's fixed reference context. Clarification cases must ask
  for the expected missing/ambiguous information and must not invent it.
- **Per-operation metrics**: group by `EvaluationCase.operation` (the user's intended
  operation), so a clarification failure is still counted against its create/reschedule/
  snooze journey when applicable.
- **Traceability**: require every FR/NFR to appear in at least one dataset case, one test ID,
  and one implementation reference before implementation acceptance.
- **Scoring**: report valid/total counts and percentages; do not round a value up to pass.
  An empty required category is a failure, not a 100% score.

Thresholds are inherited from the constitution and spec: 100% schema validity, 100% on
deterministic property cases, 100% correct clarification on missing/ambiguous mandatory
information, at least 95% semantic correctness overall, at least 90% for each supported
operation, at least 90% core line coverage, all required security/quality checks passing, and
zero unresolved critical/high security findings.

## Dataset Strategy

Keep the development corpus at `data/evaluation/v1.jsonl`, one JSON object per line. Each row has a
stable `case_id`, `requirement_ids`, intended `operation`, `category`, `request`, fixed
`context` (`reference_time`, `timezone`, and available reminder task candidates), and an
expected five-field response. Use paraphrases for equivalent intent; do not rely on exact
example wording alone.

The implemented corpus contains 86 development cases: at least 20 for each intended operation
(`create`, `reschedule`, `snooze`, and `clarification`), plus 20 held-out cases in
`data/evaluation/heldout-v1.jsonl`. For each actionable operation,
include valid, missing-field, ambiguous, invalid, and boundary cases. Clarification cases
cover missing information, ambiguous target/time, invalid input, and unsupported requests.
Required case families include:

- The three supplied examples and paraphrases, with fixed reference time and time zone.
- Create, reschedule, and snooze requests with missing task, time, or target.
- Multiple or unmatched candidate tasks, explicit time zones, relative dates across midnight
  and week boundaries, and snooze durations.
- Invalid calendar dates, past times, DST gaps/overlaps, empty/overlong text, malformed
  requests, and unsupported intent.
- Every stable `EV-*` family in the feature specification's traceability table.

Keep evaluation data free of personal reminder content. Treat released dataset versions as
immutable; publish corrections as a new version. Maintain a development corpus for parser
iteration and a held-out regression corpus for final score reporting so tuning does not only
fit the examples used during development. Reports identify the exact dataset version.

## Validation Strategy

- Validate raw request text as non-empty and at most 4,096 characters; reject rather than
  truncate invalid input.
- Require an aware reference datetime when relative expressions need it. Resolve explicit
  request time zones first, otherwise use the configured IANA time zone. If needed context is
  absent or invalid, ask a schema-conforming clarification.
- Use timezone-aware datetimes throughout parsing and normalization. Do not silently normalize
  invalid calendar dates, past times, or DST-ambiguous/nonexistent local times.
- Confirm that a clock time was actually supplied; a parser's default midnight is not a
  user-provided time. Treat ambiguous numeric dates and timezone abbreviations as unclear
  unless locale/offset context resolves them.
- Require a unique target task from the supplied reminder context for reschedule/snooze; a
  missing or ambiguous match is a clarification.
- Validate the final response object with the canonical response schema and `FormatChecker`.
  A schema failure is a processing/test failure; it must never be disguised as a successful
  response.
- Avoid logging raw natural-language request text. Expose stable error codes and safe
  clarification messages rather than tracebacks or internal details.

## Test Strategy

- **Unit (`tests/unit/`)**: parser intent/task/time extraction with fixed clocks; validation
  boundaries, missing information, time zones, and target matching; output field mapping.
- **Contract (`tests/contract/`)**: load and check the schema itself; validate examples for
  every response kind; reject missing/extra fields, wrong types, inconsistent clarification
  flags, and invalid date-times.
- **Property (`tests/property/`)**: use Hypothesis to exercise response invariants, request
  length boundaries, and generated invalid combinations; assert invalid inputs never produce
  actionable output.
- **Evaluation integration (`tests/integration/`)**: run the versioned JSONL corpus through the
  public pipeline and verify the report, all required categories, trace links, and threshold
  failure behavior.
- **Coverage**: enforce at least 90% line coverage on core parser, validation, and output
  generation modules. Do not use coverage to excuse missing semantic cases.
- **Quality/security**: run Ruff lint/format checks, mypy type checks, Bandit, pip-audit, and a
  secret scan. All required checks pass; no unresolved critical/high findings.

## Dependency List

Runtime:

- `dateparser` — parse supported natural-language date and time expressions relative to a
  supplied reference time.
- `jsonschema[format-nongpl]` — validate output against JSON Schema Draft 2020-12 and enable
  optional `date-time` format dependencies.
- `tzdata` — provide IANA time-zone data on platforms without a system database.

Development and quality:

- `pytest` — unit, contract, and integration tests.
- `hypothesis` — property-based validation tests.
- `pytest-cov` — enforce core coverage.
- `ruff` — lint and format.
- `mypy` — static type checking.
- `types-dateparser` and `types-jsonschema` — third-party type information for mypy.
- `bandit` — Python security static analysis.
- `pip-audit` — dependency vulnerability audit.
- `detect-secrets` — automated secret scanning.

Declare compatible Python 3.11+ dependency ranges in `pyproject.toml`. No web framework,
database, network client, or LLM package is required.

## Requirement Traceability Plan

Use the stable FR/NFR, EV, and TEST IDs already defined in
[`spec.md`](./spec.md#requirement-to-evaluation-traceability). The implementation-area column
maps to concrete source files/symbols in the evaluation coverage manifest. A trace check fails
if a requirement has no evaluation case, test ID, or implementation reference. The dataset
itself carries requirement IDs, and report generation includes a requirement coverage summary.

## Acceptance Threshold Strategy

Acceptance is conjunctive; a high semantic score cannot compensate for a failed schema,
property, clarification, test, security, or traceability gate.

| Gate | Required result |
|---|---:|
| Schema-valid outputs | 100% |
| Deterministic property cases | 100% |
| Missing/ambiguous mandatory-field clarification | 100% |
| Semantic correctness, all cases | At least 95% |
| Semantic correctness, each operation | At least 90% |
| Core decision/validation/output coverage | At least 90% |
| Required automated quality/security checks | All pass |
| Unresolved critical/high security findings | 0 |
| Requirement-to-case/test/implementation links | 100% |

The harness exits successfully only when every applicable threshold and required dataset
category is present and passing. Record exact counts, denominators, and versions; percentages
are not rounded to meet a threshold.

## Project Structure

### Documentation (this feature)

```text
specs/001-reminder-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── reminder-response.schema.json
└── tasks.md                         # Created by /speckit-tasks
```

### Source Code

```text
pyproject.toml
src/
└── reminder_agent/
    ├── __init__.py
    ├── __main__.py
    ├── engine.py
    ├── main.py
    ├── models.py
    ├── parser.py
    ├── validation.py
    ├── output.py
    └── evaluation.py
data/
└── evaluation/
    ├── v1.jsonl
    └── heldout-v1.jsonl
tests/
├── unit/
├── contract/
├── property/
└── integration/
reports/                              # Generated, not committed
```

**Structure Decision**: One `src/` package keeps the four mandated layers easy to isolate and
test. The evaluation harness is a separate module but calls the same public processing
function. The feature contract under `specs/001-reminder-agent/contracts/` is the canonical
schema; no second schema copy is introduced. Storage, HTTP APIs, and integrations are excluded.

## Complexity Tracking

No constitution violations or additional project layers require justification.
