"""
RAG pipeline — Retrieve-Augment-Generate for resume Q&A and job matching.
"""

from sqlalchemy.orm import Session

from backend.services.embeddings import search_similar_chunks
from backend.services import ollama as ollama_svc


SYSTEM_PROMPT = """You are an Expert Hiring Manager AI assistant analyzing Rifat Haque's resume portfolio.
You have access to chunks of text from various resumes and cover letters.
Answer questions accurately based ONLY on the provided resume context.
If the context doesn't contain enough information to answer, say so.
Be concise, specific, and reference which resume(s) you're drawing from."""


async def chat(query: str, db: Session, top_k: int = 5) -> dict:
    """
    RAG chat: embed query → retrieve relevant chunks → generate answer.

    Returns: {"answer": str, "sources": list[dict]}
    """
    # 1. Retrieve relevant chunks
    chunks = await search_similar_chunks(query, db, top_k=top_k)

    if not chunks:
        return {
            "answer": "I don't have any resume data to search through. Please generate embeddings first.",
            "sources": [],
        }

    # 2. Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1}: {chunk['filename']} ({chunk['doc_type']}) — relevance: {chunk['relevance']}]\n"
            f"{chunk['chunk_text']}\n"
        )
    context = "\n".join(context_parts)

    # 3. Build prompt
    prompt = f"""Based on the following resume excerpts, answer the user's question.

--- RESUME CONTEXT ---
{context}
--- END CONTEXT ---

User question: {query}

Provide a clear, specific answer. Reference which resume(s) you're citing."""

    # 4. Generate answer
    answer = await ollama_svc.generate(prompt, system=SYSTEM_PROMPT)

    return {
        "answer": answer.strip(),
        "sources": [
            {
                "filename": c["filename"],
                "doc_type": c["doc_type"],
                "relevance": c["relevance"],
                "excerpt": c["chunk_text"][:150] + "..." if len(c["chunk_text"]) > 150 else c["chunk_text"],
            }
            for c in chunks
        ],
    }


JOB_MATCH_SYSTEM = """You are an Expert Hiring Manager. Given a job description and resume excerpts,
provide a detailed analysis of how well the candidate matches. Include:
1. Overall match assessment (Strong/Good/Weak)
2. Key strengths that align with the role
3. Critical gaps that need addressing
4. Specific action items to improve the resume for this role
Be honest and specific."""


async def match_job(job_description: str, db: Session, top_k: int = 8) -> dict:
    """
    Job matching: embed job desc → retrieve relevant resume chunks → analyze fit.

    Returns: {"analysis": str, "best_resumes": list, "sources": list}
    """
    # 1. Retrieve chunks most similar to the job description
    chunks = await search_similar_chunks(job_description, db, top_k=top_k)

    if not chunks:
        return {
            "analysis": "No resume data available. Please generate embeddings first.",
            "best_resumes": [],
            "sources": [],
        }

    # Identify unique resumes that matched
    resume_map = {}
    for c in chunks:
        if c["filename"] not in resume_map:
            resume_map[c["filename"]] = {
                "filename": c["filename"],
                "doc_type": c["doc_type"],
                "avg_relevance": 0,
                "chunk_count": 0,
            }
        resume_map[c["filename"]]["avg_relevance"] += c["relevance"]
        resume_map[c["filename"]]["chunk_count"] += 1

    for info in resume_map.values():
        info["avg_relevance"] = round(info["avg_relevance"] / info["chunk_count"], 3)

    best_resumes = sorted(resume_map.values(), key=lambda x: x["avg_relevance"], reverse=True)

    # 2. Build context
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[{chunk['filename']}]\n{chunk['chunk_text']}\n"
        )
    context = "\n".join(context_parts)

    # 3. Generate analysis
    prompt = f"""Analyze how well this candidate's resume matches the following job description.

--- JOB DESCRIPTION ---
{job_description[:2000]}
--- END JOB DESCRIPTION ---

--- CANDIDATE'S RESUME EXCERPTS ---
{context}
--- END RESUME EXCERPTS ---

Provide:
1. Overall match assessment
2. Key strengths for this role
3. Critical gaps
4. Action items to tailor the resume"""

    analysis = await ollama_svc.generate(prompt, system=JOB_MATCH_SYSTEM, temperature=0.4)

    return {
        "analysis": analysis.strip(),
        "best_resumes": best_resumes[:5],
        "sources": [
            {
                "filename": c["filename"],
                "relevance": c["relevance"],
                "excerpt": c["chunk_text"][:120] + "...",
            }
            for c in chunks
        ],
    }
