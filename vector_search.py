import re
from fastembed import TextEmbedding
from db import supabase

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"   # 384 dimensions
_embedder = None


def get_embedder():
    """Load the model on first use, so the server starts fast and uses less memory at boot."""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=MODEL_NAME)
    return _embedder


def embed_text(text):
    return list(get_embedder().embed([text]))[0].tolist()


def chunk_for_search(text, max_chars=1000, overlap=150):
    """Sentence-aware chunks with a small overlap between neighbours."""
    parts = re.split(r'(?<=[.!?\u0964])\s+|\n+', text)
    chunks, current = [], ""
    for p in parts:
        p = p.strip()
        if not p or p.startswith("--- Page"):
            continue
        if current and len(current) + len(p) + 1 > max_chars:
            chunks.append(current.strip())
            tail = current[-overlap:]
            current = tail[tail.find(" ") + 1:] + " "
        current += p + " "
    if current.strip():
        chunks.append(current.strip())
    return chunks


def store_document_chunks(document_name, full_text):
    """Chunk the document, embed all chunks in one batch, and store them in one insert."""
    chunks = chunk_for_search(full_text)
    if not chunks:
        raise ValueError("No readable text found in this PDF.")

    embeddings = list(get_embedder().embed(chunks))
    rows = [
        {
            "document_name": document_name,
            "chunk_text": chunk,
            "embedding": emb.tolist(),
        }
        for chunk, emb in zip(chunks, embeddings)
    ]

    # Remove older copies of the same file so search never returns duplicates
    supabase.table("document_chunks").delete().eq("document_name", document_name).execute()
    supabase.table("document_chunks").insert(rows).execute()
    print(f"Stored {len(rows)} chunks for '{document_name}'")


def find_relevant_chunks_semantic(user_question, document_name=None, max_chunks=3):
    """Semantic search, scoped to the currently attached document."""
    result = supabase.rpc("match_chunks", {
        "query_embedding": embed_text(user_question),
        "match_count": max_chunks,
        "filter_document_name": document_name,
    }).execute()
    return "\n\n".join(row["chunk_text"] for row in result.data)