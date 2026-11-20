Write-Host "Running Ruff Lint Checks..."

python -m ruff check src tests
python -m ruff format --check src tests

Write-Host "Lint checks completed."