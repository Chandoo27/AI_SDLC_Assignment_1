# Quickstart: Reminder Agent Validation

This guide covers the implemented local validation workflow. The agent runs without a network
service, database, or notification provider. Run commands from the project root.

## Prerequisites

- Python 3.11 or newer
- A virtual environment
- An IANA time-zone database; include the `tzdata` package for platforms such as Windows that
  do not provide one

## Set up the environment

From the project root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The `dev` extra installs the test and quality tools specified in `pyproject.toml`.

## Run tests

Run all unit, contract/schema, property-based, and evaluation integration tests:

```powershell
python -m pytest `
  --cov=reminder_agent.parser `
  --cov=reminder_agent.validation `
  --cov=reminder_agent.output `
  --cov-report=term-missing `
  --cov-fail-under=90
```

The schema tests must validate all five response fields, both response branches, unknown-field
rejection, and RFC 3339 date-time formatting. Property tests must verify response invariants
and that invalid requests cannot produce actionable output.

Run the configured static, dependency, and security checks:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m bandit -r src
python -m pip_audit --skip-editable
detect-secrets scan --all-files src tests data specs pyproject.toml .gitignore
```

`--skip-editable` excludes this local, unpublished package from the PyPI audit while still
auditing its installed dependencies. The explicit scan paths include application code, tests, datasets, specifications, and project
configuration; `--all-files` makes the scan work in workspaces without Git metadata.

## Run the evaluation harness

Run the versioned dataset and write a machine-readable report:

```powershell
python -m reminder_agent.evaluation `
  --dataset data\evaluation\v1.jsonl `
  --report reports\evaluation-v1.json
```

Run the held-out regression corpus separately for the final score:

```powershell
python -m reminder_agent.evaluation `
  --dataset data\evaluation\heldout-v1.jsonl `
  --report reports\heldout-v1.json
```

The development dataset contains 86 cases and the held-out regression dataset contains 20.
The harness reports case-level schema, property, and semantic results; overall and
per-operation scores; schema/dataset versions; and final pass/fail status. It exits non-zero
when a required case is missing, a traceability link is incomplete, or any acceptance
threshold is missed. Reports include safe failure codes, not raw request text.

## Expected acceptance thresholds

- Schema-valid output: 100%.
- Deterministic property-validation cases: 100%.
- Clarification cases: 100% correct, with no fabricated mandatory values.
- Semantic correctness: at least 95% overall and at least 90% for each operation.
- Core parser, validator, and output-generation coverage: at least 90%.
- Required security/quality checks pass with zero unresolved critical/high findings.

Use fixed reference times and IANA time zones in examples and evaluation cases so that
relative-date results are reproducible across machines.
