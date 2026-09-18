"""
Embeddings service — chunks resume text and generates/stores vector embeddings.

Uses Ollama's nomic-embed-text model for embedding generation
and pgvector in PostgreSQL for storage and similarity search.
"""

import re
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text

from backend.models import Resume, ResumeChunk
from backend.database import is_postgres


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT CHUNKING
# ═══════════════════════════════════════════════════════════════════════════════

def chunk_text(text: str, max_tokens: int = 300, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of roughly max_tokens words."""
    if not text or not text.strip():
        return []

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    words = text.split()

    if len(words) <= max_tokens:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDING GENERATION + STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

async def embed_resume(resume: Resume, db: Session) -> int:
    """Chunk a resume's text and generate embeddings. Returns number of chunks created."""
    from backend.services.ollama import embed

    if not resume.content_text:
        return 0

    # Clear existing chunks for this resume
    db.query(ResumeChunk).filter(ResumeChunk.resume_id == resume.id).delete()

    # Chunk the text
    chunks = chunk_text(resume.content_text)
    if not chunks:
        return 0

    # Prefix chunks with resume context for better embeddings
    prefixed = [
        f"Resume: {resume.filename}. {chunk}"
        for chunk in chunks
    ]

    # Generate embeddings via Ollama
    embeddings = await embed(prefixed)

    # Store in database
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        db.add(ResumeChunk(
            resume_id=resume.id,
            chunk_index=i,
            chunk_text=chunk,
            embedding=emb,
        ))

    db.commit()
    return len(chunks)


async def embed_all_resumes(db: Session) -> dict:
    """Generate embeddings for all resumes in the database."""
    resumes = db.query(Resume).all()
    total_chunks = 0
    processed = 0

    for resume in resumes:
        count = await embed_resume(resume, db)
        total_chunks += count
        processed += 1
        print(f"  [{processed}/{len(resumes)}] {resume.filename}: {count} chunks")

    return {"resumes_processed": processed, "total_chunks": total_chunks}


# ═══════════════════════════════════════════════════════════════════════════════
# SIMILARITY SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

async def search_similar_chunks(query: str, db: Session, top_k: int = 5) -> list[dict]:
    """Find the most relevant resume chunks for a query using pgvector cosine similarity."""
    from backend.services.ollama import embed_single

    # Embed the query
    query_embedding = await embed_single(f"search_query: {query}")

    if is_postgres:
        # Use pgvector's cosine distance operator
        emb_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        results = db.execute(
            sql_text("""
                SELECT rc.id, rc.chunk_text, rc.resume_id, rc.chunk_index,
                       r.filename, r.doc_type,
                       (rc.embedding <=> CAST(:emb AS vector)) as distance
                FROM resume_chunks rc
                JOIN resumes r ON r.id = rc.resume_id
                ORDER BY rc.embedding <=> CAST(:emb AS vector)
                LIMIT :k
            """),
            {"emb": emb_str, "k": top_k}
        ).fetchall()

        return [
            {
                "chunk_id": row[0],
                "chunk_text": row[1],
                "resume_id": row[2],
                "chunk_index": row[3],
                "filename": row[4],
                "doc_type": row[5],
                "distance": float(row[6]),
                "relevance": round(1 - float(row[6]), 3),
            }
            for row in results
        ]
    else:
        # SQLite fallback: no vector search, return all chunks (for dev only)
        chunks = db.query(ResumeChunk).limit(top_k).all()
        return [
            {
                "chunk_id": c.id,
                "chunk_text": c.chunk_text,
                "resume_id": c.resume_id,
                "chunk_index": c.chunk_index,
                "filename": c.resume.filename if c.resume else "?",
                "doc_type": c.resume.doc_type if c.resume else "?",
                "distance": 0.5,
                "relevance": 0.5,
            }
            for c in chunks
        ]
