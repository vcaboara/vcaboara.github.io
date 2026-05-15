# AI Tech Brief Evaluator

Automated system for evaluating and refining technology briefs using ChatGPT and Gemini AI agents working together.

## Quick Start

### Option 1: Use a File for Your Tech Brief (Recommended)

1. Copy `example_tech_brief.md` and fill in your invention details
2. Run with your file:
   ```powershell
   python ai_conversation.py --prompt my_invention.md
   ```

### Option 2: Provide Prompt Directly

```powershell
python ai_conversation.py --prompt "Evaluate this invention: [your description here]"
```

### Option 3: Automated Setup Scripts

**Windows Command Prompt:**
```cmd
setup_ai_conversation.bat
```

**Windows PowerShell:**
```powershell
.\setup_ai_conversation.ps1
```

1. **Install dependencies:**
   ```bash
   pip install -r ai_conversation_requirements.txt
   ```

2. **Set API keys:**
   ```powershell
   # PowerShell
   $env:OPENAI_API_KEY = "sk-..." 
   $env:GEMINI_API_KEY = "AI..."
   ```

3. **Create your tech brief file** (or use [example_tech_brief.md](example_tech_brief.md))

4. **Run with your file:**
   ```bash
   python ai_conversation.py --prompt your_brief.md
   ```

### Command Line Usage

The script uses an **alternating conversation model**:

1. **You provide** the initial tech brief (via file or command line)
2. **Agent 1 (Technical Evaluator)** receives it first and provides technical evaluation
3. **Agent 2 (Strategic Analyst)** receives Agent 1's response and adds strategic feedback
4. **Agent 1** receives Agent 2's feedback and refines the brief
5. **Agent 2** reviews the refinement
6. **Continues alternating** until they agree (convergence) or reach max rounds

**Command Line Examples:**
```powershell
# Use a file
python ai_conversation.py --prompt my_brief.md

# Use inline text
python ai_conversation.py --prompt "Evaluate this tech..."

# Customize rounds and output location
python ai_conversation.py --prompt my_brief.md --rounds 15 --output results/

# Show help
python ai_conversation.py --help
```

## How It Works

Two AI agents collaborate to evaluate and refine your tech brief:

- **Agent 1 (ChatGPT/GPT-4o)** - Technical Evaluator
  - Analyzes technical accuracy and innovation
  - Assesses patentability and prior art concerns
  - Evaluates implementation feasibility

- **Agent 2 (Gemini 1.5 Pro)** - Strategic Analyst  
  - Reviews market opportunity and business value
  - Evaluates competitive positioning
  - Assesses IP strategy and defensibility

They iterate back and forth until reaching consensus on a refined, comprehensive tech brief.

## Your Tech Brief Template

Use [tech_brief_template.md](tech_brief_template.md) as your starting point. It includes:

- Problem statement
- Technical solution
- Key features & advantages
- Market applications
- IP strategy considerations
- Differentiation analysis

## Output Files

After running, check the `ai_conversations/` folder for:

- **`final_document_*.txt`** - Refined tech brief ready for IP filing
- **`transcript_*.txt`** - Full conversation showing the iteration process
- **`conversation_*.json`** - Complete data log

## Configuration

Edit `ai_conversation.py` to customize:

```python
# Adjust max rounds (default: 10)
max_rounds=10

# Adjust convergence threshold (0.0-1.0, default: 0.85)
convergence_threshold=0.85

# Change agent roles/prompts
agent1.system_prompt = "Your custom instructions..."
```

## API Keys

Get your free API keys:
- **OpenAI (ChatGPT):** https://platform.openai.com/api-keys
- **Google Gemini:** https://aistudio.google.com/app/apikey

Both offer free tiers suitable for tech brief evaluation.

## Tips for Best Results

1. **Be specific** - More detail in your initial brief = better evaluation
2. **Include prior art** - Mention any similar technologies you know about
3. **Quantify value** - Include market size, cost savings, or performance improvements
4. **Define the problem clearly** - Explain why current solutions are insufficient
5. **Review the transcript** - The iteration process often reveals valuable insights

## Support

For detailed usage info, see [AI_CONVERSATION_USAGE.md](AI_CONVERSATION_USAGE.md)
