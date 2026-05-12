"""
TailorTalk Backend — FastAPI
Exposes a /chat endpoint consumed by the Streamlit frontend.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up the agent on startup so the first request isn't slow."""
    logger.info("Warming up LangChain agent …")
    try:
        from agent import _get_llm_with_tools
        _get_llm_with_tools()
        logger.info("Agent ready.")
    except Exception as e:
        logger.error("Agent warm-up failed: %s", e)
    yield


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TailorTalk Drive Agent API",
    version="1.0.0",
    description="Conversational AI agent for Google Drive file discovery.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class Turn(BaseModel):
    role: str        # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Turn] = []


class ChatResponse(BaseModel):
    reply: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Send a message to the Drive agent and get a reply.

    Body:
        message  - The user's latest message.
        history  - Prior conversation turns (role + content).

    Returns:
        reply    - The agent's response string.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    history = [{"role": t.role, "content": t.content} for t in req.history]

    try:
        from agent import chat
        reply = chat(user_message=req.message, history=history)
    except Exception as e:
        logger.exception("Agent error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(reply=reply)
