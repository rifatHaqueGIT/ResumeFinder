"""
Resume Intelligence Dashboard v2 — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_tables
from backend.routers import resumes, roles


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


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
