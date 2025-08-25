# 🆓 FREE AI APIs Setup Guide - Maritime Assistant

## 🎉 **BEST FREE OPTIONS (No Credit Card Required!)**

Your backend is now configured to use FREE AI APIs! Here are the best options:

---

## 🏆 **Option 1: Hugging Face (100% FREE Forever)**

### ✅ **Why Choose Hugging Face:**
- **Completely FREE** - No credit card, no limits
- **No expiration** - Free forever
- **Great models** - Llama 2, Code Llama, Mistral
- **Easy signup** - Just email required

### 📝 **Setup Steps:**
1. **Visit:** https://huggingface.co/join
2. **Sign up** with email (no credit card!)
3. **Go to:** https://huggingface.co/settings/tokens
4. **Create** a new token (select "Read" access)
5. **Copy** your token
6. **Add to `.env`:**
   ```env
   HUGGINGFACE_API_KEY=hf_your_token_here
   ```

---

## 🚀 **Option 2: Groq (Super Fast & FREE)**

### ✅ **Why Choose Groq:**
- **FREE** - Generous limits
- **SUPER FAST** - Lightning quick responses
- **Great models** - Llama 3, Mixtral, Gemma
- **Easy setup** - 2-minute signup

### 📝 **Setup Steps:**
1. **Visit:** https://console.groq.com
2. **Sign up** with email
3. **Go to** API Keys section
4. **Create** new API key
5. **Copy** your key
6. **Add to `.env`:**
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

---

## 💎 **Option 3: OpenRouter (FREE Credits)**

### ✅ **Why Choose OpenRouter:**
- **$5-10 FREE credits** monthly
- **Multiple models** - GPT-4o mini, Llama 3.1, Claude
- **Very cheap** after free credits
- **Great performance**

### 📝 **Setup Steps:**
1. **Visit:** https://openrouter.ai
2. **Sign up** with email
3. **Go to** Keys section
4. **Create** API key
5. **Copy** your key
6. **Add to `.env`:**
   ```env
   OPENROUTER_API_KEY=sk-or-your_key_here
   ```

---

## ⚡ **Quick Start (Choose Any One):**

### **For Completely FREE (Recommended):**
```bash
# 1. Get Hugging Face token (100% free)
# 2. Add to .env:
HUGGINGFACE_API_KEY=hf_your_token_here

# 3. Start backend
cd backend
python main.py

# 4. Start frontend  
npm run dev

# 5. Test at: http://localhost:3000/chat
```

### **For Super Fast (Also Free):**
```bash
# 1. Get Groq API key (free & fast)
# 2. Add to .env:
GROQ_API_KEY=gsk_your_key_here

# 3. Start services and test!
```

---

## 📊 **Comparison:**

| Service | Cost | Speed | Models | Setup Time |
|---------|------|-------|--------|------------|
| **Hugging Face** | 100% FREE | Medium | Llama 2, Mistral | 2 min |
| **Groq** | FREE | ⚡ SUPER FAST | Llama 3, Mixtral | 2 min |
| **OpenRouter** | FREE Credits | Fast | GPT-4o mini, Llama 3.1 | 3 min |
| **Together AI** | $25 FREE | Fast | Llama 2, Mistral | 3 min |

---

## 🎯 **My Personal Recommendation:**

### **Start with Groq** (fastest setup + super fast responses):
1. Go to https://console.groq.com
2. Sign up → Get API key
3. Add to `.env`: `GROQ_API_KEY=your_key`
4. Done! Lightning fast maritime AI responses!

---

## 🧪 **Test Your Setup:**

Once you add ANY of these API keys:

1. **Start backend:** `cd backend && python main.py`
2. **Start frontend:** `npm run dev`  
3. **Check status:** http://localhost:3000/settings
4. **Test chat:** http://localhost:3000/chat

---

## 🆘 **Need Help?**

**Quick test command:**
```bash
curl http://localhost:8002/settings
```

**Should show:**
```json
{
  "current_ai_provider": "groq",  // or "huggingface"
  "features_enabled": {
    "ai_chat": true
  }
}
```

---

**🎉 With any of these free options, you'll get professional maritime AI responses without spending a penny!**
