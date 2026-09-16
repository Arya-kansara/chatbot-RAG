# Notegoo — Multilingual Voice-Based Study Assistant

Notegoo is an AI-powered study companion that turns PDF notes into natural, spoken explanations — in English, Hindi, or Gujarati. It also answers direct questions, with or without a document, in a chat-style interface, with persistent memory and document-grounded answers via Retrieval-Augmented Generation (RAG).

## Problem

Students often have study material as dense PDFs (notes, cheat sheets, question banks), but reading long text is slow, and many learners — especially in regional-language-speaking areas — understand and retain concepts better when explained conversationally, in their own language, spoken aloud. Existing tools either read PDFs verbatim (not helpful) or work only in English.

## What It Does

- **Explain a full document** — upload a PDF, get a tutor-style spoken explanation
- **Ask a specific question about a document** — upload a PDF, ask something targeted, get a grounded answer using semantic search (RAG)
- **Ask a direct question** — no document needed, general Q&A
- **Conversation memory** — follow-up questions ("explain that more simply") work naturally, using persisted chat history
- **Adaptive responses** — short answers for quick meanings, detailed explanations when asked, step-by-step working for maths, formatted code blocks for programming questions, clean output for content-generation requests (essays, paragraphs)
- All modes work in **English, Hindi, or Gujarati**, with **6 voice options** (male/female per language)
- Handles natural Hinglish/Gujlish input (Romanized native language, e.g., "kem cho," "kaise ho")
- Markdown rendering — tables, bold text, and bullet points display properly formatted, not as raw symbols

## How It Works

```
User (chat interface)
    |
Flask backend routes based on input:
  - PDF + "explain everything"  -> full document explanation
  - PDF + specific question     -> RAG-based Q&A grounded in that document
  - No PDF, just a question     -> general tutor Q&A
    |
Text extraction (pdfplumber, for PDFs)
    |
For document Q&A: text is chunked, embedded (sentence-transformers),
stored in Supabase (pgvector) -> question embedded -> semantic similarity
search retrieves the most relevant chunks
    |
Recent conversation history (from Supabase) + relevant chunks + adaptive
style instructions -> assembled into a prompt
    |
LLM (Groq API - openai/gpt-oss-120b) generates the response
    |
Text-to-Speech (edge-tts) converts the response into spoken audio
    |
Response (text + audio) returned to the chat interface,
Markdown rendered via marked.js
```

### PDF Text Extraction
Uses `pdfplumber` to extract the text layer from text-based PDFs, page by page. Scanned/image-based PDFs aren't currently supported (would need OCR — see Future Work).

### Retrieval-Augmented Generation (RAG)
Documents are split into chunks (~3000 characters), and each chunk is converted into a 384-dimensional embedding using `sentence-transformers` (`all-MiniLM-L6-v2`), stored in Supabase using the `pgvector` extension. When a user asks a question about a document, the question is embedded using the same model, and a SQL function (`match_chunks`) performs cosine-similarity search to find the most semantically relevant chunks — scoped to the currently attached document. This replaced an earlier, simpler keyword-overlap matching approach, and correctly finds relevant content even when the question is phrased differently than the source text.

### Conversation Memory
Every exchange is saved to Supabase's `conversations` table. Before generating a new response, recent history is fetched and injected into the prompt, with an instruction telling the model to use it for resolving follow-up questions like "explain that more simply."

### Adaptive Response Styling
A layered prompt instruction set detects what kind of response is needed — a quick definition, a detailed explanation, a maths problem requiring step-by-step working, a coding question requiring a formatted code block, or a content-generation request (essay/paragraph) that should skip conversational framing entirely.

### Multilingual Generation (Not Translation)
The LLM generates responses directly in the target language rather than translating from an English draft, with natural code-mixing — keeping commonly-English terms (e.g., "computer," "SQL," "photosynthesis") in English even within Hindi/Gujarati sentences, matching how people actually speak.

### Text-to-Speech
`edge-tts` converts the LLM's text response into spoken audio, with 6 selectable voices (English/Hindi/Gujarati x Male/Female).

## Tech Stack

| Component | Tool |
|---|---|
| LLM | Groq API (`openai/gpt-oss-120b`) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector database | Supabase (PostgreSQL + pgvector) |
| Conversation storage | Supabase (PostgreSQL) |
| PDF text extraction | pdfplumber |
| Text-to-speech | edge-tts |
| Backend | Flask (Python) |
| Frontend | HTML / CSS / vanilla JavaScript, marked.js for Markdown rendering |
| Cost | Free — entirely free-tier tools |

## Key Engineering Decisions & Real Debugging

- **Model migration** — originally built on `llama-3.3-70b-versatile`, migrated to `openai/gpt-oss-120b` after Groq announced deprecation mid-project (Aug 16, 2026 shutdown)
- **Chunking for rate-limit handling** — hit a real 413 "request too large" error on large PDFs; solved with paragraph-boundary-aware chunking
- **Fixed an audio caching bug** — the browser served stale audio because every response was saved to the same filename; fixed with unique UUID-based filenames
- **Fixed truncated responses** — increased token limits and added explicit completion instructions
- **Diagnosed a Supabase RLS permissions issue** — new tables default to locked-down Row Level Security, blocking even backend writes until explicitly configured
- **Fixed a table-naming mismatch** — a typo (`document_chunk` vs `document_chunks`) silently broke RAG retrieval; Postgres error messages didn't make this obvious, requiring careful verification queries
- **Fixed a function-naming collision** — a locally-defined legacy function shadowed an imported one with the same name, causing the RAG upgrade to silently fail while error messages pointed elsewhere
- **Fixed cross-document retrieval bleed-through** — semantic search initially searched across ALL previously uploaded documents' chunks rather than scoping to the currently attached document; fixed by adding a document-name filter to the similarity search function
- **Optimized slow document processing** — batched embedding generation and database inserts instead of processing one chunk at a time
- **Deployment memory constraint** — attempted deployment on Render's free tier (512MB RAM) surfaced an out-of-memory error, since `sentence-transformers` pulls in PyTorch, which alone can exceed the available memory. This is a genuine, documented limitation of running local ML inference on free-tier hosting, and is noted as active future work (see below)

## Advantages

- Genuine RAG implementation with semantic search, not just keyword matching or full-document stuffing
- Multilingual generation, not translation — natural code-mixed output
- Three distinct interaction modes plus persistent conversation memory
- Zero cost in development — entirely free-tier APIs and libraries
- Tested systematically across subjects, languages, and edge cases (vague questions, trick questions, off-topic questions, emotionally-framed questions)

## Limitations

- Only supports text-based PDFs — scanned/handwritten documents aren't currently handled
- No user authentication — single shared session, not scoped per user
- Single-document context per conversation — multi-document support is planned but not yet implemented
- **Production deployment blocked by a memory constraint**: the embedding model (via PyTorch) exceeds free-tier hosting memory limits (512MB on Render). The application runs correctly in local development; a production deployment would require either a lighter-weight embedding approach (e.g., a hosted embedding API instead of local inference) or a higher-memory hosting tier
- Not yet mobile-responsive

## Future Work

- Resolve the deployment memory constraint — likely by switching to a hosted embedding API instead of local `sentence-transformers`/PyTorch inference, to keep the deployed app lightweight
- Multiple PDF upload support, with search scoped across all attached documents
- Mobile responsiveness
- User authentication (Supabase Auth), scoping conversation history and documents per user
- OCR support for photographed/scanned notes (image preprocessing with OpenCV — deskew, denoise, contrast enhancement — was built and tested; full OCR integration is a planned next step)
- CI/CD pipeline for automated testing and deployment on future updates

## Setup (Local Development)

```bash
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_key_here"        # Mac/Linux
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"

python app.py
```

On Windows PowerShell, set variables like this instead:
```powershell
$env:GROQ_API_KEY="your_key_here"
$env:SUPABASE_URL="your_supabase_url"
$env:SUPABASE_KEY="your_supabase_key"
```

Open `http://127.0.0.1:5000` in your browser.

## Project Structure

```
notegoo/
├── app.py                  # Flask backend, routes
├── extract_pdf.py          # PDF text extraction
├── explain_text.py         # Full-document explanation + chunking
├── answer_question.py      # Targeted & direct Q&A, RAG integration, memory
├── vector_search.py        # Embedding generation + semantic search (RAG)
├── db.py                   # Supabase connection, conversation history
├── text_to_speech.py       # Voice generation (6 voices)
├── preprocess_image.py     # Image preprocessing (built, OCR integration pending)
├── templates/
│   └── index.html          # Chat-style frontend
├── uploads/                 # Temporary PDF storage
└── static/audio/            # Generated audio files
```
