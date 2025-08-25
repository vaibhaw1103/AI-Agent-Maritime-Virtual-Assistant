# 🚀 Maritime Assistant - Real API Setup Guide

## 📋 Your .env File is Ready!

Your `.env` file has been created with all the necessary placeholders. Now you just need to add your API keys.

## 🔑 Step 1: Get OpenAI API Key (Recommended - Easiest)

### Option A: OpenAI API
1. **Visit:** https://platform.openai.com
2. **Sign up/Login** with your account
3. **Go to:** "API Keys" section in your dashboard
4. **Click:** "Create new secret key" 
5. **Copy** the key (starts with `sk-...`)
6. **Edit your `.env` file** and add:
   ```env
   OPENAI_API_KEY=sk-your_actual_key_here
   ```

### Option B: Azure OpenAI (Enterprise)
1. **Visit:** https://portal.azure.com
2. **Create:** "Azure OpenAI" resource
3. **Get:** API Key, Endpoint, Deployment Name
4. **Add to `.env`:**
   ```env
   AZURE_OPENAI_API_KEY=your_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```

## 🌤️ Step 2: Get Weather API Key (FREE)

1. **Visit:** https://openweathermap.org/api
2. **Sign up** for a free account  
3. **Go to:** "My API Keys" in your dashboard
4. **Copy** your API key
5. **Add to `.env`:**
   ```env
   OPENWEATHER_API_KEY=your_weather_key_here
   ```

## ⚡ Step 3: Install & Start

### Install Dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Start Backend:
```bash
python main.py
```

### Start Frontend (New Terminal):
```bash
cd ..
npm run dev
```

## ✅ Step 4: Test Your Setup

1. **Visit:** http://localhost:3000/settings
2. **Check:** Which APIs are configured (Green = Working!)
3. **Test Chat:** Go to http://localhost:3000/chat
4. **Test Weather:** Go to http://localhost:3000/weather

## 💰 API Costs (Very Affordable)

| Service | Free Tier | Cost |
|---------|-----------|------|
| **OpenAI GPT-4** | $5 free credits | ~$0.03 per 1K tokens |
| **OpenWeatherMap** | 1000 calls/day | FREE for basic plan |

**Estimated Usage:** ~$1-5 per month for regular testing

## 🐛 Troubleshooting

### Common Issues:
- **"Mock responses"** = API key not configured correctly
- **CORS errors** = Backend not running on port 8002
- **No weather data** = Check OpenWeatherMap key is active

### Quick Tests:
```bash
# Test Backend Health
curl http://localhost:8002/

# Test Chat API
curl -X POST http://localhost:8002/chat -H "Content-Type: application/json" -d '{"query":"What is laytime?"}'

# Check Settings
curl http://localhost:8002/settings
```

## 🎉 What You'll Get

Once configured, your maritime assistant will provide:

✅ **Real AI Responses** - Professional maritime expertise from GPT-4  
✅ **Live Weather Data** - Real-time marine conditions  
✅ **Maritime Intelligence** - Industry-specific knowledge base  
✅ **Professional Calculations** - Laytime, demurrage, distance calculations  

---

**Need help getting API keys?** The OpenAI and OpenWeatherMap signup processes are very straightforward and you'll be up and running in 5-10 minutes!
