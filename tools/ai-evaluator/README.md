# AI Conversation System

Multi-AI agent conversation tool for evaluating and refining documents through iterative dialogue between agents with different perspectives.

## Quick Start

```bash
# See full documentation
python ai_conversation.py --help

# Or view module docstring
python -c "import sys; sys.path.insert(0, '.'); import ai_conversation; print(ai_conversation.__doc__)"
```

## Essential Files

- **ai_conversation.py** - Main tool (see `--help` and module docstring for complete documentation)
- **GET_API_KEYS.md** - How to get API keys for OpenAI, Gemini, Anthropic
- **CONVERSATION_FLOW.md** - Visual diagram of how agents interact

## Documentation Philosophy

This tool follows the principle: **code documents itself**. Instead of maintaining separate README files that get out of sync, we use:

1. **Comprehensive module docstrings** - Run `python ai_conversation.py --help` or use Python's built-in `help()` function
2. **Rich argparse help** - Detailed `--help` output with examples
3. **Minimal external docs** - Only for setup (GET_API_KEYS.md) or visual aids (CONVERSATION_FLOW.md)

This reduces documentation overhead and ensures information stays current with the code.
