# Push project to https://github.com/Tejashvini-478/chatbot
$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\bin;" + $env:Path
Set-Location $PSScriptRoot

if (-not (Test-Path .git)) {
    git init
    git branch -M main
    git remote add origin https://github.com/Tejashvini-478/chatbot.git
}

Write-Host "Staging files ( .env and .venv are excluded by .gitignore )..."
git add .

$status = git status --porcelain
if ($status) {
    git -c user.name="Tejashvini-478" -c user.email="Tejashvini-478@users.noreply.github.com" `
        commit -m "Update AI business automation assistant"
}

Write-Host "Pushing to GitHub — sign in when the browser opens..."
git push -u origin main

Write-Host "Done: https://github.com/Tejashvini-478/chatbot"
