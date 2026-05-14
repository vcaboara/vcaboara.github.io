# VS Code Remote Setup for Laptop → Desktop Workflow

## Why This Approach?

Work from your laptop while using your desktop's resources. Close laptop anytime - desktop keeps running.

## Setup Steps

### 1. Enable Remote Desktop on Desktop PC

```powershell
# On desktop (one-time setup):
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
```

### 2. Install VS Code Remote Extensions on Laptop

In VS Code on laptop:
- Install "Remote - SSH" extension
- OR install "Remote Desktop" extension (if using Windows Remote Desktop)

### 3. Configure SSH (Recommended)

**On Desktop**, enable OpenSSH:
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

**On Laptop**, connect:
1. `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
2. Enter: `your-username@desktop-ip` or `your-username@desktop-hostname`
3. Select "Windows" as platform
4. Open folder: `d:\Dev\Repos\vcaboara.github.io`

### 4. Verify Setup

Once connected:
```bash
# In VS Code terminal (runs on desktop):
pwd  # Should show d:\Dev\Repos\vcaboara.github.io
git status
python --version

# Test agent with knowledge base:
.\run_agent.ps1 -Prompt "Test remote connection" -Rounds 1
```

## Workflow

### Morning: Start from Laptop

```bash
# Connect to desktop via VS Code Remote
# Terminal automatically runs on desktop

# Pull latest knowledge base
git pull

# Run long analysis
.\run_agent.ps1 -Prompt "Analyze market positioning" -Rounds 20
```

### During Day: Close Laptop

- Close laptop lid
- Desktop keeps running
- Agent continues processing

### Evening: Check Results

```bash
# Reconnect from laptop
# Check output
Get-ChildItem tools\ai-evaluator\output\ | Sort-Object LastWriteTime -Descending | Select-Object -First 3

# Read final document
cat tools\ai-evaluator\output\final_document_*.txt | Select-Object -Last 1
```

### Update Knowledge Base

```bash
# Edit context (runs on desktop, editing remote files)
code knowledge-base\ip-context\context.md

# Add your notes
# Save (Ctrl+S) - saves to desktop

# Commit from laptop (commits on desktop)
git add knowledge-base\
git commit -m "Add insight: market feedback"
git push
```

## Benefits

✅ **Laptop Experience**: Familiar VS Code, your keyboard, your setup  
✅ **Desktop Power**: Python, AI agents, processing all on desktop  
✅ **Persistent**: Close laptop, desktop keeps running  
✅ **Copilot Works**: GitHub Copilot works normally in remote session  
✅ **Single Source**: No syncing - you're editing desktop files directly  

## Troubleshooting

**Can't connect via SSH?**
```powershell
# On desktop, check SSH service:
Get-Service sshd
# Should show "Running"

# Check firewall:
Get-NetFirewallRule -Name *ssh* | Select-Object Name, Enabled
```

**Connection slow?**
- Use SSH keys instead of password authentication
- Enable compression in SSH config

**Terminal not working?**
- VS Code may need to download VS Code Server to desktop first time
- Check Windows Defender isn't blocking

## Alternative: Remote Desktop Extension

If SSH doesn't work, use native RDP:
1. Install "Remote Desktop" extension in VS Code
2. Connect using standard RDP (desktop IP)
3. VS Code will automatically open on remote desktop

## Your Specific Workflow

```bash
# On laptop:
# 1. Open VS Code
# 2. Connect to desktop (Remote-SSH)
# 3. Open d:\Dev\Repos\vcaboara.github.io

# Knowledge base automatically available:
python tools\ai-evaluator\ai_conversation.py \
  --prompt "your question" \
  --context knowledge-base\ip-context \
  --rounds 10

# Copilot chat works same as local
# But execution happens on desktop
# Close laptop - desktop continues
```

## This Copilot Session

⚠️ **Note**: This specific Copilot chat conversation won't persist when you reconnect. That's fine because:

- ✓ Your knowledge base persists (in git)
- ✓ AI agents load context from files
- ✓ All commits and code persist
- ✓ You can start new Copilot chat on any machine

The agents don't need "this conversation" - they have **persistent context** via `knowledge-base/ip-context/`.

## Summary

**Recommended Setup**:
1. Use VS Code Remote-SSH from laptop → desktop
2. Knowledge base in git ensures context persists
3. Run agents on desktop, they auto-load IP context
4. Close laptop anytime, desktop keeps working
5. Reconnect later, pull updates, continue

No need to re-explain your IP each time - it's in the knowledge base! 🎉
