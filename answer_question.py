import os
from groq import Groq
from explain_text import chunk_text
from db import save_conversation, format_history_for_prompt
from vector_search import store_document_chunks , find_relevant_chunks_semantic




client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def find_relevant_chunks(chunks, user_question, max_chunks=2):
    question_words = set(user_question.lower().split())
    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        overlap = len(question_words & chunk_words)
        scored_chunks.append((overlap, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for score, chunk in scored_chunks[:max_chunks]]

    return "\n\n".join(top_chunks)

ADAPTIVE_STYLE_INSTRUCTION = """
- Match your response style to what the student is actually asking for:
  - If they ask for a quick meaning, definition, or "what is X" in a short way, 
    give a brief 1-3 sentence answer — don't over-explain.
  - If they ask to "explain in detail," "explain fully," or ask a broad 
    conceptual question, give a longer, well-structured explanation with 
    examples.
  - If they ask to solve a maths problem or equation, show the full 
    step-by-step working, not just the final answer.
  - If they ask a coding question, provide a clear code example (properly 
    formatted) along with a brief explanation of how it works — don't just 
    describe code in prose.
  - If unsure what depth they want, default to a clear, moderate-length 
    explanation — not too short, not overly long.
  - - When comparing multiple items, listing steps, or presenting structured 
  information, use Markdown formatting (tables, bullet points, bold for 
  key terms) to make it easy to scan — not just dense paragraphs.
"""


NATURAL_LANGUAGE_INSTRUCTION = """
- Use whichever words a real student would naturally say out loud in 
  {language} — some words are commonly said in English even in Hindi/
  Gujarati speech (e.g., "computer," "internet," "SQL"), while basic/
  everyday words should stay in native {language}. Don't force translation 
  where English is natural, and don't force English where native language 
  is natural.
"""

COMPLETION_INSTRUCTION = """
- Make sure you finish your explanation completely — do not cut off 
  mid-sentence or mid-thought, even if it takes a few more sentences 
  to wrap up naturally.
"""

CONTENT_VS_EXPLANATION_INSTRUCTION = """
- Determine whether the student wants (a) a concept explained to them, or 
  (b) a piece of written content generated (essay, paragraph, letter, 
  story, summary, etc.):
  - If they want a CONCEPT EXPLAINED: respond conversationally, like a 
    tutor talking to them (e.g., "So, this works because...").
  - If they want WRITTEN CONTENT (e.g., "write an essay on X", "write a 
    paragraph about Y", "draft a letter for Z"): give ONLY the clean 
    final content itself — no conversational framing before or after 
    (do not say things like "So you want me to write...", "Here's your 
    essay", "Does this sound good?", or "Let me know if you want 
    changes"). Just output the essay/content directly, ready to use.
  - If a word count is specified, stay close to it.
"""


def answer_question(user_question, context_text=None, document_name=None, language="English"):
    conversation_history = format_history_for_prompt(limit=10)

    if context_text:
        relevant_text = find_relevant_chunks_semantic(user_question, document_name=document_name, max_chunks=2)
        prompt = f"""You are a friendly, patient tutor talking to a student.
{conversation_history}
The student asked: "{user_question}"

Use the following study material to answer accurately:
{relevant_text}

Answer their question in {language}, as if you were speaking directly to 
them. Be conversational and clear.
{ADAPTIVE_STYLE_INSTRUCTION}
{CONTENT_VS_EXPLANATION_INSTRUCTION}
{NATURAL_LANGUAGE_INSTRUCTION.format(language=language)}
{COMPLETION_INSTRUCTION}

If the current question refers back to something in the recent conversation 
(e.g., "explain that more simply", "what about the second point"), use the 
conversation history above to understand what they're referring to.
"""
    else:
        relevant_text = None
        prompt = f"""You are a friendly, patient tutor talking to a student.
{conversation_history}
The student asked: "{user_question}"

Answer their question in {language}, as if you were speaking directly to 
them. Be conversational and clear.
{ADAPTIVE_STYLE_INSTRUCTION}
{CONTENT_VS_EXPLANATION_INSTRUCTION}
{NATURAL_LANGUAGE_INSTRUCTION.format(language=language)}
{COMPLETION_INSTRUCTION}

If the current question refers back to something in the recent conversation 
(e.g., "explain that more simply", "what about the second point"), use the 
conversation history above to understand what they're referring to.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000  # bumped up slightly to give room for code/detailed answers
    )

    return response.choices[0].message.content