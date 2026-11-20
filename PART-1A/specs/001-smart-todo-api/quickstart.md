# Quickstart

## Prerequisites

- Python 3.11 or newer
- A virtual environment
- A writable local JSON file location

## Setup

```powershell
cd PART-1A
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
```

Set `SMART_TODO_DATA_FILE` to a test JSON path before running the server or tests.
The file path is application configuration and is never read from request input. Run one
server worker at a time; JSON mutation locking is process-local.

## Run

```powershell
python -m uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for generated OpenAPI documentation.

## Validation Scenarios

Create a task:

```powershell
$body = @{title="Ship release"; description="Prepare notes"; priority="High"; tags=@("work","release")} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks" -ContentType "application/json" -Body $body
```

Expected: HTTP 201 with a UUID, UTC `createdAt`, `Pending` status, and normalized tags.

Update and retrieve:

```powershell
$body = @{title="Ship release today"} | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri "http://127.0.0.1:8000/tasks/<task-id>" -ContentType "application/json" -Body $body
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks/<task-id>"
```

Expected: HTTP 200; only the supplied editable field changes.

Filter and sort:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks?tags=work,release&sort=priority"
```

Expected: tasks matching at least one tag, ordered High then Medium then Low.

Complete and reopen:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks/<task-id>/complete"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/tasks/<task-id>/reopen"
```

Expected: HTTP 200 with `Completed`, then HTTP 200 with `Pending`.

Delete and verify:

```powershell
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/tasks/<task-id>"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/tasks/<task-id>"
```

Expected: HTTP 204, then HTTP 404 with the stable error shape.

## Automated Checks

```powershell
python -m pytest
ruff check src tests scripts
ruff format --check src tests scripts
bandit -q -r src
pip-audit --skip-editable
python scripts/check_secrets.py
```
