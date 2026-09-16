import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def chunk_text(text, max_chars=6000):
    """
    Splits text into chunks under a safe character limit,
    trying to break at paragraph boundaries where possible.
    """
    chunks = []
    current_chunk = ""

    paragraphs = text.split("\n")
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chars:
            current_chunk += para + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def explain_text(raw_text, language="English"):
    """
    Takes raw extracted text and returns a tutor-style spoken explanation.
    Handles long text by chunking and explaining each part separately.
    """
    chunks = chunk_text(raw_text)
    print(f"Text split into {len(chunks)} chunk(s).")

    all_explanations = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"Explaining chunk {i}/{len(chunks)}...")

        prompt = f"""You are a friendly, patient tutor explaining study notes out loud to a student.

Here are the student's notes (part {i} of {len(chunks)}):
\"\"\"
{chunk}
\"\"\"

Explain this content in {language}, as if you were speaking directly to the student:
- Use simple, conversational language (not formal/written style)
- Break down any technical terms briefly
- Be CONCISE — aim for a short, focused explanation, not exhaustive detail
- Do not just repeat the notes word-for-word — actually explain the concepts
- Use whichever words a real student would naturally say out loud in 
  {language} — some words are commonly said in English even in Hindi/
  Gujarati speech (e.g., "computer," "internet," "SQL"), while basic/
  everyday words should stay in native {language} (e.g., basic maths, 
  common objects, everyday actions). Don't force translation where 
  English is natural, and don't force English where native language 
  is natural — match how a real teacher or student would actually speak.
- Make sure you finish your explanation completely — do not cut off 
  mid-sentence or mid-thought, even if it takes a few more sentences 
  to wrap up naturally.

Give only the explanation text, nothing else (no preamble like "Sure, here's the explanation").
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        all_explanations.append(response.choices[0].message.content)

    return "\n\n".join(all_explanations)


if __name__ == "__main__":
    with open("extracted_output.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("Generating explanation... (this may take a bit longer for large notes)\n")

    explanation = explain_text(raw_text, language="English")

    print("===== TUTOR EXPLANATION =====")
    print(explanation)

    with open("explanation_output.txt", "w", encoding="utf-8") as f:
        f.write(explanation)

    print("\n\nDone. Saved to explanation_output.txt")