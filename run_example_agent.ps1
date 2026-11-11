$ErrorActionPreference = 'Stop'
if (-not (Test-Path '..\.venv\Scripts\python.exe')) {
    Write-Host 'Run this from the project root after installing dependencies, or use the project venv.' -ForegroundColor Yellow
}
python -m uvicorn examples.http_agent_example:app --host 127.0.0.1 --port 9001 --reload
