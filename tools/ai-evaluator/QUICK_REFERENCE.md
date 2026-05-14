# Quick Command Reference

## Basic Usage

```powershell
# Use a markdown file (RECOMMENDED)
python ai_conversation.py --prompt my_tech_brief.md

# Use a text file
python ai_conversation.py --prompt ideas/invention.txt

# Inline prompt (short descriptions only)
python ai_conversation.py --prompt "Evaluate patent idea: AI-powered XYZ system"
```

## Common Options

```powershell
# Customize number of rounds (default: 10)
python ai_conversation.py --prompt my_brief.md --rounds 15

# Custom output directory
python ai_conversation.py --prompt my_brief.md --output results/project_alpha/

# Combine options
python ai_conversation.py --prompt my_brief.md --rounds 20 --output final_evaluation/
```

## Setup API Keys (One-time)

```powershell
# PowerShell (recommended for Windows)
$env:OPENAI_API_KEY = "sk-proj-..."
$env:GEMINI_API_KEY = "AIza..."

# To make permanent (PowerShell):
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-...', 'User')
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'AIza...', 'User')

# Git Bash / Linux / Mac
export OPENAI_API_KEY="sk-proj-..."
export GEMINI_API_KEY="AIza..."
```

## Output Files

After running, check the output directory (default: `ai_conversations/`):

```
ai_conversations/
├── conversation_20260428_143022.json    # Full data log
├── final_document_20260428_143022.txt   # Ready-to-use result
└── transcript_20260428_143022.txt       # Human-readable conversation
```

## Workflow Examples

### Example 1: Quick Evaluation
```powershell
# 1. Copy template and fill in your idea
copy example_tech_brief.md my_idea.md
notepad my_idea.md

# 2. Run evaluation
python ai_conversation.py --prompt my_idea.md

# 3. Check results
cd ai_conversations
cat final_document_*.txt
```

### Example 2: Deep Analysis
```powershell
# More rounds for complex inventions
python ai_conversation.py --prompt complex_invention.md --rounds 20 --output deep_analysis/
```

### Example 3: Multiple Versions
```powershell
# Evaluate different approaches
python ai_conversation.py --prompt approach_a.md --output evaluation_a/
python ai_conversation.py --prompt approach_b.md --output evaluation_b/
python ai_conversation.py --prompt approach_c.md --output evaluation_c/
```

## Troubleshooting

### "Error: No API keys found"
Set at least one API key (see Setup API Keys above)

### "Error: Required packages not installed"
```powershell
pip install -r ai_conversation_requirements.txt
```

### Want to see what's happening?
The script prints real-time updates as agents converse. Watch for:
- `Round X` - Current iteration
- Agent responses (truncated preview)
- `✓ Convergence detected` - AIs agreed!
- `⚠ Reached maximum rounds` - Didn't fully converge

### Resume or modify?
Edit the last output in `ai_conversations/final_document_*.txt` and run again with that as input:
```powershell
python ai_conversation.py --prompt ai_conversations/final_document_20260428_143022.txt --rounds 5
```

## Help

```powershell
python ai_conversation.py --help
```
