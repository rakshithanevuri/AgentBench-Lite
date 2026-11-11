$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.\node_modules')) {
    Write-Host 'Frontend packages are missing. Run npm install in the frontend folder first.' -ForegroundColor Yellow
    exit 1
}
npm run dev
