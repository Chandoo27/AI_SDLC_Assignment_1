# Research: Natural Language Reminder Agent

**Date**: 2026-11-20

## Decision 1: Use `dateparser` for extracted temporal expressions

**Decision**: Use `dateparser` after the parser layer has isolated the temporal phrase from
the request. Supply a fixed `RELATIVE_BASE` and explicit `TIMEZONE`, request aware datetime
results, and normalize with Python's `zoneinfo`. Do not parse the whole user request as if it
were only a date.

**Rationale**: The official documentation covers relative expressions, weekday expressions,
more than 200 locales, timezone settings, and a `RELATIVE_BASE` setting for reproducibility.
It can support the supplied examples without adding a remote service. The same documentation
warns that `search_dates()` support is limited; controlled extraction followed by parsing is
safer than searching arbitrary text for date-like substrings.

`dateparser` also makes assumptions for incomplete dates (for example, preferring the current
day/month by default). Those assumptions can fabricate a required value. Configure strict
handling for incomplete absolute dates, and explicitly detect whether the request supplied
the mandatory clock time; relative expressions such as “tomorrow” can otherwise parse to
midnight even when the user omitted a time. Do not apply incomplete-date settings globally in
a way that rejects valid relative expressions. If the request or parser result does not
establish every required value, generate clarification rather than accepting a default. Treat
ambiguous numeric dates and timezone abbreviations as unclear unless locale/offset context
removes ambiguity.

**Alternatives considered**:

- A custom regular-expression parser with only Python standard-library date types would avoid
  a runtime dependency, but would require implementing and maintaining relative-date and
  locale behavior. Keep only operation/task boundary extraction as explicit local patterns.
- A general-purpose NLP model or hosted language-model call would add model, privacy,
  availability, and nondeterminism concerns that are unnecessary for this local MVP.

**Time-zone handling**: Python `zoneinfo` uses the system IANA database and can fall back to
the first-party `tzdata` package; the Python docs specifically recommend declaring `tzdata`
for cross-platform projects because Windows commonly lacks a system IANA database. Use
`zoneinfo` and round-trip/offset checks for nonexistent or repeated local times rather than
assuming that attaching a time zone alone resolves DST ambiguity.

## Decision 2: Use `jsonschema` Draft 2020-12 validation

**Decision**: Use `jsonschema.validators.Draft202012Validator` for the canonical output
contract. Install the `format-nongpl` extra, call `check_schema()` in a contract test/startup
check, reuse the validator for responses, and pass an explicit `FormatChecker` so the schema's
`date-time` format is validated rather than treated as annotation only.

**Rationale**: The project's schema uses conditionals and targets Draft 2020-12. The
`jsonschema` documentation provides draft-specific validators and schema checking. It states
that format checks are not performed unless a format checker is supplied, and that optional
extras provide dependencies for format validation. The non-GPL extra supplies format-related
dependencies without adding unrelated GPL format packages. Reusing a constructed validator
avoids rechecking a known schema for every response.

**Alternatives considered**:

- Hand-written field checks are insufficient as the contract changes and would duplicate
  JSON Schema semantics.
- A different JSON Schema implementation would add a second behavior source without a
  requirement for it.

## Decision 3: Use `pytest` with Hypothesis for deterministic and generated tests

**Decision**: Use pytest for the suite and integrate Hypothesis tests as ordinary pytest
tests for property invariants. Use the independent dataset runner for semantic scoring; do
not treat property-based tests as a substitute for curated semantic cases.

**Rationale**: Hypothesis documents direct use with pytest and generated strategies, which
fits boundary and cross-field response properties. Its current PyPI metadata declares Python
3.11 or newer, consistent with the selected minimum. Keep the environment locked for
reproducibility.

**Alternatives considered**:

- Hand-authored boundary tests alone may miss combinations of invalid field values.
- A separate property-test runner is unnecessary because Hypothesis runs under pytest.

## Decision 4: Keep evaluation local, versioned, and deterministic

**Decision**: Store evaluation cases as versioned JSONL. Every case includes a stable case
ID, requirement IDs, natural-language input, fixed resolution context, and expected
five-field response. Score schema, deterministic property, semantic, per-operation, and
traceability results separately; emit a JSON report and a non-zero process status on failure.

**Rationale**: Fixed reference time, time zone, and candidate-reminder context avoid
environment-dependent expectations. A dataset makes semantic behavior measurable and
reproducible without network calls or a model. Immutable dataset versions allow prior
reports to be reproduced.

**Alternatives considered**:

- A live external model benchmark would introduce nondeterminism and a network dependency.
- A single aggregate accuracy score could conceal schema failures or poor performance on an
  individual action, so the harness reports separate gates.

## Dependency and compatibility notes

- Runtime: `dateparser`, `jsonschema[format-nongpl]`, and `tzdata`.
- Development/quality: `pytest`, `hypothesis`, `pytest-cov`, `ruff`, `mypy`, `bandit`,
  `pip-audit`, and `detect-secrets`.
- Pin a tested environment in the implementation dependency lock; do not assume a package's
  current latest release remains compatible without running the project checks.
- `dateparser`'s GitHub repository identifies its license as BSD-3-Clause. Hypothesis's PyPI
  metadata identifies MPL-2.0. Recheck all selected dependency licenses and advisories as part
  of dependency review before release.

## Sources

- dateparser documentation, features and usage:
  <https://dateparser.readthedocs.io/en/latest/index.html>
- dateparser settings, including `TIMEZONE`, `RETURN_AS_TIMEZONE_AWARE`,
  `RELATIVE_BASE`, strict/incomplete parsing, and `search_dates()` limitations:
  <https://dateparser.readthedocs.io/en/latest/settings.html>
- dateparser project repository and BSD-3-Clause license declaration:
  <https://github.com/scrapinghub/dateparser>
- `jsonschema` schema validation and validator reuse:
  <https://python-jsonschema.readthedocs.io/en/stable/validate/>
- `jsonschema` optional format extras:
  <https://python-jsonschema.readthedocs.io/en/stable/#extras>
- `jsonschema` validator API and explicit format checker:
  <https://python-jsonschema.readthedocs.io/en/stable/api/jsonschema/validators/>
- Hypothesis quickstart and pytest integration:
  <https://hypothesis.readthedocs.io/en/latest/quickstart.html>
- Hypothesis PyPI metadata, Python minimum, and license:
  <https://pypi.org/project/hypothesis/>
- Python `zoneinfo`, IANA time-zone sources, Windows/tzdata guidance, and DST `fold` behavior:
  <https://docs.python.org/3/library/zoneinfo.html>
