from sentence_transformers import SentenceTransformer
from db import supabase
from explain_text import chunk_text



# Load the embedding model once
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    """
    converts a piece of text into a vector embedding using the SentenceTransformer model.
    """

    embedding = embedder.encode(text)
    return embedding.tolist()  # Convert to list for JSON serialization


def store_document_chunks(document_name, full_text):
    """
    Splits a document into chunks, embeds them all at once (batched), 
    and inserts them into Supabase in a single request.
    """
    chunks = chunk_text(full_text, max_chars=1500)

    # Embed ALL chunks in one batch call (much faster than one-by-one)
    embeddings = embedder.encode(chunks)

    # Build all rows first
    rows = [
        {
            "document_name": document_name,
            "chunk_text": chunk,
            "embedding": embedding.tolist()
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    # Insert all rows in a single database call instead of one per chunk
    supabase.table("document_chunks").insert(rows).execute()

    print(f"Stored {len(chunks)} chunks for '{document_name}'")


def find_relevant_chunks_semantic(user_question,document_name=None,max_chunks=2):
    """
    Finds the most semantically relevant chunks to a question, 
    using vector similarity search instead of keyword overlap.
    """
    question_embedding = embed_text(user_question)

    result = supabase.rpc("match_chunks", {
        "query_embedding": question_embedding,
        "match_count": max_chunks,
        "filter_document_name": document_name
    }).execute()

    relevant_texts = [row["chunk_text"] for row in result.data]
    return "\n\n".join(relevant_texts)