[CmdletBinding()]
param(
    [string]$Owner = "vcaboara",
    [string]$Repo = "vcaboara.github.io",
    [string]$Branch = "main",
    [int]$RequiredApprovals = 1,
    [switch]$RequireCodeOwnerReviews,
    [switch]$RequireLastPushApproval,
    [string[]]$RequiredStatusChecks
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is not installed or not available in PATH."
}

$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$statusChecks = $null
if ($RequiredStatusChecks -and $RequiredStatusChecks.Count -gt 0) {
    $statusChecks = @{
        strict   = $true
        contexts = $RequiredStatusChecks
    }
}

$payload = @{
    required_status_checks           = $statusChecks
    enforce_admins                   = $true
    required_pull_request_reviews    = @{
        dismiss_stale_reviews           = $true
        require_code_owner_reviews      = [bool]$RequireCodeOwnerReviews
        required_approving_review_count = $RequiredApprovals
        require_last_push_approval      = [bool]$RequireLastPushApproval
    }
    restrictions                     = $null
    required_linear_history          = $true
    allow_force_pushes               = $false
    allow_deletions                  = $false
    block_creations                  = $false
    required_conversation_resolution = $true
    lock_branch                      = $false
    allow_fork_syncing               = $false
}

$tempFile = Join-Path $env:TEMP "gh-branch-protection-$Owner-$Repo-$Branch.json"
$payload | ConvertTo-Json -Depth 10 | Set-Content -Path $tempFile -NoNewline

$endpoint = "repos/$Owner/$Repo/branches/$Branch/protection"
gh api --method PUT -H "Accept: application/vnd.github+json" $endpoint --input $tempFile | Out-Null
$protection = gh api $endpoint | ConvertFrom-Json

Remove-Item -Path $tempFile -ErrorAction SilentlyContinue

[pscustomobject]@{
    Repository                     = "$Owner/$Repo"
    Branch                         = $Branch
    PullRequestReviewsRequired     = $true
    RequiredApprovals              = $protection.required_pull_request_reviews.required_approving_review_count
    DismissStaleReviews            = $protection.required_pull_request_reviews.dismiss_stale_reviews
    EnforceAdmins                  = $protection.enforce_admins.enabled
    LinearHistory                  = $protection.required_linear_history.enabled
    ForcePushesAllowed             = $protection.allow_force_pushes.enabled
    DeletionsAllowed               = $protection.allow_deletions.enabled
    ConversationResolutionRequired = $protection.required_conversation_resolution.enabled
    RequiredStatusChecks           = if ($protection.required_status_checks) { ($protection.required_status_checks.contexts -join ", ") } else { "<none>" }
} | Format-List