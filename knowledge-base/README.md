# Knowledge Base System

Persistent IP and context storage for AI conversations. Enables agents to remember your patent details, business strategy, and insights across sessions.

## Documentation

See module docstring in `context_loader.py`:

```bash
python -c "import sys; sys.path.insert(0, '.'); import knowledge_base.context_loader as kc; print(kc.__doc__)"
```

Or read the source directly - `context_loader.py` has comprehensive usage examples in its module docstring.

## Structure

```
knowledge-base/
├── ip-context/            Context files (markdown)
│   ├── tech-brief.md      Patent/technology details
│   ├── aif-pillars.md     Impact foundation structure
│   └── context.md         Strategy notes, insights
├── context_loader.py      Loader module (see docstring)
└── extract_pdfs.py        PDF extraction utility
```

## Usage

Most users will access the knowledge base through the AI conversation tool:

```bash
python tools/ai-evaluator/ai_conversation.py \
    --prompt "your question" \
    --context knowledge-base/ip-context
```

The `--context` flag automatically loads all `.md` files and injects them into agent system prompts.

## Philosophy

This system follows **code as documentation** - comprehensive docstrings in `context_loader.py` replace lengthy README files. Documentation lives with the code it describes, stays current, and is accessible via Python's built-in `help()` function.
