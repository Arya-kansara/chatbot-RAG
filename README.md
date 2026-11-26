# Notegoo - Multilingual AI Study Assistant

Notegoo turns study notes into clear, structured answers you can read and listen to, in English, Hindi or Gujarati. Upload a PDF and ask about it, or ask any question. Answers about a PDF come from a RAG pipeline that searches only the document you attached.

## Features

- **Ask with or without a PDF.** With a PDF, the answer is built from the most relevant passages of that file.
- **Structured answers.** Each answer starts with a one-line summary, then headings, key points, numbered steps, tables, code blocks, callouts and mind maps where they fit. Quick questions get short answers, and "explain" questions get detailed notes.
- **Three languages, six voices.** Choose the response language (English, Hindi, Gujarati) and a male or female voice. Answers are read aloud and the audio is stored in Supabase Storage.
- **Chat memory.** Follow-ups such as "explain that more simply" work. The page keeps each chat in the browser and sends the last 8 messages with every question.
- **Chat history.** Conversations are saved in the browser and can be reopened from the sidebar.
- **Responsive UI.** A custom HTML/CSS/JS interface that works on desktop, tablet and mobile, with a collapsible sidebar and a docked input bar on small screens.

## How it works

```
Browser (chat UI, history in localStorage)
   |  question + last 8 messages + language/voice
   v
Flask (app.py)
   |-- PDF upload: pdfplumber -> text -> sentence-aware chunks -> embeddings -> Supabase (pgvector)
   |-- Question: embed question -> pgvector search (current document only) -> top 3 chunks
   |-- Prompt: format rules + language rules + chunks + chat history -> Groq LLM
   |-- Answer text -> edge-tts -> MP3 -> Supabase Storage
   v
Browser renders Markdown (tables, steps, code with Copy) and plays the audio
```

### Retrieval (RAG)
- Text is split into chunks of about 1000 characters at sentence boundaries, with a 150-character overlap.
- Each chunk is embedded with `all-MiniLM-L6-v2` (384 dimensions) using `fastembed`, which runs on ONNX and does not need PyTorch.
- Chunks are stored in a Supabase Postgres table with `pgvector`. A SQL function, `match_chunks`, returns the closest chunks by cosine distance, filtered to the attached document.
- Short follow-up questions are searched together with the previous question, so "explain that" still finds the right passage.
- If vector search returns nothing, a keyword fallback searches the extracted text.

### Prompting
One shared instruction block (`prompts.py`) sets the answer format. Further instructions control natural Hindi/Gujarati wording (common English terms stay in English), clean output for essays and letters, and how to treat follow-up questions.

## Tech stack

| Part | Tool |
|---|---|
| LLM | Groq API, `openai/gpt-oss-120b` |
| Embeddings | fastembed, `all-MiniLM-L6-v2` |
| Vector store and audio storage | Supabase (Postgres + pgvector, Storage) |
| PDF text | pdfplumber |
| Voice | edge-tts |
| Backend | Flask, gunicorn |
| Frontend | HTML, CSS, JavaScript, marked.js |

## Run it locally

1. Clone the repo and create a virtual environment, then install the packages:
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   python -m pip install -r requirements.txt
   ```
2. Create a `.env` file in the project folder:
   ```
   GROQ_API_KEY=your_groq_key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_secret_key
   ```
3. In the Supabase SQL Editor, run:
   ```sql
   create extension if not exists vector;

   create table document_chunks (
     id bigserial primary key,
     document_name text not null,
     chunk_text text not null,
     embedding vector(384),
     created_at timestamptz default now()
   );
   alter table document_chunks disable row level security;
   grant select, insert, update, delete on public.document_chunks to service_role;
   grant usage, select on all sequences in schema public to service_role;

   create or replace function match_chunks (
     query_embedding vector(384),
     match_count int default 3,
     filter_document_name text default null
   )
   returns table (id bigint, document_name text, chunk_text text, similarity float)
   language sql stable as $$
     select id, document_name, chunk_text, 1 - (embedding <=> query_embedding) as similarity
     from document_chunks
     where filter_document_name is null or document_name = filter_document_name
     order by embedding <=> query_embedding
     limit match_count;
   $$;
   ```
4. In Supabase Storage, create a **public** bucket named `audio`.
5. Start the app and open `http://127.0.0.1:5000`:
   ```bash
   python app.py
   ```

## Deployment notes

- The `Procfile` runs `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 2`. The longer timeout is needed because a PDF question can include an LLM call, voice generation and an upload.
- Set `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` and `SECRET_KEY` as environment variables on the host.
- The first attempt on a 512 MB free tier failed because `sentence-transformers` pulls in PyTorch. Moving to `fastembed` removed that dependency.
- Free Supabase projects pause after a period of inactivity. If the app shows connection errors, restore the project from the Supabase dashboard.

## Limitations

- Only text-based PDFs work. Scanned PDFs need OCR, which is not built.
- One PDF per chat, and no user accounts. Chunks are stored per file name, so two people uploading files with the same name would overwrite each other's chunks.
- Chat memory sends the last 8 messages, so very old parts of a long chat are forgotten.
- Chat history lives in the browser, so it is not shared across devices.
- "Explain this document" makes one LLM call per large chunk, so it is slow on long PDFs.

## What I would build next

- Multiple PDFs per chat and per-user accounts with Supabase Auth.
- An embedding cache and an answer cache for repeated questions.
- OCR for scanned notes.
- Quiz and flashcard modes that cover the whole document.
- A rolling summary for long chats instead of a fixed 8-message window.

## Project structure

```
app.py               Flask routes: upload, process, clear_file
answer_question.py   Prompt building, retrieval, memory, LLM call
explain_text.py      Whole-document explanation with chunking
extract_pdf.py       PDF text extraction
vector_search.py     Chunking, embeddings, pgvector search
text_to_speech.py    edge-tts voice generation
db.py                Supabase client and audio upload
prompts.py           Shared answer-format instruction
templates/index.html The chat interface
Procfile, requirements.txt, .gitignore
```
