# ✅ Setup Complete!

All files have been organized into `tools/ai-evaluator/` subfolder.

## 📁 Folder Structure

```
tools/ai-evaluator/
├── 📄 ai_conversation.py              # Main script
├── 📄 ai_conversation_requirements.txt # Python dependencies  
├── 📄 .env.example                    # API key template
├── 📄 .gitignore                      # Keeps .env private
├── 📄 example_tech_brief.md          # Quick start template
├── 📄 tech_brief_template.md         # Detailed template
├── 📄 setup_ai_conversation.ps1      # Automated setup (PowerShell)
├── 📄 setup_ai_conversation.bat      # Automated setup (CMD)
├── 📘 README.md                      # Main documentation
├── 📘 GET_API_KEYS.md               # How to get API keys (detailed!)
├── 📘 QUICK_REFERENCE.md            # Command cheat sheet
├── 📘 AI_CONVERSATION_USAGE.md      # Advanced usage
├── 📘 CONVERSATION_FLOW.md          # How AI conversation works
└── 📁 output/                        # Generated tech briefs (for hosting)
```

---

## 🚀 Quick Start (3 Steps!)

### Step 1: Run Setup Script

```powershell
cd tools\ai-evaluator
.\setup_ai_conversation.ps1
```

**This will:**
- ✅ Install Python packages (including .env support)
- ✅ Create `.env` file from template
- ✅ Prompt you to enter API keys (optional - can do later)
- ✅ Create output directory

### Step 2: Get API Keys

**Option A: Enter during setup** (recommended)
- Setup script will prompt you

**Option B: Edit `.env` file manually**
```powershell
notepad .env
```

**Where to get keys:**
- **OpenAI (ChatGPT)**: https://platform.openai.com/api-keys
- **Gemini (Google)**: https://aistudio.google.com/app/apikey ⭐ **FREE tier!**

**See [GET_API_KEYS.md](GET_API_KEYS.md) for step-by-step instructions with screenshots!**

### Step 3: Run Your First Evaluation

```powershell
# Edit the example with your invention
notepad example_tech_brief.md

# Run evaluation
python ai_conversation.py --prompt example_tech_brief.md

# Check results
cd output
cat final_document_*.txt
```

---

## ✨ Key Features

### ✅ .env File Support (No More Manual Key Entry!)

Your API keys are loaded automatically from `.env` file:

```env
# tools/ai-evaluator/.env
OPENAI_API_KEY=sk-proj-your-key-here
GEMINI_API_KEY=AIza-your-key-here
```

**Benefits:**
- ✅ Set once, use forever
- ✅ No need to export keys each terminal session
- ✅ Automatically git-ignored (secure)
- ✅ Easy to update

### ✅ Output for Website Hosting

Generated files go to `output/` folder by default:

```
output/
├── final_document_20260428_143022.txt
├── transcript_20260428_143022.txt
└── conversation_20260428_143022.json
```

**To host on your website:**
```powershell
# Option 1: Copy to downloads folder
Copy-Item output\final_document_*.txt ..\..\downloads\

# Option 2: Generate directly to downloads
python ai_conversation.py --prompt my_brief.md --output ../../downloads/tech-briefs/
```

Then link from HTML:
```html
<a href="downloads/tech-briefs/final_document_20260428_143022.txt" download>
  Download Tech Brief
</a>
```

### ✅ Alternating AI Conversation

1. **You** provide initial tech brief
2. **ChatGPT** analyzes technical aspects
3. **Gemini** adds strategic perspective
4. **ChatGPT** refines based on feedback
5. **Gemini** reviews refinement
6. Repeat until consensus!

---

## 📚 Documentation Files

| File                         | Purpose                                           |
| ---------------------------- | ------------------------------------------------- |
| **README.md**                | Main getting started guide                        |
| **GET_API_KEYS.md**          | Step-by-step API key instructions (⭐ start here!) |
| **QUICK_REFERENCE.md**       | Command cheat sheet                               |
| **CONVERSATION_FLOW.md**     | Visual diagram of AI interaction                  |
| **AI_CONVERSATION_USAGE.md** | Advanced configuration                            |

---

## 💡 Common Commands

```powershell
# Basic evaluation
python ai_conversation.py --prompt my_invention.md

# More rounds for complex inventions
python ai_conversation.py --prompt complex.md --rounds 20

# Output to specific location
python ai_conversation.py --prompt brief.md --output ../../downloads/

# View help
python ai_conversation.py --help

# Check if API keys are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING'); print('Gemini:', 'SET' if os.getenv('GEMINI_API_KEY') else 'MISSING')"
```

---

## 💰 Cost (Very Affordable!)

**Recommended: ChatGPT + Gemini**

| Provider   | Model   | Cost per Brief | Notes                 |
| ---------- | ------- | -------------- | --------------------- |
| **Gemini** | 1.5 Pro | **FREE**       | Generous daily limits |
| **OpenAI** | GPT-4o  | $0.02-0.05     | Or use free credits   |

**You only need ONE API key** - Gemini free tier is perfect for most usage!

---

## 🔒 Security

✅ `.env` file is git-ignored (your keys stay private)  
✅ Never commit API keys to git  
✅ Set usage limits in provider dashboards

---

## ❓ Troubleshooting

### "Error: No API keys found"
```powershell
# Make sure .env file exists
notepad .env

# Add at least one key:
OPENAI_API_KEY=sk-proj-...
# or
GEMINI_API_KEY=AIza...
```

### "ModuleNotFoundError: No module named 'dotenv'"
```powershell
pip install python-dotenv
# or
pip install -r ai_conversation_requirements.txt
```

### Keys not loading
```powershell
# Make sure you're in the right directory
cd tools\ai-evaluator

# Verify .env exists
dir .env
```

---

## 🎯 Next Steps

1. **Run setup**: `.\setup_ai_conversation.ps1`
2. **Get API keys**: See [GET_API_KEYS.md](GET_API_KEYS.md)
3. **Create your first brief**: Edit `example_tech_brief.md`
4. **Run evaluation**: `python ai_conversation.py --prompt example_tech_brief.md`
5. **Review results**: Check `output/` folder
6. **Host on site**: Copy to your downloads folder!

---

## 📞 Documentation

- **API Key Help**: [GET_API_KEYS.md](GET_API_KEYS.md) ⭐
- **Quick Commands**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **How It Works**: [CONVERSATION_FLOW.md](CONVERSATION_FLOW.md)
- **Full Guide**: [README.md](README.md)

**Ready to evaluate your first tech brief!** 🚀
