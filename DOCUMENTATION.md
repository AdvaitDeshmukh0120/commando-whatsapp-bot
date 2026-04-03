# COMMANDO Networks WhatsApp RAG Chatbot — Documentation

## Table of Contents
1. [Overview of Approach and Architecture](#1-overview-of-approach-and-architecture)
2. [Instructions for Setting Up and Running Locally](#2-instructions-for-setting-up-and-running-locally)
3. [Suggestions for Future Improvements and Scalability](#3-suggestions-for-future-improvements-and-scalability)
4. [Demonstrating the Functionality](#4-demonstrating-the-functionality)

---

## 1. Overview of Approach and Architecture

### Problem Statement

Build a RAG-based AI chatbot for COMMANDO Networks that can be deployed on WhatsApp, answer product-related queries using web-scraped data, and maintain conversational context across multiple users.

### Approach

The solution follows a 4-phase pipeline:

**Phase 1 — Data Collection (Web Scraping)**

I scraped 30+ pages from commandonetworks.com using BeautifulSoup4 and Requests, extracting text content from product pages, company info, warranty details, partner programs, and more. Additionally, the scraper downloads and extracts text from any linked PDFs and PPTs using PyPDF2 and python-pptx.

The scraped data was organized into 4 knowledge base files:
- `commando_knowledge_base.txt` — Raw scraped website content (277 lines)
- `product_overview.txt` — Structured product catalog with all 13 switch series, wireless products, gateways, routers, accessories, software comparison, company info, partner program, warranty details, and a product recommendation guide (106 lines)
- `detailed_product_specs.txt` — Deep specifications for key products like C3500-24X, E2000-24GP-8CF, AIR-AP3000AX, MSG-150, MSG-1200, E1000-16GP-4CF (302 lines)
- `faq_direct_answers.txt` — Curated FAQ pairs covering ranking questions, similar-name disambiguation, feature-across-product queries, use-case recommendations, and common customer questions (171 lines)

**Why curated FAQ data?** During testing, I discovered that pure vector search struggles with ranking queries ("cheapest switch") and similar model names (E2000 vs E200). Adding curated FAQ pairs that directly match common question patterns significantly improved retrieval accuracy — a well-documented best practice in production RAG systems.

**Phase 2 — Data Processing and Indexing**

The knowledge base is processed through the following pipeline:
1. **Loading** — All text files are read and split into document sections
2. **Chunking** — Documents are split into chunks of 800 characters with 150-character overlap using LangChain's RecursiveCharacterTextSplitter
3. **Embedding** — Each chunk is converted to a 384-dimensional vector using the `sentence-transformers/all-MiniLM-L6-v2` model (runs locally, no API needed)
4. **Indexing** — Vectors are stored in a FAISS index for fast similarity search

**Phase 3 — RAG Pipeline (Retrieval + Generation)**

When a user sends a message, the pipeline:

1. **Query Enrichment** — Three types of intelligent query processing:
   - *Normal questions* → passed directly to FAISS
   - *Affirmative responses* ("yes", "yeah", "sure", "tell me more") → enriched with the original topic from conversation history, then searched
   - *Pronoun references* ("it", "this", "that") → resolved using conversation history and appended to the search query

2. **Retrieval** — FAISS semantic search finds the top 4 most relevant chunks (5 for follow-up queries). This was optimized to balance answer quality vs. token consumption.

3. **Generation** — Retrieved chunks + conversation history + user question are passed to Groq's Llama 3.3 70B model via LangChain. The system prompt instructs the LLM to:
   - Only answer from provided context
   - Use WhatsApp formatting (bold, italic, bullets)
   - Resolve pronouns from conversation history
   - End every response with a relevant follow-up suggestion

4. **History Update** — The question and answer are added to the user's conversation store.

**Phase 4 — WhatsApp Integration**

The Flask server exposes a `/webhook` endpoint that receives Twilio WhatsApp messages via HTTP POST. Each incoming message is routed through the RAG pipeline, and the response is sent back via Twilio's MessagingResponse. Users are identified by their WhatsApp phone number, enabling independent conversation contexts.

ngrok creates a secure tunnel from the local Flask server to the internet, allowing Twilio's cloud to reach the local webhook.

### Architecture Diagram

```
WhatsApp Users (Phone 1, Phone 2, ...)
        │
        ▼
┌──────────────┐
│   Twilio     │  Cloud-hosted WhatsApp API
│   Sandbox    │
└──────┬───────┘
       │ HTTP POST (webhook)
       ▼
┌──────────────┐
│   ngrok      │  Secure tunnel to localhost
│   tunnel     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│          Flask Server (app.py)        │
│                                      │
│  • Receives WhatsApp messages        │
│  • Routes to RAG pipeline            │
│  • Formats response for WhatsApp     │
│  • Sends reply via Twilio API        │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│       RAG Pipeline (rag_chain.py)    │
│                                      │
│  ┌─────────────────────────┐         │
│  │  Query Enrichment       │         │
│  │  • YES detection        │         │
│  │  • Pronoun resolution   │         │
│  └───────────┬─────────────┘         │
│              ▼                       │
│  ┌─────────────────────────┐         │
│  │  FAISS Vector Search    │         │
│  │  • 4 chunks (5 for YES) │         │
│  │  • all-MiniLM-L6-v2     │         │
│  └───────────┬─────────────┘         │
│              ▼                       │
│  ┌─────────────────────────┐         │
│  │  Groq LLM Generation   │         │
│  │  • Llama 3.3 70B       │         │
│  │  • Context + History    │         │
│  └───────────┬─────────────┘         │
│              ▼                       │
│  ┌─────────────────────────┐         │
│  │  Conversation Store     │         │
│  │  • Per-user (phone #)   │         │
│  │  • 6 pairs (12 msgs)   │         │
│  └─────────────────────────┘         │
│                                      │
└──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│     Knowledge Base (data/)           │
│                                      │
│  • commando_knowledge_base.txt       │
│  • product_overview.txt              │
│  • detailed_product_specs.txt        │
│  • faq_direct_answers.txt            │
│  • faiss_index/ (generated)          │
└──────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| FAISS over Pinecone/Weaviate | Free, local, no cloud dependency. Sufficient for our dataset size (~60KB). |
| Groq over OpenAI | Free tier with high-quality Llama 3.3 70B. Fastest inference available. |
| Sentence-transformers over OpenAI embeddings | Runs locally, free, no API calls needed. Fast embedding generation. |
| 800 chunk size, 4 retrieval chunks | Optimized for Groq's 100K daily token limit. Balances quality vs. token consumption. |
| In-memory conversation store | Simplest implementation for demo. Production would use Redis/SQLite. |
| FAQ augmentation | Addresses known weaknesses of vector search: ranking queries and similar-name confusion. |

---

## 2. Instructions for Setting Up and Running Locally

### Prerequisites

| Requirement | Where to Get |
|-------------|-------------|
| Python 3.9+ | https://python.org |
| Groq API Key (free) | https://console.groq.com |
| Twilio Account (free trial) | https://www.twilio.com |
| ngrok (free) | https://ngrok.com |

### Step-by-Step Setup

**1. Clone the repository and install dependencies:**
```bash
git clone <repo-url>
cd commando-whatsapp-bot
pip install -r requirements.txt
```

**2. Configure environment variables:**
```bash
cp .env.example .env
```
Edit `.env`:
```
GROQ_API_KEY=gsk_your_key_here
TWILIO_ACCOUNT_SID=ACyour_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
NGROK_AUTH_TOKEN=your_ngrok_token_here
```

**3. Build the vector store (one-time):**
```bash
python build_vectorstore.py
```

**4. Test locally without WhatsApp:**
```bash
python test_local.py
```
Commands: type questions to chat, `switch 2` for multi-user, `clear` to reset, `quit` to exit.

**5. Run the WhatsApp bot:**
```bash
python app.py
```

**6. Connect Twilio:**
- Copy the webhook URL printed in terminal
- Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message → Sandbox Settings
- Paste webhook URL in "When a message comes in" field
- Set method to POST → Save

**7. Test on WhatsApp:**
- Send `join <your-code>` to +1 415 523 8886 from WhatsApp
- Send `hi` to start chatting

### Optional: Re-scrape Website Data
```bash
python scraper.py           # Scrapes commandonetworks.com
python build_vectorstore.py  # Rebuilds FAISS index
```

---

## 3. Suggestions for Future Improvements and Scalability

### Short-Term Improvements

| Improvement | Description | Impact |
|-------------|-------------|--------|
| **Persistent Storage** | Replace in-memory conversation store with Redis or SQLite. Currently, conversation history is lost on server restart. | Conversations survive restarts |
| **Rich Media Responses** | Send product images alongside text responses using Twilio MMS. Product images are already available on commandonetworks.com. | More engaging user experience |
| **Multi-Language Support** | Add language detection (using langdetect library) and translate queries/responses. COMMANDO operates in 100+ countries. | Broader global reach |
| **Feedback Loop** | Allow users to rate responses (thumbs up/down via WhatsApp buttons) and log poor answers for improvement. | Continuous quality improvement |
| **Caching** | Cache frequent query-response pairs to reduce LLM API calls and improve response time. | Lower cost, faster responses |

### Medium-Term Improvements

| Improvement | Description | Impact |
|-------------|-------------|--------|
| **Scheduled Re-scraping** | Run scraper.py on a weekly cron job to automatically capture new products and updates from the website. | Always up-to-date knowledge base |
| **Analytics Dashboard** | Track popular queries, response times, user satisfaction, and conversation patterns using a simple dashboard. | Data-driven improvements |
| **PDF/Datasheet Delivery** | When users ask about a specific product, offer to send the official datasheet PDF directly in WhatsApp. | Higher value interactions |
| **Voice Message Support** | Use Whisper API to transcribe WhatsApp voice messages, process through RAG, and respond. | Accessibility improvement |
| **Hybrid Search** | Combine FAISS vector search with BM25 keyword search for better retrieval accuracy, especially for model numbers. | More accurate results |

### Scalability Plans

| Aspect | Current | Scalable Solution |
|--------|---------|-------------------|
| **Hosting** | Local machine + ngrok | Deploy on AWS EC2/GCP/Azure with a proper domain and SSL |
| **Vector Store** | FAISS (in-memory) | Migrate to Pinecone, Weaviate, or Qdrant for cloud-hosted vector search |
| **LLM** | Groq free tier (100K tokens/day) | Upgrade to Groq paid tier or use self-hosted Llama model via vLLM |
| **WhatsApp** | Twilio Sandbox | Register for Twilio WhatsApp Business API with a dedicated number |
| **Conversation Store** | In-memory Python dict | Redis for distributed caching across multiple server instances |
| **Load Balancing** | Single Flask instance | Gunicorn with multiple workers behind Nginx reverse proxy |
| **Monitoring** | Terminal logs | Prometheus + Grafana for metrics, Sentry for error tracking |
| **Data Updates** | Manual scraping | Automated CI/CD pipeline with scheduled scraping and re-indexing |

### Production Architecture (Proposed)

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (Nginx)        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Worker 1 │  │ Worker 2 │  │ Worker 3 │
        │ (Flask)  │  │ (Flask)  │  │ (Flask)  │
        └─────┬────┘  └─────┬────┘  └─────┬────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Redis   │  │ Pinecone │  │  Groq /  │
        │ (Cache)  │  │ (Vector) │  │ Self-host│
        └──────────┘  └──────────┘  └──────────┘
```

---

## 4. Demonstrating the Functionality

### Feature Demonstration

**Feature 1: RAG-Based Product Knowledge**

The chatbot accurately answers questions about COMMANDO products using only the scraped knowledge base, never hallucinating information.

```
User:  What products does COMMANDO Networks offer?
Bot:   COMMANDO Networks offers: Switches, Wireless APs, Routers, Gateways, Accessories
       [Lists each category with descriptions]

User:  What is the switching capacity of C3500-24X?
Bot:   The switching capacity of the C3500-24X is 480 Gbps.
```

**Feature 2: Context Retention Across Multi-Turn Conversations**

The bot maintains conversation history per user and resolves pronouns using context.

```
User:  What switches support stacking?
Bot:   C3500 Series — C3500-24X, C3500-24X-2Q, C3500-24X-2C

User:  What are the different models available in it?
Bot:   The C3500 Series has: C3500-24X (24x10G SFP+), C3500-24X-2Q (2x40G QSFP+),
       C3500-24X-2C (2x100G QSFP28)
       [Understands "it" = C3500 Series from conversation history]
```

**Feature 3: YES Follow-Up Feature**

When users reply with "yes", "yeah", "sure", or "tell me more", the bot automatically provides deeper information about the last discussed topic.

```
User:  What switches support stacking?
Bot:   C3500 Series supports stacking via VSF...
       Would you like to know more about C3500 Series features?

User:  yes
Bot:   The C3500 Series (Marshall) supports: MPLS, VXLAN, NVGRE, GENEVE tunnels,
       Stacking via VSF, MLAG as an alternative...
```

**Feature 4: Multi-User Independent Conversations**

Each WhatsApp user has completely independent conversation context.

```
User 1: I need to setup a network for 300 users
Bot:    Recommends MSG-400 gateway + E2000 switches + AIR-AP3000AX

User 2: I want to connect two buildings 5km apart
Bot:    Recommends AIR-WB900-5K wireless bridges

User 1: What about the firewall features?
Bot:    MSG-400 has: Packet Filters, URL Blocking, Web Content Filters...
        [Remembers User 1 was discussing MSG-400, not wireless bridges]
```

**Feature 5: Smart Product Recommendations**

The bot recommends the right product for the use case, not just the most expensive one.

```
User:  I need a 24 port PoE switch for IP cameras
Bot:   For IP cameras, the best options are:
       • E2000-24GP-8CF — 24-port Managed, PoE+ 450W, Surveillance VLAN
       • E1000-24GP-4CF — 24-port Unmanaged, PoE+ 450W, plug-and-play
       [Correctly recommends edge switches, NOT the C3500 data center switch]
```

**Feature 6: WhatsApp-Optimized Formatting**

All responses use WhatsApp-native formatting for optimal mobile readability: bold product names, italic follow-up suggestions, bullet points, and short paragraphs.

**Feature 7: Follow-Up Suggestions**

Every response ends with a contextually relevant follow-up question, encouraging natural conversation flow and making the bot feel more interactive and helpful.

---

### Testing Results

| Test Scenario | Result |
|---------------|--------|
| Basic product query | ✅ Pass |
| YES follow-up feature | ✅ Pass |
| Pronoun resolution ("it", "this") | ✅ Pass |
| Multi-user context isolation | ✅ Pass |
| Product recommendation (IP cameras) | ✅ Pass |
| Gateway comparison | ✅ Pass |
| Warranty information | ✅ Pass |
| Company location query | ✅ Pass |
| Stacking query + follow-up | ✅ Pass |
| WhatsApp formatting | ✅ Pass |
| Conversation reset | ✅ Pass |

---

*Built for the COMMANDO Networks AI Interview Task*
