import os
from groq import Groq
from explain_text import chunk_text
from vector_search import find_relevant_chunks_semantic
from prompts import STRUCTURE_INSTRUCTION

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def find_relevant_chunks(chunks, user_question, max_chunks=2):
    """Keyword-overlap fallback, used only if the vector search returns nothing."""
    question_words = set(user_question.lower().split())
    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        overlap = len(question_words & chunk_words)
        scored_chunks.append((overlap, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for score, chunk in scored_chunks[:max_chunks]]

    return "\n\n".join(top_chunks)


ADAPTIVE_STYLE_INSTRUCTION = STRUCTURE_INSTRUCTION

NATURAL_LANGUAGE_INSTRUCTION = """
- Use whichever words a real student would naturally say out loud in
  {language} - some words are commonly said in English even in Hindi/
  Gujarati speech (e.g., "computer," "internet," "SQL"), while basic/
  everyday words should stay in native {language}. Don't force translation
  where English is natural, and don't force English where native language
  is natural.
"""

COMPLETION_INSTRUCTION = """
- Make sure you finish your explanation completely - do not cut off
  mid-sentence or mid-thought, even if it takes a few more sentences
  to wrap up naturally.
"""

CONTENT_VS_EXPLANATION_INSTRUCTION = """
- Determine whether the student wants (a) a concept explained to them, or
  (b) a piece of written content generated (essay, paragraph, letter,
  story, etc.):
  - If they want a CONCEPT EXPLAINED: follow the response format above.
  - If they want WRITTEN CONTENT (e.g., "write an essay on X", "write a
    paragraph about Y", "draft a letter for Z"): give ONLY the clean
    final content itself - no conversational framing before or after
    (do not say things like "So you want me to write...", "Here's your
    essay", "Does this sound good?", or "Let me know if you want
    changes"). Just output the essay/content directly, ready to use.
  - If a word count is specified, stay close to it.
"""

FOLLOW_UP_INSTRUCTION = """This is a continuing chat. If the question refers back to earlier
messages (for example "explain that more simply", "give an example",
"what about the second point"), answer about the earlier topic."""


def answer_question(user_question, context_text=None, document_name=None,
                    language="English", history=None):
    history = history or []
    print("MEMORY:", len(history), "|", user_question)

    # Short follow-ups like "explain that again" have no keywords of their own,
    # so search the PDF using the previous question as well.
    search_query = user_question
    if len(user_question.split()) < 8:
        last_user = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"), ""
        )
        search_query = (last_user + " " + user_question).strip()

    if context_text:
        relevant_text = None

        # First try Supabase semantic search.
        try:
            relevant_text = find_relevant_chunks_semantic(
                search_query,
                document_name=document_name,
                max_chunks=3
            )
        except Exception as e:
            print(f"Semantic search failed: {e}")

        # If semantic search returns nothing useful, fall back to the
        # locally extracted PDF text.
        if not relevant_text or not relevant_text.strip():
            print("Using local PDF text fallback.")
            chunks = chunk_text(context_text, max_chars=6000)
            relevant_text = find_relevant_chunks(chunks, search_query, max_chunks=3)

        if not relevant_text or not relevant_text.strip():
            raise ValueError("Could not retrieve relevant content from the uploaded PDF.")

        prompt = f"""You are a friendly, patient tutor talking to a student.

The student asked: "{user_question}"

{FOLLOW_UP_INSTRUCTION}

Use the following study material to answer accurately.
If the answer is not present in the material, clearly say so.

Study material:
{relevant_text}

Answer in {language}, clearly.

{ADAPTIVE_STYLE_INSTRUCTION}
{CONTENT_VS_EXPLANATION_INSTRUCTION}
{NATURAL_LANGUAGE_INSTRUCTION.format(language=language)}
{COMPLETION_INSTRUCTION}
"""
    else:
        prompt = f"""You are a friendly, patient tutor talking to a student.

The student asked: "{user_question}"

{FOLLOW_UP_INSTRUCTION}

Answer in {language}, clearly.

{ADAPTIVE_STYLE_INSTRUCTION}
{CONTENT_VS_EXPLANATION_INSTRUCTION}
{NATURAL_LANGUAGE_INSTRUCTION.format(language=language)}
{COMPLETION_INSTRUCTION}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=history + [{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content