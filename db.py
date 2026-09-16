import os
from supabase import create_client , Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def save_conversation(question, answer, language, mode):
    """
    Saves a single Q&A exchange to the conversations table.
    """
    data = {
        "question": question,
        "answer": answer,
        "language": language,
        "mode": mode
    }
    result = supabase.table("conversations").insert(data).execute()
    return result


def get_recent_conversations(limit=5):
    """
    Fetches the most recent conversations, oldest first (chronological order),
    so they can be fed into the prompt as conversation history.
    """
    result = supabase.table("conversations") \
        .select("*") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()

    # Reverse so oldest comes first — makes more sense as "history" in a prompt
    return list(reversed(result.data))


def format_history_for_prompt(limit=5):
    """
    Formats recent conversation history into a readable block of text
    to inject into the LLM prompt.
    """
    history = get_recent_conversations(limit=limit)
    if not history:
        return ""

    formatted = "Here is the recent conversation history for context:\n\n"
    for row in history:
        formatted += f"Student asked: {row['question']}\n"
        formatted += f"You answered: {row['answer']}\n\n"

    return formatted

def save_document(filename):
    """
    Records that a document was uploaded.
    """
    data = {"filename": filename}
    result = supabase.table("documents").insert(data).execute()
    return result


if __name__ == "__main__":
    # Quick test
    print("Testing save...")
    save_conversation(
        question="What is machine learning?",
        answer="Machine learning is a field of AI where systems learn from data.",
        language="English",
        mode="direct_question"
    )
    print("Saved!")

    print("\nTesting retrieve...")
    recent = get_recent_conversations(limit=3)
    for row in recent:
        print(f"- Q: {row['question']}")
        print(f"  A: {row['answer'][:60]}...")
        print(f"  ({row['language']}, {row['created_at']})\n")