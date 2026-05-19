# Start the Business Automation Assistant locally
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

if (-not (Test-Path ".\.env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example — add your API keys before live AI mode."
}

.\.venv\Scripts\streamlit run app.py
