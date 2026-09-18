"""
Resume Intelligence Dashboard v2 — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import create_tables, get_db
from backend.routers import resumes, roles, chat, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables. Shutdown: nothing special."""
    print("\n  Resume Intelligence v2")
    print("  Initializing database...\n")
    create_tables()
    print("\n  Ready! API docs at http://localhost:8000/docs\n")
    yield


app = FastAPI(
    title="Resume Intelligence API",
    description="Expert Hiring Manager — analyze resumes against target roles",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(resumes.router)
app.include_router(roles.router)
app.include_router(chat.router)
app.include_router(jobs.router)


@app.get("/api/health")
def health():
    from backend.services.ollama import is_ollama_available
    return {
        "status": "ok",
        "version": "2.0.0",
        "ollama": is_ollama_available(),
    }


@app.post("/api/embeddings/generate")
async def generate_embeddings(db: Session = Depends(get_db)):
    """Generate vector embeddings for all resumes (run once after seeding)."""
    from backend.services.embeddings import embed_all_resumes
    result = await embed_all_resumes(db)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
