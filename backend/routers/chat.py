"""
Chat API — RAG-powered Q&A over resume portfolio.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage
from backend.services.rag import chat as rag_chat
from backend.services.ollama import is_ollama_available

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


@router.get("/status")
def chat_status():
    """Check if Ollama is available for chat."""
    available = is_ollama_available()
    return {"available": available, "message": "Ollama is running" if available else "Ollama not available — start it with 'ollama serve'"}


@router.post("", response_model=ChatResponse)
async def send_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get a RAG-powered response."""
    if not is_ollama_available():
        return ChatResponse(
            answer="Ollama is not running. Please start it with 'ollama serve' and try again.",
            sources=[],
        )

    # Save user message
    db.add(ChatMessage(role="user", content=req.message))
    db.commit()

    # RAG pipeline
    result = await rag_chat(req.message, db)

    # Save assistant response
    db.add(ChatMessage(
        role="assistant",
        content=result["answer"],
        context_chunks=[s["filename"] for s in result["sources"]],
    ))
    db.commit()

    return ChatResponse(**result)


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent chat history."""
    messages = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.context_chunks or [],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in reversed(messages)
    ]
