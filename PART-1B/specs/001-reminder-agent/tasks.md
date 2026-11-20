# Tasks: Natural Language Reminder Agent

**Input**: Design documents from `/specs/001-reminder-agent/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
`quickstart.md`

**Tests**: Required by the feature specification and constitution. Write tests before the
corresponding implementation and verify the tests fail first.

**Organization**: Tasks are grouped by the three approved user stories, ordered by priority:
create (P1), clarification (P1), then reschedule/snooze (P2).

## Format

- Every task uses `- [x]` when complete or `- [ ]` when pending, followed by its ID,
  optional priority/story tags, and description with file path.
- `[P]` appears only where the task can proceed independently in different files.
- User-story phase tasks include `[US1]`, `[US2]`, or `[US3]`.
- Task descriptions include requirement, acceptance-criterion, or evaluation-case IDs.

## Phase 1: Setup

**Purpose**: Initialize the Python package and shared project tooling.

- [x] T001 [P] Create package, test, data, and report directories with `src/reminder_agent/__init__.py`, `tests/unit/`, `tests/contract/`, `tests/property/`, `tests/integration/`, `data/evaluation/`, and `reports/`.
- [x] T002 [P] Create `pyproject.toml` for Python 3.11+ with runtime dependencies `dateparser`, `jsonschema[format-nongpl]`, `tzdata`; dev dependencies `pytest`, `hypothesis`, `pytest-cov`, `ruff`, `mypy`, `bandit`, `pip-audit`, and `detect-secrets`; configure package metadata, checks, and 90% core coverage (NFR-005, NFR-006; AC-006).
- [x] T003 [P] Add `.gitignore` entries for `.venv/`, Python/test/type/lint caches, coverage output, and generated evaluation reports under `reports/` (NFR-004, NFR-007).

## Phase 2: Foundational

**Purpose**: Establish shared models, response/schema validation, output generation, and the
evaluation harness. All user stories depend on this phase.

- [x] T004 [P] Add Draft 2020-12 response contract tests in `tests/contract/test_response_schema.py`, loading `specs/001-reminder-agent/contracts/reminder-response.schema.json`, for the five required fields, valid create/clarification responses, missing/extra/wrong-type fields, conditional clarification rules, and invalid `date-time` values (FR-006, FR-007, NFR-001; AC-001; EV-SCHEMA-*).
- [x] T005 [P] Define typed request, resolution-context, parsed-request, response, evaluation-case, result, and report models in `src/reminder_agent/models.py`; enforce the data-model constraints including 1–4,096 raw request characters, non-empty-after-trim text, aware reference time, and the five required response fields (FR-006, FR-008; AC-001, AC-004).
- [x] T006 [P] Write input/action validation tests in `tests/unit/test_validation.py` for request-size boundaries, missing context, invalid IANA time zones, missing required values, ambiguous reminder targets, and invalid date/time properties (FR-008, FR-009; AC-004; EV-PROP-*).
- [x] T007 [P] Write response-generation tests in `tests/unit/test_output.py` for exact five-field output, empty clarification text on actions, required non-empty question on clarification, and JSON round-trip behavior (FR-006, FR-007; AC-001; EV-SCHEMA-*).
- [x] T008 Implement input/action validation and reusable schema validation in `src/reminder_agent/validation.py`; load the canonical schema from `specs/001-reminder-agent/contracts/reminder-response.schema.json`, use `Draft202012Validator` with an explicit `FormatChecker`, reject over-limit input without truncation, and prevent invalid or ambiguous inputs from yielding actions (FR-007, FR-008, FR-009; AC-001, AC-004; EV-PROP-*).
- [x] T009 Implement the five-field response builder and JSON serialization in `src/reminder_agent/output.py`; validate the response before emission and never append non-JSON prose (FR-006, FR-007; AC-001; EV-SCHEMA-*).
- [x] T010 [P] Write evaluation harness tests in `tests/integration/test_evaluation.py` for JSONL loading, separate schema/property/semantic stages, score calculation, non-zero pass/fail behavior, report metadata, and rejection of datasets with fewer than 15 cases (FR-011, NFR-001–NFR-004; AC-001, AC-004, AC-005; EV-HARNESS-*, EV-REPORT-*).
- [x] T011 [P] Create `data/evaluation/traceability.json` mapping all 19 FR/NFR IDs to acceptance criteria, stable EV/TEST IDs, and planned source paths/symbols from `src/reminder_agent/` (FR-010, NFR-008; AC-005, AC-007; EV-TRACE-*).
- [x] T012 Implement the dataset runner and report generation in `src/reminder_agent/evaluation.py`; load versioned JSONL, run schema/property/semantic checks, report per-case and per-operation metrics with exact denominators, and fail when thresholds or the 15-case minimum are missed (FR-011, NFR-001–NFR-004; AC-001–AC-005; EV-HARNESS-*, EV-REPORT-*).

**Checkpoint**: Shared response contract, validation functions, models, and testable evaluation
runner are in place. No user-story task may bypass schema or input validation.

## Phase 3: User Story 1 — Create a Reminder (Priority: P1)

**Goal**: Extract a task and explicit/relative time from natural-language create requests and
return an actionable JSON response.

**Independent Test**: With a fixed reference time and time zone, run the three supplied
examples and paraphrases. Verify `intent=create`, the task, the correct offset date-time, an
empty clarification question, and schema validity.

- [x] T013 [P] [US1] Write create-intent parser tests in `tests/unit/test_create_parser.py` for “tomorrow at 6 PM”, “next Monday at 10 AM”, “in 30 minutes”, paraphrases, and missing/ambiguous time (FR-001, FR-002; AC-002; EV-CREATE-VALID, EV-CREATE-MISSING-TIME).
- [x] T014 [US1] Add at least 20 create-intent cases to `data/evaluation/v1.jsonl`, each with stable case IDs, requirement IDs, fixed reference context, expected five-field output, and valid/missing/ambiguous/invalid/boundary coverage (FR-001, FR-002; AC-002; EV-CREATE-*).
- [x] T015 [US1] Implement create intent, task extraction, and date/time resolution in `src/reminder_agent/parser.py`; pass a fixed relative base and explicit time zone to `dateparser`, and clarify rather than assume omitted clock times (FR-001, FR-002; AC-002; EV-CREATE-*).
- [x] T016 [US1] Add end-to-end create dataset tests in `tests/integration/test_create_evaluation.py` to run create cases through parsing, property checks, output generation, schema validation, and semantic scoring (FR-002, FR-006, FR-007, FR-011; AC-001, AC-002; EV-CREATE-*, EV-SCHEMA-CREATE).

**Checkpoint**: User Story 1 passes independently and provides the MVP create flow.

## Phase 4: User Story 3 — Clarify Incomplete or Invalid Requests (Priority: P1)

**Goal**: Detect missing, ambiguous, malformed, or invalid information and return a
schema-valid clarification without fabricating a value or producing an action.

**Independent Test**: Submit requests missing task, date/time, or target, plus invalid and
unsupported requests. Verify `intent=clarification`, `needs_clarification=true`, a non-empty
question, no actionable output, and schema validity.

- [x] T017 [P] [US3] Write clarification tests in `tests/unit/test_clarification.py` for missing task/time, absent or ambiguous target, invalid dates, unsupported input, and safe clarification wording (FR-005, FR-009; AC-003, AC-004; EV-CLARIFY-*, EV-INVALID-*).
- [x] T018 [P] [US3] Write Hypothesis properties in `tests/property/test_clarification_properties.py` asserting missing/invalid mandatory values never produce an actionable response and every clarification response satisfies the five-field invariants (FR-005, FR-006, FR-009; AC-003, AC-004; EV-PROP-*, EV-CLARIFY-*).
- [x] T019 [US3] Add at least 20 clarification-result cases to `data/evaluation/v1.jsonl`, covering missing information, ambiguous time/target, malformed input, unsupported intent, and over-limit text (FR-005, FR-008, FR-009; AC-003, AC-004; EV-CLARIFY-*, EV-INVALID-*, EV-PROP-REQUEST-LENGTH).
- [x] T020 [US3] Implement missing/ambiguous/invalid input detection and focused clarification-question generation in `src/reminder_agent/parser.py` and `src/reminder_agent/validation.py`; return no action when mandatory information is unavailable (FR-005, FR-008, FR-009; AC-003, AC-004, AC-008; EV-CLARIFY-*, EV-INVALID-*).
- [x] T021 [US3] Add end-to-end clarification evaluation tests in `tests/integration/test_clarification_evaluation.py` and verify 100% correct clarification on all missing/ambiguous mandatory-field cases (FR-005, FR-011, NFR-003, NFR-007; AC-003, AC-008; EV-CLARIFY-*, EV-INPUT-UNTRUSTED, EV-ERROR-REDACTION).

**Checkpoint**: User Story 3 returns schema-valid clarifications and never fabricates
mandatory values.

## Phase 5: User Story 2 — Reschedule or Snooze a Reminder (Priority: P2)

**Goal**: Identify an existing reminder by supplied task context and produce a replacement
date-time for rescheduling or snoozing.

**Independent Test**: Provide a unique reminder-task context and fixed reference time. Verify
separate reschedule and snooze requests return the correct intent, target task, resulting
date-time, empty clarification question, and schema-valid JSON; ambiguous targets clarify.

- [x] T022 [P] [US2] Write reschedule/snooze tests in `tests/unit/test_reschedule_snooze.py` for unique and ambiguous target matches, replacement times, and relative snooze durations (FR-003, FR-004, FR-005; AC-002, AC-003; EV-RESCHEDULE-*, EV-SNOOZE-*).
- [x] T023 [P] [US2] Add at least 20 reschedule and 20 snooze cases to `data/evaluation/v1.jsonl`, including valid, missing-target, ambiguous-target, invalid-time, duration, and boundary cases with stable IDs and fixed context (FR-003–FR-005; AC-002, AC-003; EV-RESCHEDULE-*, EV-SNOOZE-*).
- [x] T024 [US2] Implement reschedule intent and unique task-target matching in `src/reminder_agent/parser.py`; require an unambiguous replacement time and use clarification for absent or multiple matches (FR-003, FR-005; AC-002, AC-003; EV-RESCHEDULE-*).
- [x] T025 [US2] Implement snooze intent and duration-to-date-time resolution in `src/reminder_agent/parser.py`; calculate relative durations from the fixed aware reference time and configured/requested time zone (FR-004, FR-005; AC-002, AC-003; EV-SNOOZE-*).
- [x] T026 [US2] Add reschedule/snooze end-to-end dataset tests in `tests/integration/test_reschedule_snooze_evaluation.py` and verify per-operation semantic scores meet threshold (FR-003, FR-004, FR-011, NFR-003; AC-002, AC-003; EV-RESCHEDULE-*, EV-SNOOZE-*).

**Checkpoint**: Both change operations pass independently without persistence or notification
side effects.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Enforce complete traceability, privacy/security, documentation, and release gates.

- [x] T027 [P] Write traceability coverage tests in `tests/integration/test_traceability.py` verifying every FR/NFR maps to an evaluation case, test ID, and implementation reference, and the dataset has at least 15 distinct cases (FR-010, FR-011; AC-005; EV-TRACE-COMPLETE, EV-TRACE-MISSING-LINK).
- [x] T028 Implement traceability-manifest checks and requirement coverage reporting in `src/reminder_agent/evaluation.py`; fail on any missing FR/NFR-to-EV/TEST/source link or unmet semantic/schema/property threshold (FR-010, FR-011; AC-005; EV-TRACE-*, EV-HARNESS-THRESHOLD-FAIL).
- [x] T029 Update `specs/001-reminder-agent/quickstart.md` with final pytest, security/quality, dataset evaluation, report, and held-out evaluation commands; document that request content is not included in routine reports (NFR-004, NFR-005, NFR-007, NFR-008; AC-006–AC-008; EV-REPORT-*, EV-LOGGING, EV-DOC-EVAL).
- [x] T030 Run the complete quickstart validation from `specs/001-reminder-agent/quickstart.md`; pass pytest with at least 90% core coverage, all static/security/dependency checks, the full dataset and held-out evaluation thresholds, and confirm the generated report contains no raw reminder text (NFR-001–NFR-008; AC-001–AC-008; EV-SCHEMA-*, EV-PROP-*, EV-SEMANTIC-*, EV-SECURITY-*, EV-TRACE-*).

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001–T003; independent and parallelizable.
- **Foundational (Phase 2)**: Depends on setup. Tests/models can proceed in parallel; validation and output implementations depend on their tests and shared models; the evaluation runner depends on schema, validation, output, runner tests, and traceability data.
- **User Story 1 (Phase 3)**: Depends on Phase 2; delivers the MVP create path.
- **User Story 3 (Phase 4)**: Depends on Phase 2 and the request-dispatch interface introduced by US1; implemented before the P2 change operations so those operations can safely reuse clarification behavior.
- **User Story 2 (Phase 5)**: Depends on Phase 2 and clarification handling from US3; reschedule and snooze implementation tasks are sequential because they extend the shared parser module.
- **Polish (Phase 6)**: Depends on all three user stories and the full versioned dataset.

### Task Dependencies

- T004–T007 and T010–T011 may run in parallel after setup.
- T008 depends on T005 and T006; T009 depends on T004, T005, T007, and T008.
- T012 depends on T008–T011.
- T013 and T014 may be prepared independently; T015 depends on T013 and Phase 2; T016 depends on T014–T015 and the evaluation runner.
- T017–T019 may be prepared independently; T020 depends on T017–T019 and T015; T021 depends on T020 and T012.
- T022 and T023 may be prepared independently; T024 depends on T022–T023 and T020; T025 follows T024; T026 depends on T024–T025 and T012.
- T027 is independent of T028; T028 depends on T027 and all dataset phases; T029 can run in parallel with T027; T030 depends on all prior tasks.

### Parallel Opportunities

- **Setup**: T001, T002, and T003 touch separate paths.
- **Foundation**: T004–T007 and T010–T011 can proceed concurrently; implementation tasks wait for their related tests.
- **US1**: T013 parser tests and T014 dataset authoring can proceed concurrently.
- **US3**: T017 unit tests, T018 property tests, and T019 dataset authoring can proceed concurrently.
- **US2**: T022 tests and T023 dataset authoring can proceed concurrently.
- **Polish**: T027 traceability tests and T029 quickstart documentation can proceed concurrently.
- Do not parallelize tasks that edit the same `data/evaluation/v1.jsonl`, `src/reminder_agent/parser.py`, `src/reminder_agent/validation.py`, or `src/reminder_agent/evaluation.py` file.

## Requirement and Evaluation Traceability

| Work | Requirements | Acceptance criteria | Evaluation case families |
|---|---|---|---|
| Setup and quality configuration (T001–T003) | NFR-005, NFR-006, NFR-007 | AC-006, AC-008 | EV-SECURITY-*, EV-LOGGING |
| Models, schema, validation, and output foundation (T004–T009) | FR-006–FR-009, NFR-001, NFR-002 | AC-001, AC-004 | EV-SCHEMA-*, EV-PROP-*, EV-INVALID-* |
| Evaluation runner and trace map (T010–T012, T027–T028) | FR-010, FR-011, NFR-003, NFR-004 | AC-002, AC-005 | EV-HARNESS-*, EV-REPORT-*, EV-TRACE-*, EV-SEMANTIC-* |
| Create reminder (T013–T016) | FR-001, FR-002 | AC-001, AC-002 | EV-INTENT-CREATE, EV-CREATE-*, EV-SCHEMA-CREATE |
| Clarification and safe rejection (T017–T021) | FR-005, FR-008, FR-009, NFR-007 | AC-003, AC-004, AC-008 | EV-CLARIFY-*, EV-INVALID-*, EV-INPUT-UNTRUSTED, EV-ERROR-REDACTION |
| Reschedule and snooze (T022–T026) | FR-003, FR-004, FR-005 | AC-002, AC-003 | EV-RESCHEDULE-*, EV-SNOOZE-*, EV-CLARIFY-* |
| Documentation and release gates (T029–T030) | NFR-004–NFR-008 | AC-005–AC-008 | EV-REPORT-*, EV-DOC-*, EV-SECURITY-* |

## Suggested MVP

Implement Phase 1, Phase 2, and Phase 3 (US1 create) first. This yields a usable natural
language create-to-JSON path with schema validation and evaluation support. Complete US3
before US2 so both rescheduling and snoozing reuse safe clarification behavior.
