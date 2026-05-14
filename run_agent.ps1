#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run AI conversation agent with knowledge base context
.DESCRIPTION
    Wrapper script for running AI conversations that persist across RDP sessions.
    Loads knowledge base context automatically.
.PARAMETER Prompt
    Question or prompt file path
.PARAMETER Rounds
    Maximum conversation rounds (default: 10)
.PARAMETER Output
    Output directory (default: tools/ai-evaluator/output)
.EXAMPLE
    .\run_agent.ps1 -Prompt "Analyze outreach strategy"
.EXAMPLE
    .\run_agent.ps1 -Prompt strategy_review_prompt.md -Rounds 15
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Prompt,
    
    [Parameter(Mandatory=$false)]
    [int]$Rounds = 10,
    
    [Parameter(Mandatory=$false)]
    [string]$Output = "tools/ai-evaluator/output"
)

$ErrorActionPreference = "Stop"

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & .venv\Scripts\Activate.ps1
}

# Run AI conversation with knowledge base
Write-Host "`nRunning AI conversation with knowledge base context..." -ForegroundColor Green
Write-Host "Prompt: $Prompt" -ForegroundColor Yellow
Write-Host "Rounds: $Rounds" -ForegroundColor Yellow
Write-Host "Output: $Output`n" -ForegroundColor Yellow

python tools/ai-evaluator/ai_conversation.py `
    --prompt "$Prompt" `
    --context knowledge-base/ip-context `
    --rounds $Rounds `
    --output "$Output"

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✓ Conversation complete!" -ForegroundColor Green
    
    # Show latest output files
    $outputDir = Get-Item $Output -ErrorAction SilentlyContinue
    if ($outputDir) {
        Write-Host "`nLatest files:" -ForegroundColor Cyan
        Get-ChildItem $outputDir | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -First 3 | 
            ForEach-Object { Write-Host "  - $($_.Name)" }
    }
} else {
    Write-Host "`n✗ Error: Exit code $exitCode" -ForegroundColor Red
}

exit $exitCode
