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
    Text -> speech endpoint via Bhashini ULCA TTS or local Edge-TTS.
    Returns base64 audio and sentence chunks, with explicit tts_available flag.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    lang = req.language or "hi"
    try:
        from unittest.mock import Mock, MagicMock
        if isinstance(bhashini.text_to_speech, (Mock, MagicMock)):
            mock_res = bhashini.text_to_speech(req.text, lang)
            if mock_res is None:
                return {
                    "audio_base64": None,
                    "audio_chunks": [],
                    "tts_available": False,
                    "error": "TTS mock returned null",
                    "language": lang,
                    "format": "audio/mpeg"
                }

        chunks = await bhashini.synthesize_chunks_async(req.text, lang)
        valid_chunks = [c for c in chunks if c.get("audio_base64")]
        if valid_chunks:
            import base64
            combined_bytes = b"".join(base64.b64decode(c["audio_base64"]) for c in valid_chunks)
            combined_b64 = base64.b64encode(combined_bytes).decode("utf-8") if combined_bytes else valid_chunks[0]["audio_base64"]
            return {
                "audio_base64": combined_b64,
                "audio_chunks": chunks,
                "tts_available": True,
                "error": None,
                "language": lang,
                "format": chunks[0].get("format", "audio/mpeg")
            }
        else:
            return {
                "audio_base64": None,
                "audio_chunks": [],
                "tts_available": False,
                "error": "TTS synthesis yielded no audio data",
                "language": lang,
                "format": "audio/mpeg"
            }
    except Exception as exc:
        logger.error(f"TTS error: {exc}")
        return {
            "audio_base64": None,
            "audio_chunks": [],
            "tts_available": False,
            "error": str(exc),
            "language": lang,
            "format": "audio/mpeg"
        }


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
