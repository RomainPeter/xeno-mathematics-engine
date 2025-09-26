# ProofEngine demonstration script
Write-Host "=== 🚀 ProofEngine - Demonstration ===" -ForegroundColor Green
Write-Host ""

# LLM connectivity test
Write-Host "1. LLM connectivity test..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1
python -m proofengine.runner.cli ping
Write-Host ""

# Metacognitive plan
Write-Host "2. Metacognitive plan for 'Create a secure logging system'..." -ForegroundColor Yellow
python -m proofengine.runner.cli propose-plan --goal "Create a secure logging system"
Write-Host ""

# Stochastic actions
Write-Host "3. Stochastic actions for 'Implement a rate limiter'..." -ForegroundColor Yellow
python -m proofengine.runner.cli propose-actions --task "Implement a rate limiter" --k 2
Write-Host ""

Write-Host "=== ✅ Demonstration completed ===" -ForegroundColor Green
Write-Host "Your ProofEngine is operational!" -ForegroundColor Cyan
