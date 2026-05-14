# How to Get API Keys

## 🔑 OpenAI API Key (ChatGPT)

### Step 1: Create OpenAI Account
1. Go to https://platform.openai.com/signup
2. Sign up with email or Google account
3. Verify your email

### Step 2: Get API Key
1. Go to https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Give it a name (e.g., "Tech Brief Evaluator")
4. **Copy the key immediately** (you won't see it again!)
5. Paste into your `.env` file as `OPENAI_API_KEY=sk-proj-...`

### Pricing
- **Free tier**: $5 credit for new accounts (expires after 3 months)
- **Pay-as-you-go**: ~$0.01-0.03 per tech brief evaluation
- **Set usage limits**: https://platform.openai.com/account/billing/limits

**Models available:**
- `gpt-4o` (recommended) - Most capable
- `gpt-4o-mini` - Cheaper, still good
- `gpt-3.5-turbo` - Fastest, cheapest

---

## 🔑 Google Gemini API Key

### Step 1: Get API Key
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select **"Create API key in new project"** (or use existing)
5. **Copy the key** (starts with `AIza...`)
6. Paste into your `.env` file as `GEMINI_API_KEY=AIza...`

### Pricing
- **Free tier**: 
  - 60 requests per minute
  - 1,500 requests per day
  - **More than enough for tech brief evaluation!**
- **Paid tier**: $0.00035 per 1K characters (very cheap)

**Models available:**
- `gemini-1.5-pro` (recommended) - Most capable
- `gemini-1.5-flash` - Faster, cheaper
- `gemini-pro` - Original model

**Gemini limits page:** https://ai.google.dev/pricing

---

## 🔑 Anthropic API Key (Optional - Claude)

### Step 1: Create Anthropic Account
1. Go to https://console.anthropic.com/
2. Sign up with email
3. Verify your email

### Step 2: Get API Key
1. Go to https://console.anthropic.com/settings/keys
2. Click **"Create Key"**
3. Give it a name
4. **Copy the key** (starts with `sk-ant-...`)
5. Paste into your `.env` file as `ANTHROPIC_API_KEY=sk-ant-...`

### Pricing
- **No free tier** (credit card required)
- Pay-as-you-go: ~$0.015 per tech brief evaluation
- $5 minimum to start

**Models available:**
- `claude-3-5-sonnet-20241022` (best)
- `claude-3-opus-20240229` (most capable, expensive)

---

## 💡 Recommendations

### For Tech Brief Evaluation:

**Best combination (what the script defaults to):**
1. **ChatGPT (GPT-4o)** - Technical Evaluator
2. **Gemini (1.5 Pro)** - Strategic Analyst

**Why?**
- Both have free/cheap tiers
- Complementary strengths (technical vs strategic)
- ChatGPT excels at structured technical analysis
- Gemini excels at broad strategic thinking

### Minimum Setup:
- You only need **ONE** API key to run the script
- **Gemini** is best for free usage (generous limits)
- **OpenAI** is best for quality (but costs money after free credits)

---

## 🔐 Setup Your Keys

### 1. Copy the example file:
```powershell
Copy-Item .env.example .env
```

### 2. Edit `.env` file:
```powershell
notepad .env
```

### 3. Paste your keys:
```env
OPENAI_API_KEY=sk-proj-abc123xyz...
GEMINI_API_KEY=AIzaSyABC123xyz...
```

### 4. Save and close

**That's it!** The keys will be loaded automatically when you run the script.

---

## 🛡️ Security Tips

✅ **DO:**
- Keep your `.env` file private (it's in `.gitignore`)
- Use different keys for different projects
- Rotate keys periodically
- Set usage limits in the provider's dashboard

❌ **DON'T:**
- Commit `.env` to git
- Share keys publicly
- Use keys in client-side code
- Leave keys in command history

---

## 🧪 Test Your Setup

```powershell
# Test that keys are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'); print('Gemini:', 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

Expected output:
```
OpenAI: SET
Gemini: SET
```

---

## 💰 Cost Estimates

**For a typical tech brief evaluation (10 rounds, ~5000 tokens):**

| Provider  | Model             | Cost per Evaluation           |
| --------- | ----------------- | ----------------------------- |
| Gemini    | 1.5 Pro           | **FREE** (under daily limits) |
| OpenAI    | GPT-4o            | ~$0.02-0.05                   |
| OpenAI    | GPT-4o-mini       | ~$0.002-0.005                 |
| Anthropic | Claude 3.5 Sonnet | ~$0.015-0.03                  |

**Running 20 evaluations:**
- Gemini only: **$0** (free tier)
- OpenAI GPT-4o: ~$0.40-1.00
- Mixed (GPT-4o + Gemini): ~$0.20-0.50

---

## 📞 Support

- **OpenAI Help**: https://help.openai.com/
- **Gemini Help**: https://ai.google.dev/gemini-api/docs
- **Anthropic Help**: https://support.anthropic.com/
