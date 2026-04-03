import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_chain import generate_response, clear_history, load_vectorstore, get_llm


AUTO_TESTS = [
    {
        "name": "Basic Product Query",
        "user_id": "test_user_1",
        "messages": ["What products does COMMANDO offer?"]
    },
    {
        "name": "Stacking + YES + Context",
        "user_id": "test_user_2",
        "messages": [
            "Which switches support stacking?",
            "yes",
            "What are the different models available in it?",
        ]
    },
    {
        "name": "Gateway Comparison",
        "user_id": "test_user_3",
        "messages": [
            "Compare all gateway models",
            "Which one is best for 300 users?",
        ]
    },
    {
        "name": "IP Camera Recommendation",
        "user_id": "test_user_4",
        "messages": ["I need a 24 port PoE switch for IP cameras"]
    },
    {
        "name": "Warranty",
        "user_id": "test_user_5",
        "messages": ["How does the warranty work?", "What is ShieldX Total?"]
    },
    {
        "name": "Company Info",
        "user_id": "test_user_6",
        "messages": [
            "What is COMMANDO Networks?",
            "Where is the company located?",
        ]
    },
]


def run_automated_tests():
    print("\n" + "=" * 70)
    print("   AUTOMATED TEST SUITE")
    print("=" * 70)

    total_tests = 0
    passed = 0

    for test in AUTO_TESTS:
        print(f"\n{'─' * 70}")
        print(f"TEST: {test['name']}")
        print(f"{'─' * 70}")

        user_id = test["user_id"]
        clear_history(user_id)

        for msg in test["messages"]:
            total_tests += 1
            print(f"\n👤 User: {msg}")
            try:
                response = generate_response(user_id, msg)
                print(f"🤖 Bot: {response}")
                if len(response) < 20 or ("error" in response.lower() and "encountered" in response.lower()):
                    print("   ❌ FAIL")
                else:
                    print("   ✅ PASS")
                    passed += 1
            except Exception as e:
                print(f"   ❌ FAIL: {e}")

    print(f"\n{'=' * 70}")
    print(f"   RESULTS: {passed}/{total_tests} tests passed")
    print(f"{'=' * 70}\n")


def run_interactive():
    print("\n" + "=" * 70)
    print("   COMMANDO Networks RAG Chatbot — Interactive Mode")
    print("=" * 70)
    print("\nCommands:")
    print("  Type your question to chat")
    print("  'switch <number>' — Switch to different user")
    print("  'clear'           — Clear current user's history")
    print("  'users'           — Show active users")
    print("  'quit'            — Exit\n")

    current_user = "whatsapp:+919999900001"
    user_names = {current_user: "User 1"}

    print(f"Current user: {user_names[current_user]} ({current_user})")
    print("─" * 70)

    while True:
        try:
            question = input(f"\n👤 [{user_names[current_user]}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() == 'quit':
            print("Goodbye!")
            break

        if question.lower() == 'clear':
            clear_history(current_user)
            print("   ✅ History cleared.")
            continue

        if question.lower() == 'users':
            for uid, name in user_names.items():
                marker = " ◀ (current)" if uid == current_user else ""
                print(f"     • {name}: {uid}{marker}")
            continue

        if question.lower().startswith('switch'):
            parts = question.split()
            if len(parts) == 2:
                num = parts[1]
                new_user = f"whatsapp:+91999990000{num}"
                new_name = f"User {num}"
                user_names[new_user] = new_name
                current_user = new_user
                print(f"   ✅ Switched to {new_name} ({new_user})")
            else:
                print("   Usage: switch <number>")
            continue

        response = generate_response(current_user, question)
        print(f"\n🤖 Bot: {response}")


def main():
    print("\n" + "=" * 70)
    print("   COMMANDO RAG Chatbot — Local Test Environment")
    print("=" * 70)

    print("\n[1/2] Loading vector store...")
    try:
        load_vectorstore()
    except FileNotFoundError:
        print("Vector store not found. Building...")
        os.system(f"{sys.executable} build_vectorstore.py")
        load_vectorstore()

    print("[2/2] Initializing LLM...")
    get_llm()
    print("Ready!\n")

    if "--auto" in sys.argv:
        run_automated_tests()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
