Write-Host "Running schema validation..."
.\schema_validation.ps1

Write-Host "Running property validation..."
.\property_validation.ps1

Write-Host "Running semantic validation..."
.\semantic_validation.ps1

Write-Host "Harness complete."