"""
Multi-Provider LLM Profile Extraction (Claude & Gemini).
Extracts structured livelihood signals from free-form multi-turn conversational transcripts.
Supports:
  - Anthropic Claude (via ANTHROPIC_API_KEY)
  - Google Gemini (via GEMINI_API_KEY)
  - Automatic fallback to deterministic rules when no keys are provided or on network error.
"""
import os
import json
import re
import logging
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("llm_extractor")

EXTRACTION_SYSTEM_PROMPT = """You extract a livelihood profile from a beneficiary's spoken, free-form
story about their life. They will NOT use structured terms — infer meaning
from context, dialect, and indirect phrasing (e.g. "I help my father fix
fans and switches" implies occupation/interest = electrical work).

Return ONLY a JSON object, no other text or explanation. Use null
for anything not yet mentioned or not confidently inferable — never guess:

{
  "name": string|null,        // beneficiary name if stated, else null
  "education": string|null,   // e.g. "8th Standard", "10th Standard", "12th Standard", "Graduate", "No Formal Education"
  "occupation": string|null,  // current or family's traditional work (e.g., "Tailoring / Weaving", "Agriculture & Farming", "Daily Wage Labor")
  "interests": string|null,   // what trade they want to learn or pursue (e.g., "Food Processing", "Tailoring", "Solar PV", "Two-Wheeler & EV Maintenance")
  "skills": string|null,      // comma-separated specific technical, vocational, traditional, or soft skills mentioned
  "mobility": string|null,    // "Cannot travel far (Restricted to village/cluster)" or "Willing to commute to District/Taluka center" or "Willing to relocate"
  "preference": string|null,  // "self_employment" or "wage_employment"
  "state": string|null        // Indian state if mentioned (e.g. "Delhi", "Maharashtra", "Tamil Nadu", "Karnataka", "Uttar Pradesh")
}"""


def call_groq(system_prompt: str, user_message: str) -> str:
    """Calls Groq OpenAI-compatible Chat Completions API (Free tier)."""
    api_key = os.getenv("GROQ_API_KEY", "")
    api_key = api_key.replace("GROQ_API_KEY=", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("No response choice returned by Groq API")
    return choices[0].get("message", {}).get("content", "")


def call_anthropic(system_prompt: str, user_message: str) -> str:
    """Calls Anthropic Claude Messages API."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    api_key = api_key.replace("ANTHROPIC_API_KEY=", "").strip()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    payload = {
        "model": model,
        "max_tokens": 600,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []))


def call_gemini(system_prompt: str, user_message: str) -> str:
    """Calls Google Gemini REST API (Free tier on Google AI Studio)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    api_key = api_key.replace("GEMINI_API_KEY=", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json"
        }
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No candidate returned by Gemini API")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def has_llm_provider() -> bool:
    """Returns True if Groq, Gemini, or Anthropic API key is configured."""
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


def extract_profile_with_llm(full_transcript: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured beneficiary profile using an LLM.
    Prioritizes free, low-latency providers (Groq, Gemini) before paid fallbacks.
    Returns None if no LLM key is set or if extraction fails, allowing graceful rule-based fallback.
    """
    if not has_llm_provider():
        return None

    user_prompt = f'Beneficiary\'s story so far:\n"""\n{full_transcript}\n"""'
    raw_output = None

    # 1. Try Groq first (Free tier, ultra-fast Llama 3.3 70B / 3.1 8B)
    if os.getenv("GROQ_API_KEY"):
        try:
            raw_output = call_groq(EXTRACTION_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}. Trying Gemini or Claude if available.")

    # 2. Try Google Gemini (Free tier on Google AI Studio)
    if not raw_output and os.getenv("GEMINI_API_KEY"):
        try:
            raw_output = call_gemini(EXTRACTION_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Trying Claude if available.")

    # 3. Fallback to Anthropic Claude if configured
    if not raw_output and os.getenv("ANTHROPIC_API_KEY"):
        try:
            raw_output = call_anthropic(EXTRACTION_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"Claude API call failed: {e}")

    if not raw_output:
        return None

    # Clean JSON
    cleaned = raw_output.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON: {e}, raw: {raw_output}")
        return None

    # Transform into internal Nivara canonical profile structure
    profile: Dict[str, Any] = {}
    if parsed.get("name"):
        profile["name"] = str(parsed["name"]).strip()
    if parsed.get("education"):
        profile["education"] = str(parsed["education"]).strip()
        profile["education_level"] = str(parsed["education"]).strip()
    if parsed.get("occupation"):
        profile["family_occupation"] = str(parsed["occupation"]).strip()
    if parsed.get("interests"):
        val = parsed["interests"]
        profile["interests"] = [val] if isinstance(val, str) else list(val)
    if parsed.get("skills"):
        s_val = parsed["skills"]
        if isinstance(s_val, str):
            profile["skills"] = [s.strip() for s in s_val.split(",") if s.strip()]
        elif isinstance(s_val, list):
            profile["skills"] = s_val
    if parsed.get("mobility"):
        profile["mobility"] = str(parsed["mobility"]).strip()
        profile["mobility_constraint"] = str(parsed["mobility"]).strip()
    if parsed.get("preference"):
        pref = str(parsed["preference"]).lower()
        if "self" in pref:
            profile["employment_preference"] = "self_employment"
        elif "wage" in pref or "job" in pref or "salary" in pref:
            profile["employment_preference"] = "wage_employment"
        else:
            profile["employment_preference"] = parsed["preference"]
    if parsed.get("state"):
        profile["state"] = str(parsed["state"]).strip()
        profile["location"] = str(parsed["state"]).strip()

    return profile
