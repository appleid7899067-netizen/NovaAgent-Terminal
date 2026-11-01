"""Authenticated, bounded Expert API routes."""

import logging
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from .orchestrator import ExpertOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/expert", tags=["Expert"])
orchestrator = ExpertOrchestrator()


class CodeInput(BaseModel):
    code: str = Field(min_length=1, max_length=200_000)
    language: str = Field(default="python", min_length=1, max_length=64)


def _expert_token() -> str:
    return os.environ.get("EXPERT_API_TOKEN", "").strip()


def require_expert_auth(authorization: str | None = Header(default=None)) -> None:
    """Require an explicitly configured bearer token; fail closed by default."""
    expected = _expert_token()
    if not expected or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    supplied = authorization[7:].strip()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/review", dependencies=[Depends(require_expert_auth)])
def review_code(input: CodeInput):
    try:
        result = orchestrator.review_code(input.code, input.language)
        return {"status": "success", "data": result.model_dump()}
    except Exception:
        logger.exception("Expert review failed")
        raise HTTPException(status_code=502, detail="Expert review unavailable")


@router.get("/health")
def health_check():
    # Health is intentionally non-sensitive and suitable for a local supervisor.
    return {"status": "ok", "service": "expert-orchestrator"}
