Write-Host "Running Security Checks..."

python -m bandit -r src
python -m pip_audit

Write-Host "Security checks completed."