# Step-by-Step Setup Guide

This guide walks you through setting up the COMMANDO WhatsApp RAG Chatbot from scratch.

---

## STEP 1: Get API Keys (All Free)

### 1A. Groq API Key (Free LLM)
1. Go to https://console.groq.com
2. Sign up with Google/GitHub
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy and save the key (starts with `gsk_...`)

### 1B. Twilio Account (Free WhatsApp Sandbox)
1. Go to https://www.twilio.com/try-twilio
2. Sign up (no credit card needed for trial)
3. Verify your phone number
4. From the Dashboard, copy your **Account SID** and **Auth Token**
5. Go to **Messaging → Try it out → Send a WhatsApp message**
6. You'll see a sandbox number (usually `+1 415 523 8886`) and a join code
7. From your WhatsApp, send the join code (e.g., `join <word>-<word>`) to that number
8. You should get a confirmation reply

### 1C. ngrok (Free Tunnel)
1. Go to https://ngrok.com
2. Sign up for free
3. Download ngrok for your OS
4. Copy your auth token from the dashboard
5. Run: `ngrok config add-authtoken YOUR_TOKEN`

---

## STEP 2: Install the Project

```bash
# Unzip the project
unzip commando-whatsapp-bot.zip
cd commando-whatsapp-bot

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## STEP 3: Configure Environment

```bash
# Copy the template
cp .env.example .env

# Edit .env with your credentials
# Use any text editor (notepad, nano, vim, VS Code)
```

Fill in your `.env` file:
```
GROQ_API_KEY=gsk_your_actual_key_here
TWILIO_ACCOUNT_SID=AC_your_actual_sid_here
TWILIO_AUTH_TOKEN=your_actual_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
NGROK_AUTH_TOKEN=your_ngrok_token_here
```

---

## STEP 4: Build the Vector Store

```bash
python build_vectorstore.py
```

Expected output:
```
Loading: data/commando_knowledge_base.txt
Loaded 15 document sections.
Created 85 chunks (chunk_size=800, overlap=150)
Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
Building FAISS vector store...
Vector store saved to: data/faiss_index
Quick retrieval test...
Vector store build complete!
```

---

## STEP 5: Test Locally (Without WhatsApp)

```bash
# Interactive mode
python test_local.py

# Or run automated tests
python test_local.py --auto
```

This lets you verify the RAG pipeline works before connecting WhatsApp.

---

## STEP 6: Run the WhatsApp Bot

```bash
python app.py
```

Expected output:
```
[1/3] Loading vector store...
[2/3] Initializing LLM...
[3/3] Starting server...

🌐 NGROK TUNNEL ACTIVE
Public URL:  https://abc123.ngrok.io
Webhook URL: https://abc123.ngrok.io/webhook

🚀 Server running on http://0.0.0.0:5000
```

---

## STEP 7: Connect Twilio Webhook

1. Copy the **Webhook URL** from the terminal output
2. Go to Twilio Console → **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Click **Sandbox Settings** (or go to the Sandbox configuration page)
4. In **"When a message comes in"**, paste your webhook URL:
   `https://abc123.ngrok.io/webhook`
5. Set the method to **POST**
6. Click **Save**

---

## STEP 8: Test on WhatsApp!

1. Open WhatsApp on your phone
2. Send a message to the Twilio sandbox number
3. Try these test messages:
   - `hi` → Welcome message
   - `What switches do you have?` → Product listing
   - `Which switches support stacking?` → C3500 series
   - `What are the different models available in it?` → Context-aware follow-up
   - `Tell me about Wi-Fi 6 access points` → Wireless products
   - `How does warranty work?` → Warranty info
   - `reset` → Clear conversation

---

## Troubleshooting

### "Vector store not found"
Run `python build_vectorstore.py` first.

### "GROQ_API_KEY not set"
Make sure you created `.env` file and added your Groq API key.

### ngrok not connecting
- Make sure you ran `ngrok config add-authtoken YOUR_TOKEN`
- Check if another ngrok instance is already running
- Try running ngrok manually: `ngrok http 5000`

### Twilio not sending messages
- Make sure you joined the sandbox from your WhatsApp
- Check the webhook URL is correct in Twilio settings
- Look at the Flask terminal for incoming requests

### Bot gives wrong answers
- Run `python scraper.py` to get fresh data
- Rebuild: `python build_vectorstore.py`
- Check if the `.env` GROQ_API_KEY is valid

---

## Recording the Demo Video

For your demo video, show:

1. **Starting the bot**: Run `python app.py` and show it connecting
2. **Basic query**: Ask about products from WhatsApp
3. **Specific product**: Ask about a specific model (e.g., C3500-24X)
4. **Context retention**: Ask a follow-up question that requires memory
5. **Multi-user**: Show a second WhatsApp user (or use the `test_local.py` with `switch` command)
6. **Reset**: Show the `reset` command clearing history

Tip: Use a screen recorder that captures both your phone (WhatsApp) and your laptop (terminal) side by side.
