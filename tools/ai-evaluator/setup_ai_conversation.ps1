#Requires -Version 5.1
# Quick setup script for AI Tech Brief Evaluator

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Tech Brief Evaluator - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[1/4] Installing required packages..." -ForegroundColor Yellow
python -m pip install -q -r ai_conversation_requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install packages" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Packages installed (including .env support)" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Setting up .env file..." -ForegroundColor Yellow

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "[WARNING] .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/n)"
    if ($overwrite -ne 'y' -and $overwrite -ne 'Y') {
        Write-Host "[OK] Keeping existing .env" -ForegroundColor Green
    }
    else {
        Copy-Item .env.example .env -Force
        Write-Host "[OK] Created new .env from template" -ForegroundColor Green
    }
}
else {
    Copy-Item .env.example .env
    Write-Host "[OK] Created .env from template" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/4] API Key Configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "Get your FREE API keys from:" -ForegroundColor Cyan
Write-Host "  - OpenAI (ChatGPT): https://platform.openai.com/api-keys"
Write-Host "  - Google Gemini:    https://aistudio.google.com/app/apikey (FREE!)"
Write-Host ""
Write-Host "See GET_API_KEYS.md for detailed step-by-step instructions" -ForegroundColor Gray
Write-Host ""

$setupKeys = Read-Host "Do you want to enter API keys now? (y/n)"

if ($setupKeys -eq 'y' -or $setupKeys -eq 'Y') {
    $openaiKey = Read-Host "Enter OpenAI API key (or press Enter to skip)"
    $geminiKey = Read-Host "Enter Gemini API key (or press Enter to skip)"
    
    if ([string]::IsNullOrWhiteSpace($openaiKey) -and [string]::IsNullOrWhiteSpace($geminiKey)) {
        Write-Host "[WARNING] No keys entered. Edit .env file later to add keys." -ForegroundColor Yellow
    }
    else {
        # Update .env file
        $envContent = Get-Content .env
        if (-not [string]::IsNullOrWhiteSpace($openaiKey)) {
            $envContent = $envContent -replace 'OPENAI_API_KEY=.*', "OPENAI_API_KEY=$openaiKey"
            Write-Host "[OK] OpenAI key saved to .env" -ForegroundColor Green
        }
        if (-not [string]::IsNullOrWhiteSpace($geminiKey)) {
            $envContent = $envContent -replace 'GEMINI_API_KEY=.*', "GEMINI_API_KEY=$geminiKey"
            Write-Host "[OK] Gemini key saved to .env" -ForegroundColor Green
        }
        $envContent | Set-Content .env
    }
}
else {
    Write-Host "[WARNING] Remember to edit .env file and add your API keys!" -ForegroundColor Yellow
    Write-Host "   Edit with: notepad .env" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[4/4] Creating output directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "output" | Out-Null
Write-Host "[OK] Output directory created" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If you didn't enter API keys, edit .env and add them"
Write-Host "2. Fill in example_tech_brief.md with your invention"
Write-Host "3. Run: python ai_conversation.py --prompt example_tech_brief.md"
Write-Host "4. Check output/ folder for results"
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - README.md            - Getting started" -ForegroundColor Gray
Write-Host "  - GET_API_KEYS.md      - How to get API keys" -ForegroundColor Gray
Write-Host "  - python ai_conversation.py --help  - Command reference" -ForegroundColor Gray
Write-Host ""

$viewDocs = Read-Host "Open GET_API_KEYS.md for instructions? (y/n)"
if ($viewDocs -eq 'y' -or $viewDocs -eq 'Y') {
    Start-Process "GET_API_KEYS.md"
}
