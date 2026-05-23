"""
FastAPI Backend — exposes /analyze endpoint for IDE extensions and web UI.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.parsers.error_parser import ErrorParser
from src.ai.llm_client import LLMClient
from src.core.config import Config

app = FastAPI(
    title="AI Terminal Debug Assistant",
    description="REST API for AI-powered error debugging",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = ErrorParser()


# ── Request/Response Models ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    error_text: str
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4o-mini"

class FixCommand(BaseModel):
    command: str
    explanation: str

class Reference(BaseModel):
    title: str
    url: str

class AnalyzeResponse(BaseModel):
    language: str
    error_type: str
    severity: str
    explanation: str
    root_cause: str
    fix_commands: list[FixCommand]
    prevention: str
    references: list[Reference]


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "DebugAI API is running 🤖", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Analyze an error and return AI-powered explanation + fixes."""
    try:
        config = Config(provider=req.provider, model=req.model)
        parsed = parser.parse(req.error_text)
        llm = LLMClient(config)
        result = llm.analyze(req.error_text, parsed)

        return AnalyzeResponse(
            language=parsed.get("language", "Unknown"),
            error_type=parsed.get("error_type", "Unknown"),
            severity=parsed.get("severity", "medium"),
            explanation=result.get("explanation", ""),
            root_cause=result.get("root_cause", ""),
            fix_commands=[
                FixCommand(
                    command=f.get("command", ""),
                    explanation=f.get("explanation", ""),
                )
                for f in result.get("fix_commands", [])
            ],
            prevention=result.get("prevention", ""),
            references=[
                Reference(title=r.get("title", ""), url=r.get("url", ""))
                for r in result.get("references", [])
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse")
async def parse_only(req: AnalyzeRequest):
    """Parse error without calling AI — useful for quick classification."""
    parsed = parser.parse(req.error_text)
    return parsed


def start():
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
