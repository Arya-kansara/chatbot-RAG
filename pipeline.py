import asyncio
from extract_pdf import extract_text_from_pdf
from explain_text import explain_text
from text_to_speech import text_to_speech
from answer_question import answer_question
from text_to_speech import text_to_speech

def run_pipeline(mode , pdf_path=None , language="English" , user_question=None):
    """
    mode: "explain_full | ask_about_pdf | ask_direct"
    """

    if mode == "explain_full":
        raw_text = extract_text_from_pdf(pdf_path)
        result_text = explain_text(raw_text, language)

    elif mode == "ask_about_pdf":
        raw_text = extract_text_from_pdf(pdf_path)
        result_text = answer_question(user_question, context_text=raw_text, language=language)

    elif mode == "ask_direct":
        result_text = answer_question(user_question, language=language)

    else:
        raise ValueError("Invalid mode. Choose from 'explain_full', 'ask_about_pdf', or 'ask_direct'.")

    asyncio.run(text_to_speech(result_text, output_file="output_audio.mp3", language=language))
    print(f"Done")


if __name__ == "__main__":
    # Mode A: Explain the entire PDF in English
    """print("=== Mode A: Explain the Entire PDF ===")
    run_pipeline(mode="explain_full", 
                 pdf_path="pdf/ML_Cheat_Sheet_Beginner_to_Advanced.pdf", 
                 language="Gujarati",
                    user_question=None)"""

    """# Mode B: Ask a specific question about the PDF in English
    print("\n\n=== Mode B: Ask a Specific Question About the PDF ===")
    run_pipeline(mode="ask_about_pdf", 
                 pdf_path="pdf/ML_Cheat_Sheet_Beginner_to_Advanced.pdf", 
                 language="Hindi",
                 user_question="Machine Learning mai overfitting ko kaise kam kar sakte hain?")"""

    # Mode C: Ask a direct question without a PDF in English
    print("\n\n=== Mode C: Ask a Direct Question Without a PDF ===")
    run_pipeline(mode="ask_direct", 
                 pdf_path=None, 
                 language="Gujarati",
                 user_question="Explain Chunks , Tokenisation and embeddings simply?")