import os
import re
import sys
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import config
from rag_chain import generate_response, clear_history, load_vectorstore, get_llm, add_to_history

app = Flask(__name__)

twilio_client = None
if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
    twilio_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def clean_for_whatsapp(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    text = re.sub(r'__(.+?)__', r'_\1_', text)
    return text


@app.route("/", methods=["GET"])
def home():
    return (
        "<h1>COMMANDO Networks WhatsApp Chatbot</h1>"
        "<p>Status: Running</p>"
    ), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    print(f"\n{'='*50}")
    print(f"From: {sender}")
    print(f"Message: {incoming_msg}")
    print(f"{'='*50}")

    msg_lower = incoming_msg.lower().strip()

    if msg_lower in ["reset", "clear", "restart"]:
        clear_history(sender)
        reply_text = (
            "🔄 *Conversation reset!*\n\n"
            "Hi! I'm the *COMMANDO Networks AI Assistant* 🤖\n\n"
            "How can I help you today?\n\n"
            "You can ask me about:\n"
            "• Products (Switches, Wireless, Routers, Gateways)\n"
            "• Specifications & features\n"
            "• Warranty & support\n"
            "• Partner program\n\n"
            "_Just type your question!_ 👇"
        )

    elif msg_lower in ["hi", "hello", "hey", "start", "hii", "hiii", "namaste"]:
        reply_text = (
            "👋 Hello! Welcome to *COMMANDO Networks*!\n\n"
            "I'm your AI assistant. I can help you with:\n\n"
            "• *Product Info* — Switches, Wireless APs, Routers, Gateways, Accessories\n"
            "• *Specifications* — Detailed specs for any model\n"
            "• *Comparisons* — Compare different products\n"
            "• *Warranty* — ShieldX warranty program\n"
            "• *Support* — Technical support info\n"
            "• *Partners* — Partner program details\n\n"
            "_What would you like to know?_ 👇"
        )
        add_to_history(sender, "user", incoming_msg)
        add_to_history(sender, "assistant", reply_text)

    elif msg_lower == "help":
        reply_text = (
            "📖 *COMMANDO Bot — How to Use*\n\n"
            "Just type any question naturally! Examples:\n\n"
            "• _Which switches support PoE+?_\n"
            "• _Tell me about the C3500 series_\n"
            "• _What Wi-Fi 6 access points do you have?_\n"
            "• _How does the warranty work?_\n\n"
            "💡 *Tip:* After each answer, I'll suggest a follow-up.\n"
            "Just reply *yes* to get more details!\n\n"
            "Commands:\n"
            "• *reset* — Clear conversation history\n"
            "• *help* — Show this message"
        )

    elif not incoming_msg:
        reply_text = "Please send a text message 📝\n\nI can help you with *COMMANDO Networks* products!"

    else:
        reply_text = generate_response(sender, incoming_msg)
        reply_text = clean_for_whatsapp(reply_text)

    if len(reply_text) > 1500:
        cut_point = reply_text.rfind('\n', 0, 1450)
        if cut_point == -1:
            cut_point = reply_text.rfind('. ', 0, 1450)
        if cut_point == -1:
            cut_point = 1450
        reply_text = reply_text[:cut_point] + "\n\n_Reply *more* to continue..._"

    print(f"Reply: {reply_text[:100]}...")

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy", "bot": "COMMANDO WhatsApp RAG Chatbot"}, 200


def start_ngrok():
    try:
        from pyngrok import ngrok
        if config.NGROK_AUTH_TOKEN:
            ngrok.set_auth_token(config.NGROK_AUTH_TOKEN)
        public_url = ngrok.connect(config.FLASK_PORT, "http")
        webhook_url = f"{public_url}/webhook"

        print("\n" + "=" * 60)
        print("🌐 NGROK TUNNEL ACTIVE")
        print("=" * 60)
        print(f"Public URL:  {public_url}")
        print(f"Webhook URL: {webhook_url}")
        print("=" * 60)
        print("\nSet this webhook URL in Twilio Sandbox Settings.")
        print("=" * 60 + "\n")
        return webhook_url
    except Exception as e:
        print(f"\nCould not start ngrok: {e}")
        print(f"Start manually: ngrok http {config.FLASK_PORT}")
        return None


def main():
    print("\n" + "=" * 60)
    print("   COMMANDO Networks WhatsApp RAG Chatbot")
    print("=" * 60)

    missing = []
    if not config.GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not config.TWILIO_ACCOUNT_SID:
        missing.append("TWILIO_ACCOUNT_SID")
    if not config.TWILIO_AUTH_TOKEN:
        missing.append("TWILIO_AUTH_TOKEN")

    if missing:
        print(f"\nMissing: {', '.join(missing)}")
        print("Please fill in your .env file.")
        sys.exit(1)

    print("\n[1/3] Loading vector store...")
    try:
        load_vectorstore()
    except FileNotFoundError:
        print("Vector store not found. Building...")
        os.system(f"{sys.executable} build_vectorstore.py")
        load_vectorstore()

    print("[2/3] Initializing LLM...")
    get_llm()

    print("[3/3] Starting server...")
    start_ngrok()

    print(f"\n🚀 Server running on http://0.0.0.0:{config.FLASK_PORT}")
    print("   Webhook endpoint: /webhook\n")

    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=False)


if __name__ == "__main__":
    main()
