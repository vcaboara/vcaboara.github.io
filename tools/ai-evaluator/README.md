# AI Tech Brief Evaluator

Automated system for evaluating and refining technology briefs using multi-AI agent collaboration (Gemini, ChatGPT, Claude).

## Quick Start

### 1. Install Dependencies
```bash
pip install -r ai_conversation_requirements.txt
```

### 2. Configure API Keys

Create `.env` file (copy from `.env.example`):
```env
GEMINI_API_KEY=your-key-here       # FREE tier available!
OPENAI_API_KEY=your-key-here       # Optional
ANTHROPIC_API_KEY=your-key-here    # Optional
```

**Get API keys:** See [GET_API_KEYS.md](GET_API_KEYS.md) for step-by-step instructions.

### 3. Run Evaluation
```bash
# See all options and examples
python ai_conversation.py --help

# Quick start with template
python ai_conversation.py --prompt example_tech_brief.md
```

## What It Does

Two AI agents alternate analyzing your tech brief:
- **Agent 1**: Technical evaluation (accuracy, patentability, innovation)
- **Agent 2**: Strategic analysis (market value, IP strategy, positioning)

They iterate until reaching consensus on a refined, patent-ready document.

**See [CONVERSATION_FLOW.md](CONVERSATION_FLOW.md) for detailed flow.**

## Documentation

- **`python ai_conversation.py --help`** - Complete usage guide with examples
- **[GET_API_KEYS.md](GET_API_KEYS.md)** - API key setup instructions
- **[CONVERSATION_FLOW.md](CONVERSATION_FLOW.md)** - How the AI conversation works
- **[example_tech_brief.md](example_tech_brief.md)** - Quick-start template
- **[tech_brief_template.md](tech_brief_template.md)** - Detailed template

## Output

Results saved to `output/` directory:
- `final_document_*.txt` - Refined tech brief
- `transcript_*.txt` - Full conversation
- `conversation_*.json` - Complete data log

## 📄 License

Part of vcaboara.github.io personal site.
