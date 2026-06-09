$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Write-Host "No .env file found. Starting with rule-based fallback configuration."
}

D:\python\python.exe -m uvicorn api.server:app --host 127.0.0.1 --port 8000
