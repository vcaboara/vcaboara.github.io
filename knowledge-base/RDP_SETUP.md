# RDP / Remote Desktop Setup Guide

## Problem
You want to run AI agents on your desktop while working from your laptop via RDP, without keeping the laptop constantly connected.

## Solution: Background Jobs & Task Scheduler

### Option 1: PowerShell Background Jobs (Simple)

```powershell
# On desktop via RDP:
cd d:\Dev\Repos\vcaboara.github.io

# Start background job
$job = Start-Job -ScriptBlock {
    Set-Location "d:\Dev\Repos\vcaboara.github.io"
    & .\run_agent.ps1 -Prompt "your question" -Rounds 20
}

# You can now disconnect RDP - job keeps running

# Later, reconnect and check:
Get-Job
Receive-Job -Id $job.Id -Keep  # View output without removing job
Receive-Job -Id $job.Id         # View output and complete job
```

### Option 2: Windows Task Scheduler (Production)

Better for long-running agents that should survive reboots.

#### Setup Steps:

1. **Create Task**:
   ```powershell
   $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File d:\Dev\Repos\vcaboara.github.io\run_agent.ps1 -Prompt 'strategy_review_prompt.md' -Rounds 20"
   
   $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
   
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 4)
   
   Register-ScheduledTask -TaskName "ArboreumAIAgent" -Action $action -Trigger $trigger -Settings $settings -User $env:USERNAME -RunLevel Highest
   ```

2. **Run Task**:
   ```powershell
   Start-ScheduledTask -TaskName "ArboreumAIAgent"
   ```

3. **Check Status**:
   ```powershell
   Get-ScheduledTask -TaskName "ArboreumAIAgent" | Get-ScheduledTaskInfo
   ```

4. **View Logs**:
   ```powershell
   # Check output directory
   Get-ChildItem d:\Dev\Repos\vcaboara.github.io\tools\ai-evaluator\output\ -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5
   ```

### Option 3: Simple Wrapper for Quick Tests

```powershell
# run_persistent.ps1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
    cd d:\Dev\Repos\vcaboara.github.io
    .\run_agent.ps1 -Prompt 'your question' -Rounds 10
}" -WindowStyle Hidden
```

This opens a hidden PowerShell window that persists after RDP disconnect.

## Knowledge Base Sync

Since your knowledge base is git-tracked:

```powershell
# On desktop: Pull latest context
cd d:\Dev\Repos\vcaboara.github.io
git pull origin feature/knowledge-base-system

# Run agent with updated context
.\run_agent.ps1 -Prompt "your question"

# On laptop: Push new insights
cd d:\Dev\Repos\vcaboara.github.io
echo "### New insight" >> knowledge-base\ip-context\context.md
git add knowledge-base\
git commit -m "Add insight: brief description"
git push
```

## Monitoring from Laptop

```powershell
# SSH into desktop (if SSH enabled):
ssh your-desktop
cd d:\Dev\Repos\vcaboara.github.io
Get-Job  # Check background jobs
Get-ScheduledTask -TaskName "ArboreumAIAgent"  # Check scheduled tasks
```

## Best Practice Workflow

1. **Morning**: Pull latest knowledge base
2. **Start Agent**: Schedule long-running analysis
3. **Disconnect RDP**: Laptop can close/sleep
4. **Evening**: Reconnect, check results
5. **Update KB**: Add insights, commit, push
6. **Next Day**: Desktop pulls updates automatically

## Troubleshooting

**Job not found after reconnect?**
- Jobs are per-session. Use Task Scheduler for persistence across logoffs.

**Task fails with permission error?**
- Run Task Scheduler as Administrator
- Set task to "Run whether user is logged on or not"

**Python environment not found?**
- Use full path in scheduled task: `C:\Python\python.exe`
- Or activate venv in script: `& .venv\Scripts\Activate.ps1`
