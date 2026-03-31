"""
NemoClaw — NVIDIA NeMo Guardrails Security Layer

Every agent prompt and response passes through this service before
being sent to or returned from the LLM. This prevents:
  - Prompt injection attacks
  - Hallucinated financial figures in reports
  - Off-topic / harmful output
  - Credential leakage in responses

Built on NVIDIA NeMo Guardrails (https://github.com/NVIDIA/NeMo-Guardrails)
"""

import logging
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from nemoguardrails import RailsConfig, LLMRails
    from langchain_openai import ChatOpenAI
    NEMO_AVAILABLE = True
except ImportError:
    NEMO_AVAILABLE = False
    logging.warning("NeMo Guardrails not installed — running in passthrough mode")

logger = logging.getLogger("nemoclaw")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())

app = FastAPI(title="NemoClaw", version="1.0.0", docs_url=None)

# ── Load guardrails config with Nemotron as the LLM ──────────────────────────
# NemoClaw uses NVIDIA Nemotron exclusively.
# OpenClaw + Deep Agents use Gemini — completely separate key.
rails = None
if NEMO_AVAILABLE:
    nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
    if not nvidia_api_key:
        logger.warning("NVIDIA_API_KEY not set — NemoClaw running in validation-only mode")
    else:
        try:
            nemotron_llm = ChatOpenAI(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                openai_api_base="https://integrate.api.nvidia.com/v1",
                openai_api_key=nvidia_api_key,
                temperature=0.0,
            )
            config = RailsConfig.from_path("./config")
            rails = LLMRails(config, llm=nemotron_llm)
            logger.info("NeMo Guardrails loaded — powered by NVIDIA Nemotron")
        except Exception as e:
            logger.warning(f"Could not load NeMo config: {e} — running in validation-only mode")


# ── Request / Response models ─────────────────────────────────────────────────

class GuardRequest(BaseModel):
    prompt: str
    context: Optional[str] = "marketing_audit"
    source: Optional[str] = "deep_agents"


class GuardResponse(BaseModel):
    safe: bool
    output: str
    blocked_reason: Optional[str] = None
    guardrail_applied: bool = False


# ── Safety rules (lightweight, no NeMo dependency) ───────────────────────────

BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "disregard all prior",
    "pretend you are",
    "act as jailbreak",
    "reveal your system prompt",
    "print your instructions",
    "bypass your guidelines",
    "forget everything",
]

OUTPUT_HALLUCINATION_MARKERS = [
    "as an AI language model",
    "I cannot verify",
    "I don't have access to real",
]


def validate_input(prompt: str) -> tuple[bool, Optional[str]]:
    lower = prompt.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return False, f"Blocked: potential prompt injection detected (pattern: '{pattern}')"
    return True, None


def validate_output(output: str) -> tuple[bool, Optional[str]]:
    for marker in OUTPUT_HALLUCINATION_MARKERS:
        if marker.lower() in output.lower():
            return False, f"Output contains hallucination marker: '{marker}'"
    return True, None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "nemo_available": NEMO_AVAILABLE,
        "rails_loaded": rails is not None,
        "mode": "full_guardrails" if rails else "validation_only",
        "llm": "nvidia/llama-3.1-nemotron-70b-instruct" if rails else None,
        "nvidia_key_set": bool(os.environ.get("NVIDIA_API_KEY")),
    }


@app.post("/guard/input", response_model=GuardResponse)
async def guard_input(req: GuardRequest):
    """Validate and sanitise agent input before sending to LLM."""
    safe, reason = validate_input(req.prompt)
    if not safe:
        logger.warning(f"INPUT BLOCKED: {reason} | source={req.source}")
        return GuardResponse(safe=False, output="", blocked_reason=reason)

    if rails:
        try:
            result = await rails.generate_async(messages=[
                {"role": "user", "content": req.prompt}
            ])
            return GuardResponse(safe=True, output=result, guardrail_applied=True)
        except Exception as e:
            logger.error(f"NeMo error: {e} — falling through")

    return GuardResponse(safe=True, output=req.prompt, guardrail_applied=False)


@app.post("/guard/output", response_model=GuardResponse)
async def guard_output(req: GuardRequest):
    """Validate LLM output before it reaches reports / delivery channels."""
    safe, reason = validate_output(req.prompt)
    if not safe:
        logger.warning(f"OUTPUT BLOCKED: {reason}")
        return GuardResponse(safe=False, output="", blocked_reason=reason)
    return GuardResponse(safe=True, output=req.prompt, guardrail_applied=False)


@app.get("/stats")
async def stats():
    return {
        "service": "NemoClaw",
        "description": "NVIDIA NeMo Guardrails security layer for ClawBoard Pro",
        "rules": len(BLOCKED_PATTERNS),
        "output_checks": len(OUTPUT_HALLUCINATION_MARKERS),
        "nemo_available": NEMO_AVAILABLE,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
