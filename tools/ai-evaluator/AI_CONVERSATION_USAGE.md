# AI Conversation Script Usage Guide

## Overview

The `ai_conversation.py` script enables two AI agents to have a conversation, iterating on content until they reach consensus or a maximum number of rounds.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r ai_conversation_requirements.txt
   ```

2. **Set API keys** (at least one required):
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY = "your-openai-key"
   $env:GEMINI_API_KEY = "your-gemini-key"
   $env:ANTHROPIC_API_KEY = "your-anthropic-key"
   
   # Windows CMD
   set OPENAI_API_KEY=your-openai-key
   set GEMINI_API_KEY=your-gemini-key
   set ANTHROPIC_API_KEY=your-anthropic-key
   
   # Git Bash / Linux / Mac
   export OPENAI_API_KEY="your-openai-key"
   export GEMINI_API_KEY="your-gemini-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```
   
   **Getting API Keys:**
   - OpenAI (ChatGPT): https://platform.openai.com/api-keys
   - Google Gemini: https://aistudio.google.com/app/apikey
   - Anthropic (Claude): https://console.anthropic.com/

## Running the Script

Basic usage:
```bash
python ai_conversation.py
```

## Customization

Edit the script to customize:

### Agent Roles
Modify the system prompts for `agent1` and `agent2` to change their personalities:
```python
agent1 = AIAgent(
    name="Your Role Name",
    provider="openai",  # "openai", "gemini", or "anthropic"
    model="gpt-4o",     # "gpt-4o", "gemini-1.5-pro", "claude-3-5-sonnet-20241022"
    system_prompt="Your custom instructions here",
    api_key=YOUR_API_KEY
)
```

**Supported Models:**
- OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Gemini: `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-pro`
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`

### Initial Topic
Change `initial_topic` to discuss any subject:
```python
initial_topic = """
Your custom starting prompt here.
This can be a question, task, or document to refine.
"""
```

### Convergence Settings
Adjust in `ConversationManager`:
```python
manager = ConversationManager(
    agent1=agent1,
    agent2=agent2,
    initial_prompt=initial_topic,
    max_rounds=10,              # Maximum conversation rounds
    convergence_threshold=0.85  # Similarity threshold (0.0-1.0)
)
```

## Output

The script creates an `ai_conversations/` directory with:
- **`conversation_YYYYMMDD_HHMMSS.json`** - Full conversation log (JSON)
- **`final_document_YYYYMMDD_HHMMSS.txt`** - Final agreed document
- **`transcript_YYYYMMDD_HHMMSS.txt`** - Human-readable transcript

## Use Cases

- **Tech brief evaluation**: Evaluate IP and technology for patentability and market value
- **Document refinement**: Start with a draft, let AIs iterate to perfection
- **Debate/discussion**: Give opposing viewpoints and see them converge
- **Code review**: One writes code, one reviews, iterate until clean
- **Content creation**: Collaborative writing with different perspectives
- **Problem solving**: Two AIs approach a problem from different angles

## Example Configurations
Tech Brief Evaluation (Default Configuration)
```python
# ChatGPT evaluates technical aspects
agent1 = AIAgent(name="Technical Evaluator", provider="openai", model="gpt-4o",
    system_prompt="Analyze tech briefs for technical accuracy, innovation, patentability...")

# Gemini evaluates strategic/business aspects  
agent2 = AIAgent(name="Strategic Analyst", provider="gemini", model="gemini-1.5-pro",
    system_prompt="Evaluate IP strategy, market opportunity, competitive advantage...")
```

### 
### Code Review Pair
```python
agent1 = AIAgent(name="Developer", ..., 
    system_prompt="Write clean, efficient code...")
agent2 = AIAgent(name="Reviewer", ...,
    system_prompt="Review code for bugs, style, performance...")
```

### Editor/Proofreader Pair
```python
agent1 = AIAgent(name="Writer", ...,
    system_prompt="Write engaging, creative content...")
agent2 = AIAgent(name="Editor", ...,
    system_prompt="Edit for grammar, clarity, consistency...")
```

### Architect/Engineer Pair
```python
agent1 = AIAgent(name="Architect", ...,
    system_prompt="Design high-level system architecture...")
agent2 = AIAgent(name="Engineer", ...,
    system_prompt="Validate feasibility and suggest implementations...")
```

## Tips

- Start with fewer rounds (5-7) for testing
- More specific system prompts = better results
- The initial prompt should be clear about the desired output
- Agreement phrases help trigger convergence detection
- Review the transcript to understand the discussion flow
