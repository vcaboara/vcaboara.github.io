# Quick Reference: Knowledge Base System

## Refresh Agent with Your IP Context

```bash
cd d:\Dev\Repos\vcaboara.github.io

# Run conversation with full IP knowledge pre-loaded
python tools/ai-evaluator/ai_conversation.py \
  --prompt "your question here" \
  --context knowledge-base/ip-context \
  --rounds 10 \
  --output tools/ai-evaluator/output
```

The agent now knows:
- ✓ Arboreum Tech Brief (US 19/424,106)
- ✓ AIF Pillars (85% profit donation model)
- ✓ Current strategy & consensus
- ✓ No need to re-explain!

## Append New Insights (Without Losing Changes)

```bash
# Option 1: Edit directly
notepad knowledge-base/ip-context/context.md

# Option 2: Append from command line
echo "### 2026-05-15: New Finding" >> knowledge-base/ip-context/context.md
echo "Your notes here" >> knowledge-base/ip-context/context.md

# Commit changes
git add knowledge-base/
git commit -m "Add: [your update]"
git push
```

All changes are version-controlled. You can never lose them.

## Update PDFs

When you update the source PDFs:

```bash
# 1. Copy new PDFs to root
# 2. Re-extract
python knowledge-base/extract_pdfs.py

# 3. Commit
git add knowledge-base/ip-context/*.md
git commit -m "Update: re-extract PDFs"
```

## Remote Desktop / Persistent Sessions

To keep agents running while you disconnect:

### On Desktop (via RDP):

```powershell
# Start a persistent PowerShell session
$job = Start-Job -ScriptBlock {
    cd d:\Dev\Repos\vcaboara.github.io
    python tools/ai-evaluator/ai_conversation.py `
        --prompt strategy_review_prompt.md `
        --context knowledge-base/ip-context `
        --rounds 20 `
        --output tools/ai-evaluator/output
}

# Check status
Get-Job
Receive-Job -Id $job.Id -Keep

# When done
Receive-Job -Id $job.Id
Remove-Job -Id $job.Id
```

### Better: Use Windows Task Scheduler

1. Create scheduled task: `Run whether user is logged on or not`
2. Trigger: On demand or schedule
3. Action: `powershell.exe -File d:\Dev\Repos\vcaboara.github.io\run_agent.ps1`

This runs even when RDP disconnected.

## View Knowledge Base

```bash
# See what agents know
ls knowledge-base/ip-context/

# View specific context
cat knowledge-base/ip-context/tech-brief.md
cat knowledge-base/ip-context/context.md
```

## History Tracking

```bash
# See all updates to knowledge base
git log -- knowledge-base/

# Compare versions
git diff HEAD~1 knowledge-base/ip-context/context.md

# Revert to previous version
git checkout HEAD~1 -- knowledge-base/ip-context/context.md
```

---

**Branch**: `feature/knowledge-base-system`  
**Location**: `d:\Dev\Repos\vcaboara.github.io\knowledge-base\`  
**Archived PDFs**: `knowledge-base\archive\` (out of root directory)
