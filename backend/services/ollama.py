"""
Ollama client — HTTP wrapper for the local Ollama API.

Handles both text generation (chat) and embeddings.
"""

import httpx
from backend.config import settings

OLLAMA_BASE = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
EMBED_MODEL = "nomic-embed-text"

# Timeout: generation can be slow on CPU
TIMEOUT = httpx.Timeout(120.0, connect=10.0)


async def generate(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    """Generate a text response from Ollama."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 1024},
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]


async def generate_stream(prompt: str, system: str = "", temperature: float = 0.3):
    """Stream a text response from Ollama, yielding chunks."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": 1024},
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/generate", json=payload) as resp:
            resp.raise_for_status()
            import json
            async for line in resp.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done"):
                        break


async def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using nomic-embed-text."""
    results = []
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for text in texts:
            resp = await client.post(
                f"{OLLAMA_BASE}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            results.append(resp.json()["embedding"])
    return results


async def embed_single(text: str) -> list[float]:
    """Generate embedding for a single text."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


def is_ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        resp = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False
