Write-Host "================================="
Write-Host " SMART TODO HARNESS EXECUTION "
Write-Host "================================="

Write-Host ""
Write-Host "Step 1: Linting"
.\lint.ps1

Write-Host ""
Write-Host "Step 2: Security"
.\security.ps1

Write-Host ""
Write-Host "Step 3: Testing"
.\test.ps1

Write-Host ""
Write-Host "All harness stages completed."