# COMMANDO Networks — RAG-Based WhatsApp AI Chatbot

A fully functional AI-powered WhatsApp chatbot built using **Retrieval-Augmented Generation (RAG)** methodology with **LangChain**. The chatbot integrates with a web-scraped knowledge base from [commandonetworks.com](https://www.commandonetworks.com) and can be deployed as a **WhatsApp Bot** via Twilio. It retains conversational context across multiple users, enabling meaningful multi-turn dialogues.

---

## Architecture

```
┌─────────────────┐
│  WhatsApp User   │ (Phone 1, Phone 2, ...)
└────────┬────────┘
         │ Message
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Twilio WhatsApp │────▶│  Flask Server     │
│  Sandbox         │◀────│  (app.py)         │
└─────────────────┘     └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │     RAG Pipeline         │
                    │     (rag_chain.py)       │
                    │                          │
                    │  ┌────────────────────┐  │
                    │  │ 1. Query Enrichment│  │  ← Handles "yes", pronouns ("it","this")
                    │  └────────┬───────────┘  │
                    │           ▼              │
                    │  ┌────────────────────┐  │
                    │  │ 2. FAISS Retrieval │  │  ← Semantic search on knowledge base
                    │  │    (Vector Store)  │  │
                    │  └────────┬───────────┘  │
                    │           ▼              │
                    │  ┌────────────────────┐  │
                    │  │ 3. LLM Generation  │  │  ← Groq (Llama 3.3 70B)
                    │  │    (Groq API)      │  │
                    │  └────────┬───────────┘  │
                    │           ▼              │
                    │  ┌────────────────────┐  │
                    │  │ 4. Context Store   │  │  ← Per-user conversation history
                    │  │   (by phone number)│  │
                    │  └────────────────────┘  │
                    └─────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Knowledge Base (data/) │
                    │                          │
                    │  • commando_knowledge    │  ← Scraped website pages
                    │    _base.txt             │
                    │  • product_overview.txt  │  ← Complete product catalog
                    │  • detailed_product      │  ← Deep specs for key products
                    │    _specs.txt            │
                    │  •  confusionclear.txt   │  ← Curated data for accuracy
                    │  •  website_data.txt.    │  ← Raw website data
                    └─────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why Chosen |
|-------|-----------|------------|
| Language | Python 3.9+ | Industry standard for AI/ML |
| RAG Framework | LangChain | Best-in-class RAG orchestration |
| Vector Database | FAISS (CPU) | Free, fast, local — no cloud dependency |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Lightweight, runs locally, free |
| LLM | Groq API (Llama 3.3 70B Versatile) | Free tier, fastest inference, high quality |
| Web Scraping | BeautifulSoup4 + Requests | Reliable HTML parsing |
| Document Parsing | PyPDF2, python-pptx | Extract text from PDFs and PPTs |
| WhatsApp Integration | Twilio WhatsApp Sandbox | Free, well-documented API |
| Web Server | Flask | Lightweight, perfect for webhooks |
| Tunneling | ngrok | Exposes local server to internet |

---

## Dependencies

```
flask==3.0.0
twilio==9.0.0
langchain==0.3.7
langchain-community==0.3.7
langchain-groq==0.2.1
langchain-huggingface==0.1.0
sentence-transformers==3.3.0
faiss-cpu==1.9.0
beautifulsoup4==4.12.3
requests==2.32.3
python-dotenv==1.0.1
pyngrok==7.2.1
PyPDF2==3.0.1
python-pptx==1.0.2
tiktoken==0.8.0
```

---

## Project Structure

```
commando-whatsapp-bot/
│
├── app.py                     # Flask server + Twilio WhatsApp webhook
├── rag_chain.py               # RAG pipeline (retrieval + generation + context)
├── build_vectorstore.py       # Builds FAISS index from knowledge base
├── scraper.py                 # Web scraper for commandonetworks.com
├── config.py                  # Centralized configuration
├── test_local.py              # Local testing (multi-user simulation)
│
├── data/
│   ├── commando_knowledge_base.txt    # Scraped website content
│   ├── product_overview.txt           # Complete product catalog + recommendations
│   ├── detailed_product_specs.txt     # Deep specs for key products
│   ├── confusionclear.txt             # for accuracy
│   ├── website_data.txt               # raw data
│   └── faiss_index/                   # Generated FAISS vector store
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── DOCUMENTATION.md           # Detailed approach and architecture document
└── SETUP.md                   # Step-by-step setup guide
```

---

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Groq API Key (free): https://console.groq.com
- Twilio Account (free trial): https://www.twilio.com
- ngrok (free): https://ngrok.com

### Step 1: Install Dependencies

```bash
git clone <repo-url>
cd commando-whatsapp-bot
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
GROQ_API_KEY=gsk_your_groq_api_key
TWILIO_ACCOUNT_SID=ACyour_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
NGROK_AUTH_TOKEN=your_ngrok_auth_token
```

### Step 3: Build the Vector Store

```bash
python build_vectorstore.py
```

### Step 4: Test Locally (Without WhatsApp)

```bash
python test_local.py
```

Multi-user testing:
```
Type a question → get answer
switch 2         → switch to User 2
Type a question → User 2 gets separate context
switch 1         → back to User 1 (remembers their context)
```

### Step 5: Run the WhatsApp Bot

```bash
python app.py
```

Copy the printed webhook URL and paste it in Twilio Sandbox Settings → "When a message comes in" → POST.

### Step 6: Test on WhatsApp

Send a message from your WhatsApp to the Twilio sandbox number.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **RAG Pipeline** | Retrieves relevant product data via FAISS semantic search, generates answers via Llama 3.3 70B |
| **Context Retention** | Maintains per-user conversation history keyed by phone number |
| **Multi-User Support** | Multiple WhatsApp users chat simultaneously with independent contexts |
| **YES Feature** | User says "yes/yeah/sure" → bot automatically provides more detail on last topic |
| **Pronoun Resolution** | "What models are in **it**?" → bot resolves "it" to the last discussed product |
| **Follow-up Suggestions** | Every response ends with a relevant follow-up question |
| **WhatsApp Formatting** | Bold, italic, bullet points optimized for mobile screens |
| **Smart Recommendations** | Use-case based product suggestions (IP cameras → E2000, not C3500) |
| **Web Scraping** | Automated scraping of commandonetworks.com + PDF/PPT extraction |

---

## Usage Examples

**Basic Query:**
```
User: What products does COMMANDO offer?
Bot:  Lists Switches, Wireless, Routers, Gateways, Accessories
```

**YES Feature:**
```
User: What switches support stacking?
Bot:  C3500 Series — C3500-24X, C3500-24X-2Q, C3500-24X-2C
User: yes
Bot:  Detailed C3500 specs — MPLS, VXLAN, VSF stacking, MLAG...
```

**Context Retention (Pronoun Resolution):**
```
User: Tell me about C3500 series
Bot:  C3500 info...
User: What are the different models available in it?
Bot:  C3500-24X, C3500-24X-2Q, C3500-24X-2C (understands "it" = C3500)
```

**Multi-User:**
```
User 1: I need a network for 300 users     → Gets gateway recommendation
User 2: Connect buildings 5km apart         → Gets wireless bridge options
User 1: What about firewall features?       → Bot remembers User 1's MSG-400 context
```

**Special Commands:**
| Command | Action |
|---------|--------|
| `hi` / `hello` | Welcome message |
| `help` | Show example questions |
| `reset` | Clear conversation history |

---

## License

This project is built for the COMMANDO Networks AI Interview Task — RAG-Based WhatsApp Chatbot.
