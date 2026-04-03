import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K_RESULTS = 4
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTORSTORE_PATH = "data/faiss_index"
KNOWLEDGE_BASE_PATH = "data/commando_knowledge_base.txt"

MAX_HISTORY_LENGTH = 6
