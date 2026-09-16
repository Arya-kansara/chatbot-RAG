import pdfplumber

def extract_text_from_pdf(pdf_path):
    """ Extract raw text from a text based pdf Returns the full extracted text as a single string"""

    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page_num , page in enumerate(pdf.pages  , start = 1):
            page_text = page.extract_text()

            if page_text:
                full_text += f"\n--- Page {page_num} ---\n"
                full_text += page_text
            else:
                print(f"Warning No Text  Found on {page_num}")

    return full_text


if __name__ == "__main__":
    pdf_path = "AI5026_Supporting_Question Bank.pdf"
    extracted_text = extract_text_from_pdf(pdf_path)

    print("===== EXTRACTED TEXT =====")
    print(extracted_text)

    # Save to a text file too, so you can inspect it easily
    with open("extracted_output.txt", "w", encoding="utf-8") as f:
        f.write(extracted_text)

    print("\n\nDone. Also saved to extracted_output.txt")