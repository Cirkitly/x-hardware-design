from flow import qa_flow
import sys

def main():
    """
    Main function to run the interactive QA-bot.
    The bot will continuously prompt for questions until the user types 'exit' or 'quit'.
    """
    print("Welcome to Cirkitly RAG Bot! Ask a question or type 'exit' to quit.")
    
    interactive_flow = qa_flow

    while True:
        shared = {}
        interactive_flow.run(shared)

        question = shared.get("question", "").strip()
        if question.lower() in ["exit", "quit"]:
            print("Exiting Cirkitly. Goodbye!")
            break

        print("\n" + "="*20)
        print(f"Question: {question}")
        print(f"Retrieved Context: {shared.get('retrieved_context', 'N/A')}")
        print(f"Answer: {shared.get('answer', 'No answer was generated.')}")
        print("="*20 + "\n")


if __name__ == "__main__":
    print("Initializing RAG pipeline...")
    try:
        main()
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        print("Please ensure your Ollama server is running and the model is available.", file=sys.stderr)
        sys.exit(1)