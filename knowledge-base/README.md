# Knowledge Base System

Persistent IP and business context for AI conversations. This system allows agents to be "refreshed" with your complete IP and socioeconomic impact context without re-explaining everything.

## Structure

```
knowledge-base/
├── ip-context/          # Core IP and business knowledge
│   ├── tech-brief.md    # Arboreum Technology Brief (extracted from PDF)
│   ├── aif-pillars.md   # AIF Pillars (extracted from PDF)
│   └── context.md       # Manually maintained context notes
├── archive/             # Historical versions and reference materials
└── extract_pdfs.py      # Utility to re-extract PDFs when updated
```

## Usage

### Loading Context in Conversations

```bash
# Run AI conversation with knowledge base context
python tools/ai-evaluator/ai_conversation.py \
  --prompt "your question here" \
  --context knowledge-base/ip-context \
  --rounds 10
```

### Refreshing an Agent

The knowledge base is version-controlled. When you update files:

1. Edit `knowledge-base/ip-context/context.md` to add new insights
2. If PDFs updated: `python knowledge-base/extract_pdfs.py`
3. Commit changes: `git add knowledge-base/ && git commit -m "Update IP context"`

Agents automatically load the latest context from these files.

### Appending Context (Without Losing Changes)

All updates are version-controlled via git:

```bash
# Add new insights to context.md
echo "## New Finding\nYour notes here" >> knowledge-base/ip-context/context.md

# Commit the update
git add knowledge-base/ip-context/context.md
git commit -m "Add finding: [brief description]"
```

## Context Files

### tech-brief.md
Extracted from `Arboreum_Tech_Brief.pdf`. Contains:
- US Patent 19/424,106 technical details
- Pyrolyzer technology for ag-waste conversion
- Decentralized manufacturing architecture
- Carbon-negative production process

### aif-pillars.md
Extracted from `Arboreum Impact Foundation (AIF) Pillars.pdf`. Contains:
- 85% profit donation model
- Social mandate funding (reparations, rural sovereignty)
- Impact Foundation (AIF) structure
- Support for historically abandoned communities

### context.md
Manually maintained file for:
- Strategy updates
- Market insights
- Outreach results
- Institutional feedback
- "Dragon King" problem notes

## Remote Desktop / Persistent Agents

Since you want to RDP into your desktop without keeping your laptop open:

1. **Desktop Setup**: Knowledge base is in git, so clone/pull on desktop
2. **Long-running Conversations**: Use `screen` or `tmux` to keep terminal sessions alive
3. **Auto-refresh**: Agents pull latest context on each run from git

```bash
# On desktop: Start long-running agent in screen
screen -S ai-agent
cd d:\Dev\Repos\vcaboara.github.io
python tools/ai-evaluator/ai_conversation.py --context knowledge-base/ip-context

# Detach: Ctrl+A, D
# Reattach from laptop RDP: screen -r ai-agent
```

## Re-extracting PDFs

When you update the source PDFs:

```bash
python knowledge-base/extract_pdfs.py
git add knowledge-base/ip-context/*.md
git commit -m "Update: re-extract PDFs"
```

## Version History

All changes are tracked in git. To see history:

```bash
git log -- knowledge-base/
git diff HEAD~1 knowledge-base/ip-context/context.md
```
