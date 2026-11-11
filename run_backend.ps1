$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
    Write-Host 'Create the environment and install dependencies first:' -ForegroundColor Yellow
    Write-Host '  python -m venv .venv'
    Write-Host '  .\.venv\Scripts\python.exe -m pip install -e ".[dev]"'
    exit 1
}
& .\.venv\Scripts\python.exe -m uvicorn agentbench_lite.api:app --reload
