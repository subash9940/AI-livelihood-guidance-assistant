"""
FastAPI routes for Bhashini ASR/TTS and the conversational profiling engine.
Supports standalone Indic voice APIs and conversational triage loop.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

import bhashini
import profiler
import nsqf_rules
import llm_extractor

logger = logging.getLogger("voice_router")

router = APIRouter(tags=["Voice & Conversational Profiling"])


class ASRRequest(BaseModel):
    audio_base64: str
    language: Optional[str] = "hi"


class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "hi"


class ChatRequest(BaseModel):
    full_transcript: str
    language: Optional[str] = "en"


@router.post("/api/asr")
async def asr(req: ASRRequest):
    """
    Speech -> text endpoint via Bhashini ULCA ASR (or regional mock when MOCK_SPEECH=true).
    """
    try:
        transcript = bhashini.speech_to_text(req.audio_base64, req.language or "hi")
        return {"transcript": transcript, "language": req.language}
    except Exception as exc:
        logger.error(f"ASR error: {exc}")
        raise HTTPException(status_code=500, detail=f"ASR failed: {exc}")


@router.post("/api/tts")
async def tts(req: TTSRequest):
    """
    Text -> speech endpoint via Bhashini ULCA TTS.
    Returns base64 WAV string, or None in mock mode so client falls back to browser SpeechSynthesis.
    """
    try:
        audio_base64 = bhashini.text_to_speech(req.text, req.language or "hi")
        return {"audio_base64": audio_base64, "language": req.language}
    except Exception as exc:
        logger.error(f"TTS error: {exc}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")


@router.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Conversational profiling engine:
    Accepts full running transcript, extracts signals using free LLM APIs (Groq / Gemini)
    with rule-based fallback, asks missing questions, and generates NSQF recommendation when complete.
    """
    if not req.full_transcript or not req.full_transcript.strip():
        raise HTTPException(status_code=400, detail="full_transcript is required")

    lang = req.language or "en"
    transcript = req.full_transcript.strip()

    # 1. Profile extraction (Groq / Gemini free API or regex rules)
    profile, is_complete = profiler.extract_profile_from_text(transcript, {"language": lang})

    # Track missing canonical fields
    missing_fields = []
    if not profile.get("education") and not profile.get("education_level"):
        missing_fields.append("education")
    if not profile.get("family_occupation") and not profile.get("occupation"):
        missing_fields.append("occupation")
    if not profile.get("interests"):
        missing_fields.append("interests")
    if not profile.get("mobility") and not profile.get("mobility_constraint"):
        missing_fields.append("mobility")
    if not profile.get("employment_preference") and not profile.get("preference"):
        missing_fields.append("preference")

    done = is_complete and len(profile.get("interests", [])) > 0

    if done:
        # Full NSQF recommendation
        skill_res = nsqf_rules.analyze_skill_gap(profile)
        reply = (
            f"Thank you. Based on your background, {skill_res.get('gap_summary', '')} "
            f"I recommend: {skill_res['recommended_trade']} ({skill_res['nsqf_alignment']})."
        )
        return {
            "profile": profile,
            "missing": [],
            "done": True,
            "reply": reply,
            "recommendation": {
                "trade_name": skill_res["recommended_trade"],
                "nsqf_level": skill_res["nsqf_alignment"],
                "sector_skill_council": skill_res.get("sector_skill_council", "National Skill Development Council (NSDC)"),
                "explanation": skill_res.get("gap_summary", ""),
                "training_programme": skill_res.get("training_programme", ""),
                "training_centre": skill_res.get("training_centre", ""),
                "roadmap_steps": skill_res.get("roadmap_steps", []),
                "confidence_tier": "Direct Pathway Ready" if len(profile.get("skills", [])) > 0 else "Exploratory Track",
            }
        }

    # Generate next targeted question in the requested language
    next_question = profiler.generate_next_prompt(profile, language=lang)
    return {
        "profile": profile,
        "missing": missing_fields,
        "done": False,
        "reply": next_question,
    }
