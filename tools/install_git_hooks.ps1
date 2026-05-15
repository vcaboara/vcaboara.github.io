[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if (-not (Test-Path ".git")) {
    throw "No .git directory found at $repoRoot"
}

$hooksPath = ".githooks"
if (-not (Test-Path $hooksPath)) {
    throw "Expected hooks folder '$hooksPath' was not found"
}

git config core.hooksPath $hooksPath

$configured = git config --get core.hooksPath
if ($configured -ne $hooksPath) {
    throw "Failed to configure core.hooksPath. Current value: '$configured'"
}

Write-Host "Configured git hooks path: $configured"
Write-Host "Installed hooks:"
Get-ChildItem -Path $hooksPath -File | Select-Object -ExpandProperty Name
