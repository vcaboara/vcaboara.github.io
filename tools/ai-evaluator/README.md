# AI Tech Brief Evaluator

Automated system for evaluating and refining technology briefs using ChatGPT and Gemini AI agents working collaboratively.

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install -r ai_conversation_requirements.txt
```

### 2. Set Up API Keys

**Copy the example file:**
```powershell
Copy-Item .env.example .env
```

**Get your API keys** (see [GET_API_KEYS.md](GET_API_KEYS.md) for detailed instructions):
- **OpenAI (ChatGPT)**: https://platform.openai.com/api-keys
- **Google Gemini**: https://aistudio.google.com/app/apikey (FREE tier available!)

**Edit `.env` and add your keys:**
```env
OPENAI_API_KEY=sk-proj-your-key-here
GEMINI_API_KEY=AIza-your-key-here
```

### 3. Create Your Tech Brief
```powershell
# Copy the template
Copy-Item example_tech_brief.md my_invention.md

# Edit with your invention details
notepad my_invention.md
```

### 4. Run Evaluation
```powershell
python ai_conversation.py --prompt my_invention.md
```

### 5. Get Results
Check the `output/` folder for:
- `final_document_*.txt` - Refined tech brief (ready for hosting/download)
- `transcript_*.txt` - Full conversation showing iteration
- `conversation_*.json` - Complete data log

---

## 📖 How It Works

Two AI agents **alternate** to evaluate and refine your tech brief:

```
Your Brief → ChatGPT (Technical) → Gemini (Strategic) → ChatGPT → Gemini → ...
```

**Agent 1: ChatGPT (GPT-4o)** - Technical Evaluator
- Technical accuracy & innovation assessment
- Patentability analysis
- Prior art concerns
- Implementation feasibility

**Agent 2: Gemini (1.5 Pro)** - Strategic Analyst  
- Market opportunity & business value
- Competitive positioning
- IP strategy & defensibility
- Commercial viability

They iterate until reaching consensus on a comprehensive, patent-ready tech brief.

**See [CONVERSATION_FLOW.md](CONVERSATION_FLOW.md) for detailed flow diagram.**

---

## 💻 Usage

### Basic Usage
```powershell
# Evaluate from file (recommended)
python ai_conversation.py --prompt my_invention.md

# Quick inline evaluation
python ai_conversation.py --prompt "Evaluate: AI-powered XYZ system..."
```

### Advanced Options
```powershell
# More rounds for complex inventions
python ai_conversation.py --prompt complex_invention.md --rounds 20

# Custom output location (e.g., for hosting)
python ai_conversation.py --prompt invention.md --output ../../downloads/evaluations/

# Show help
python ai_conversation.py --help
```

**See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for all commands.**

---

## 📁 File Structure

```
tools/ai-evaluator/
├── ai_conversation.py              # Main script
├── ai_conversation_requirements.txt # Dependencies
├── .env.example                    # API key template
├── .env                           # Your API keys (create this!)
├── example_tech_brief.md          # Example template
├── tech_brief_template.md         # Detailed template
├── README.md                      # This file
├── GET_API_KEYS.md               # How to get API keys
├── QUICK_REFERENCE.md            # Command reference
├── CONVERSATION_FLOW.md          # How the AI conversation works
└── output/                       # Generated evaluations (for hosting)
```

---

## 🎯 Output for Website Hosting

By default, outputs go to `output/` folder. To make them available for download on your site:

```powershell
# Generate evaluation in downloads folder
python ai_conversation.py --prompt invention.md --output ../../downloads/tech-briefs/

# Then link from your HTML:
# <a href="downloads/tech-briefs/final_document_20260428_143022.txt">Download Tech Brief</a>
```

---

## 💰 Cost

**Recommended setup (ChatGPT + Gemini):**
- Gemini: **FREE** (generous daily limits)
- OpenAI: ~$0.02-0.05 per evaluation (or use free credits)

**Per evaluation:** ~$0.02-0.05 (or free with Gemini only)

See [GET_API_KEYS.md](GET_API_KEYS.md) for detailed pricing.

---

## 🔧 Configuration

Edit [ai_conversation.py](ai_conversation.py) to customize:

```python
# Change models
model="gpt-4o-mini"  # Cheaper OpenAI model
model="gemini-1.5-flash"  # Faster Gemini model

# Adjust agent roles
agent1.system_prompt = "Your custom technical evaluator instructions..."
agent2.system_prompt = "Your custom strategic analyst instructions..."
```

---

## 📚 Documentation

- **[GET_API_KEYS.md](GET_API_KEYS.md)** - Step-by-step API key setup
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[CONVERSATION_FLOW.md](CONVERSATION_FLOW.md)** - How the AI conversation works
- **[AI_CONVERSATION_USAGE.md](AI_CONVERSATION_USAGE.md)** - Detailed usage guide

---

## 🛡️ Security

- `.env` file is git-ignored (your keys stay private)
- Never commit API keys to version control
- Set usage limits in provider dashboards

---

## ✅ Verification

Test your setup:
```powershell
# Check API keys are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Keys loaded:', bool(os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')))"

# Run with example
python ai_conversation.py --prompt example_tech_brief.md --rounds 5
```

---

## 🤝 Contributing

This tool is part of [vcaboara.github.io](https://vcaboara.github.io). Generated tech briefs can be hosted in the `downloads/` folder for public access.

---

## 📄 License

Part of vcaboara.github.io personal site.
