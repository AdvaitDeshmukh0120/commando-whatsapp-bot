import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import config

conversation_store = {}


def get_history(user_id):
    if user_id not in conversation_store:
        conversation_store[user_id] = []
    return conversation_store[user_id]


def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > config.MAX_HISTORY_LENGTH * 2:
        conversation_store[user_id] = history[-(config.MAX_HISTORY_LENGTH * 2):]


def clear_history(user_id):
    conversation_store[user_id] = []


def format_history(user_id):
    history = get_history(user_id)
    if not history:
        return "No previous conversation."
    formatted = []
    for msg in history[-config.MAX_HISTORY_LENGTH * 2:]:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)


_vectorstore = None
_embeddings = None


def load_vectorstore():
    global _vectorstore, _embeddings
    if _vectorstore is not None:
        return _vectorstore

    print("Loading embedding model...")
    _embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    if os.path.exists(config.VECTORSTORE_PATH):
        print(f"Loading FAISS index from {config.VECTORSTORE_PATH}...")
        _vectorstore = FAISS.load_local(
            config.VECTORSTORE_PATH, _embeddings, allow_dangerous_deserialization=True
        )
        print("Vector store loaded successfully!")
    else:
        raise FileNotFoundError(f"Vector store not found at {config.VECTORSTORE_PATH}")

    return _vectorstore


def retrieve_context(query, k=None):
    if k is None:
        k = config.TOP_K_RESULTS
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    context_parts = []
    for i, doc in enumerate(results):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[Source {i+1}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


_llm = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env file.")
    _llm = ChatGroq(
        groq_api_key=config.GROQ_API_KEY,
        model_name=config.GROQ_MODEL,
        temperature=0.3,
        max_tokens=1024,
    )
    print(f"LLM initialized: {config.GROQ_MODEL}")
    return _llm


SYSTEM_PROMPT = """You are COMMANDO Networks AI Assistant on WhatsApp. COMMANDO develops and sells networking equipment: Switches, Wireless APs, Routers, Gateways, Accessories.

RULES:
1. ONLY answer from the provided context. Never make up info.
2. If unknown, say: "Contact COMMANDO support at https://www.commandonetworks.com/contact"
3. Include model numbers and key specs when listing products.

CONTEXT RETENTION:
- Read CONVERSATION HISTORY carefully. Resolve "it/this/that/these" using previous messages.
- "yes/yeah/sure/more" = customer wants MORE DETAIL on the last topic discussed.
- Follow-ups must connect to previous conversation. Never ignore history.

WHATSAPP FORMAT:
- *bold* for product names and model numbers
- _italic_ for emphasis
- • for bullet points
- Short paragraphs, generous line breaks (phone screen)
- Max 1400 characters

FOLLOW-UP (MANDATORY):
End EVERY response with a relevant follow-up suggestion in this format:
_Would you like to know more about [specific related topic]?_ 👇

CONTEXT:
{context}

HISTORY:
{history}
"""

USER_PROMPT = """Customer: {question}

Answer from context. Use WhatsApp formatting. Resolve pronouns from history. End with follow-up suggestion."""


def get_last_topic(user_id):
    history = get_history(user_id)
    if not history:
        return None

    real_question = None
    last_assistant_answer = None

    for msg in reversed(history):
        if msg["role"] == "assistant" and last_assistant_answer is None:
            last_assistant_answer = msg["content"]
        if msg["role"] == "user":
            if not is_affirmative(msg["content"]):
                real_question = msg["content"]
                break

    if real_question is None:
        for msg in history:
            if msg["role"] == "user" and not is_affirmative(msg["content"]):
                real_question = msg["content"]
                break

    return {"last_answer": last_assistant_answer, "real_question": real_question}


AFFIRMATIVE_WORDS = {
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "ya", "haan",
    "tell me more", "more details", "go ahead", "please", "yes please",
    "continue", "more", "detail", "details", "elaborate", "explain more",
    "sure thing", "of course", "absolutely", "definitely", "why not",
    "yes i want", "yes tell me", "go on", "keep going", "yess", "yesss"
}


def is_affirmative(message):
    msg = message.lower().strip().rstrip("!?.,'")
    if msg in AFFIRMATIVE_WORDS:
        return True
    for word in AFFIRMATIVE_WORDS:
        if len(word) > 3 and word in msg:
            return True
    return False


PRONOUN_WORDS = {"it", "this", "that", "these", "them", "those", "its"}


def has_pronoun(message):
    msg_lower = message.lower()
    words = msg_lower.split()
    for word in words:
        clean = word.strip(",.?!:;'\"()[]")
        if clean in PRONOUN_WORDS:
            if any(q in msg_lower for q in [
                "what", "how", "does", "is", "are", "can", "which", "tell",
                "about", "available", "models", "specs", "features", "support",
                "compare", "difference", "price", "cost", "warranty",
                "in it", "of it", "for it", "about it", "about this",
                "about that", "in this", "in that", "of this", "of that"
            ]):
                return True
    return False


def generate_response(user_id, question):
    try:
        enriched_question = question

        if is_affirmative(question):
            last_topic = get_last_topic(user_id)
            if last_topic and last_topic["real_question"]:
                enriched_question = (
                    f"Give me more detailed and in-depth information about: "
                    f"{last_topic['real_question']}. "
                    f"Include all available models, detailed specifications, "
                    f"features, and technical details."
                )

        elif has_pronoun(question):
            last_topic = get_last_topic(user_id)
            if last_topic and last_topic["real_question"]:
                enriched_question = f"{question} (referring to: {last_topic['real_question']})"

        extra = 1 if is_affirmative(question) else 0
        context = retrieve_context(enriched_question, k=config.TOP_K_RESULTS + extra)
        history = format_history(user_id)

        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ])
        chain = prompt | llm

        response = chain.invoke({
            "context": context,
            "history": history,
            "question": question,
        })
        answer = response.content

        add_to_history(user_id, "user", question)
        add_to_history(user_id, "assistant", answer)
        return answer

    except Exception as e:
        print(f"Error generating response: {e}")
        return (
            "Sorry, I encountered an error processing your request. "
            "Please try again or contact COMMANDO support at "
            "https://www.commandonetworks.com/contact"
        )


if __name__ == "__main__":
    print("COMMANDO RAG Chain - Interactive Test")
    print("Type 'quit' to exit, 'clear' to reset.\n")
    test_user = "test_user_001"
    while True:
        question = input("You: ").strip()
        if question.lower() == 'quit':
            break
        if question.lower() == 'clear':
            clear_history(test_user)
            print("History cleared.\n")
            continue
        if not question:
            continue
        print("\nBot:", generate_response(test_user, question), "\n")
