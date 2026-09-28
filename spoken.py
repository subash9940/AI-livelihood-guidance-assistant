"""
Spoken Explanation Generator for Nivara — AI Livelihood Guidance Assistant.
Generates Siri-style, natural spoken audio summaries for livelihood recommendations.
Adheres strictly to PS 26097 guidelines: personalized, grounded only in beneficiary facts,
strictly plain spoken text, max 3 short sentences (~300 characters), supporting en, hi, ta, mr, pa.
"""
import os
import re
import hashlib
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("spoken")

# In-memory session / profile hash cache to prevent redundant LLM invocations
_EXPLANATION_CACHE: Dict[str, str] = {}


def clear_cache():
    """Clears the explanation cache (useful for testing)."""
    _EXPLANATION_CACHE.clear()


TRADE_NAMES = {
    "food_processing": {
        "en": "Food Processing & Agri-Value Addition Technician",
        "hi": "खाद्य प्रसंस्करण एवं कृषि मूल्य संवर्धन तकनीशियन",
        "mr": "अन्न प्रक्रिया व कृषी मूल्यवर्धन तंत्रज्ञ",
        "pa": "ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਅਤੇ ਖੇਤੀ ਮੁੱਲ ਵਾਧਾ ਤਕਨੀਸ਼ੀਅਨ",
        "ta": "உணவு பதப்படுத்துதல் தொழில்நுட்ப வல்லுநர்"
    },
    "apparel_tailoring": {
        "en": "Self-Employed Tailor & Apparel Specialist",
        "hi": "स्व-रोजगार दर्जी एवं परिधान विशेषज्ञ",
        "mr": "स्वयंरोजगार टेलर व वस्त्र निर्मिती तज्ज्ञ",
        "pa": "ਸਵੈ-ਰੋਜ਼ਗਾਰ ਟੇਲਰ ਅਤੇ ਕੱਪੜਾ ਮਾਹਰ",
        "ta": "சுயதொழில் தையல் கலைஞர்"
    },
    "solar_technician": {
        "en": "Solar PV Installer (Suryamitra)",
        "hi": "सोलर पीवी इंस्टॉलर (सूर्यमित्र)",
        "mr": "सोलर पीव्ही इंस्टॉलर (सूर्यमित्र)",
        "pa": "ਸੋਲਰ ਪੀਵੀ ਇੰਸਟਾਲਰ (ਸੂਰਿਆਮਿੱਤਰ)",
        "ta": "சூரிய மின்சக்தி நிறுவுநர் (சூரியமித்ரா)"
    },
    "automotive_ev": {
        "en": "Two-Wheeler & EV Service Technician",
        "hi": "टू-व्हीलर एवं ईवी सर्विस तकनीशियन",
        "mr": "दुचाकी व ईव्ही सर्व्हिस तंत्रज्ञ",
        "pa": "ਟੂ-ਵ੍ਹੀਲਰ ਅਤੇ ਈਵੀ ਸਰਵਿਸ ਤਕਨੀਸ਼ੀਅਨ",
        "ta": "இருசக்கர வாகனம் மற்றும் மின்சார வாகன சர்வீஸ் டெக்னீசியன்"
    },
    "digital_csc": {
        "en": "Digital Services Operator & CSC Citizen Facilitator",
        "hi": "डिजिटल सेवा ऑपरेटर एवं सीएससी नागरिक सहायक",
        "mr": "डिजिटल सेवा ऑपरेटर व सीएससी नागरिक सहाय्यक",
        "pa": "ਡਿਜੀਟਲ ਸੇਵਾ ਆਪਰੇਟਰ ਅਤੇ ਸੀਐਸਸੀ ਸਹਾਇਕ",
        "ta": "டிஜிட்டல் சேவை ஆபரேட்டர் மற்றும் சி.எஸ்.சி உதவியாளர்"
    }
}


def _extract_reason(profile: dict, lang: str) -> str:
    """Extracts a single concrete reason grounded strictly in facts the beneficiary provided."""
    skills = profile.get("skills") or []
    interests = profile.get("interests") or []
    fam_occ = (profile.get("family_occupation") or "").strip()
    edu = (profile.get("education_level") or profile.get("education") or "").strip()
    mobility = (profile.get("mobility_constraint") or profile.get("mobility") or "").strip()

    # Prioritize specific candidate skills and interests over general family background
    direct_signals = " ".join([str(s) for s in skills] + [str(i) for i in interests]).lower()
    combined = (direct_signals + " " + fam_occ + " " + edu + " " + mobility).lower()

    for search_pool in [direct_signals, combined]:
        if not search_pool.strip():
            continue

        if any(k in search_pool for k in ["solar", "electric", "wiring", "pv", "sun"]):
            return {
                "en": "practical knowledge of electrical wiring and solar safety",
                "hi": "बिजली वायरिंग और सौर ऊर्जा ज्ञान",
                "ta": "மின் வயரிங் மற்றும் சூரிய மின்சக்தி அறிவின்",
                "mr": "विद्युत वायरिंग व सौर ऊर्जा कौशल्यांच्या",
                "pa": "ਬਿਜਲੀ ਵਾਇਰਿੰਗ ਅਤੇ ਸੋਲਰ ਊਰਜਾ ਗਿਆਨ"
            }.get(lang, "practical knowledge of electrical wiring and solar safety")

        if any(k in search_pool for k in ["stitch", "tailor", "sew", "cutting", "garment"]):
            return {
                "en": "experience in garment stitching",
                "hi": "सिलाई और कटिंग के अनुभव",
                "ta": "தையல் மற்றும் ஆடை வடிவமைப்பு அனுபவத்தின்",
                "mr": "शिलाई कामाच्या अनुभवाच्या",
                "pa": "ਸਿਲਾਈ ਅਤੇ ਕਟਾਈ ਦੇ ਤਜਰਬੇ"
            }.get(lang, "experience in garment stitching")

        if any(k in search_pool for k in ["mechanic", "vehicle", "two-wheeler", "bike", "ev", "hand tools"]):
            return {
                "en": "hands-on skills with mechanical tools",
                "hi": "मैकेनिकल और वाहन मरम्मत के कौशल",
                "ta": "இயந்திர கருவிகள் மற்றும் வாகன பழுதுபார்ப்பு திறன்களின்",
                "mr": "मेकॅनिकल व वाहन दुरुस्ती कौशल्यांच्या",
                "pa": "ਮਕੈਨੀਕਲ ਅਤੇ ਵਾਹਨ ਮੁਰੰਮਤ ਦੇ ਹੁਨਰ"
            }.get(lang, "hands-on skills with mechanical tools")

        if any(k in search_pool for k in ["food", "preserv", "pickle", "crop", "agri", "farming"]):
            return {
                "en": "skills in agricultural and food processing",
                "hi": "खाद्य प्रसंस्करण और कृषि कौशल",
                "ta": "உணவு பதப்படுத்துதல் திறன்களின்",
                "mr": "अन्न प्रक्रिया व कृषी कौशल्यांच्या",
                "pa": "ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਅਤੇ ਖੇਤੀ ਹੁਨਰ"
            }.get(lang, "skills in agricultural and food processing")

        if any(k in search_pool for k in ["computer", "digital", "data", "csc"]):
            return {
                "en": "digital and computer skills",
                "hi": "कंप्यूटर और डिजिटल कौशल",
                "ta": "கணினி மற்றும் டிஜிட்டல் திறன்களின்",
                "mr": "संगणक व डिजिटल कौशल्यांच्या",
                "pa": "ਕੰਪਿਊਟਰ ਅਤੇ ਡਿਜੀਟਲ ਹੁਨਰ"
            }.get(lang, "digital and computer skills")

    # Specific slot fallbacks
    if skills:
        s0 = str(skills[0])
        return {
            "en": f"experience in {s0}",
            "hi": f"{s0} के अनुभव",
            "ta": f"{s0} அனுபவத்தின்",
            "mr": f"{s0} अनुभवाच्या",
            "pa": f"{s0} ਦੇ ਤਜਰਬੇ"
        }.get(lang, f"experience in {s0}")

    if interests:
        i0 = str(interests[0])
        return {
            "en": f"interest in {i0}",
            "hi": f"{i0} में रुचि",
            "ta": f"{i0} மீதான ஆர்வத்தின்",
            "mr": f"{i0} मधील आवडीच्या",
            "pa": f"{i0} ਵਿੱਚ ਰੁਚੀ"
        }.get(lang, f"interest in {i0}")

    if edu:
        return {
            "en": f"{edu} educational background",
            "hi": f"{edu} शिक्षा",
            "ta": f"{edu} கல்வி பின்னணியின்",
            "mr": f"{edu} शिक्षणाच्या",
            "pa": f"{edu} ਪੜ੍ਹਾਈ"
        }.get(lang, f"{edu} educational background")

    return {
        "en": "background and preferences",
        "hi": "अनुभव और प्राथमिकताओं",
        "ta": "பின்னணி மற்றும் விருப்பங்களின்",
        "mr": "अनुभव आणि आवडींच्या",
        "pa": "ਤਜਰਬੇ ਅਤੇ ਰੁਚੀਆਂ"
    }.get(lang, "background and preferences")


def _build_template_explanation(name: Optional[str], trade: str, reason: str, centre: str, lang: str) -> str:
    """Builds a grammatical 3-sentence fallback template in the target language."""
    lang = lang if lang in ["en", "hi", "ta", "mr", "pa"] else "en"

    if lang == "hi":
        if name:
            return f"{name}, आपके {reason} को देखते हुए, आपके लिए सबसे सही विकल्प {trade} है। आप {centre} में निःशुल्क प्रशिक्षण ले सकते हैं। क्या आप अन्य विकल्प भी सुनना चाहते हैं?"
        return f"आपके {reason} को देखते हुए, आपके लिए सबसे सही विकल्प {trade} है। आप {centre} में निःशुल्क प्रशिक्षण ले सकते हैं। क्या आप अन्य विकल्प भी सुनना चाहते हैं?"

    elif lang == "ta":
        if name:
            return f"{name}, உங்கள் {reason} அடிப்படையில், உங்களுக்கு சிறந்த தேர்வு {trade} ஆகும். நீங்கள் {centre} இல் இலவச பயிற்சியில் சேரலாம். மற்ற விருப்பங்களை நான் கூறவா?"
        return f"உங்கள் {reason} அடிப்படையில், உங்களுக்கு சிறந்த தேர்வு {trade} ஆகும். நீங்கள் {centre} இல் இலவச பயிற்சியில் சேரலாம். மற்ற விருப்பங்களை நான் கூறவா?"

    elif lang == "mr":
        if name:
            return f"{name}, तुमच्या {reason} आधारावर तुमच्यासाठी सर्वोत्तम पर्याय {trade} आहे. तुम्ही {centre} येथे मोफत प्रशिक्षण घेऊ शकता. मी इतर पर्याय सांगू का?"
        return f"तुमच्या {reason} आधारावर तुमच्यासाठी सर्वोत्तम पर्याय {trade} आहे. तुम्ही {centre} येथे मोफत प्रशिक्षण घेऊ शकता. मी इतर पर्याय सांगू का?"

    elif lang == "pa":
        if name:
            return f"{name}, ਤੁਹਾਡੇ {reason} ਦੇ ਆਧਾਰ 'ਤੇ ਤੁਹਾਡੇ ਲਈ ਸਭ ਤੋਂ ਵਧੀਆ ਕੰਮ {trade} ਹੈ। ਤੁਸੀਂ {centre} ਵਿਖੇ ਮੁਫ਼ਤ ਸਿਖਲਾਈ ਲੈ ਸਕਦੇ ਹੋ। ਕੀ ਤੁਸੀਂ ਹੋਰ ਵਿਕਲਪ ਸੁਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?"
        return f"ਤੁਹਾਡੇ {reason} ਦੇ ਆਧਾਰ 'ਤੇ ਤੁਹਾਡੇ ਲਈ ਸਭ ਤੋਂ ਵਧੀਆ ਕੰਮ {trade} ਹੈ। ਤੁਸੀਂ {centre} ਵਿਖੇ ਮੁਫ਼ਤ ਸਿਖਲਾਈ ਲੈ ਸਕਦੇ ਹੋ। ਕੀ ਤੁਸੀਂ ਹੋਰ ਵਿਕਲਪ ਸੁਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?"

    else:  # en default
        if name:
            return f"{name}, based on your {reason}, the best path for you is {trade}. You can join free training at {centre}. Want me to go through the other options?"
        return f"Based on your {reason}, the best path for you is {trade}. You can join free training at {centre}. Want me to go through the other options?"


def _clean_spoken_text(text: str) -> str:
    """Strips markdown, emojis, QP codes, and excessive whitespace."""
    if not text:
        return ""
    # Strip markdown symbols: * # _ ` ~ [ ]
    cleaned = re.sub(r'[*#_`~\[\]]', '', text)
    # Strip emojis (high unicode astral planes)
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    # Strip QP codes if hallucinated, e.g. AMH/Q1947 or FIC/Q0102
    cleaned = re.sub(r'\b[A-Z]{2,4}/Q\d{4}\b', '', cleaned)
    cleaned = re.sub(r'QP\s*Code[:\s]*[A-Z0-9/]+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'NSQF\s*Level\s*\d+', '', cleaned, flags=re.IGNORECASE)
    # Strip leading/trailing quotation marks
    cleaned = re.sub(r'^["\']+|["\']+$', '', cleaned)
    # Normalize whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _count_sentences(text: str) -> int:
    """Counts sentences split by standard punctuation including Devanagari danda."""
    t = text.strip()
    t = re.sub(r'[।!?]', '.', t)
    parts = [s.strip() for s in re.split(r'\.\s+|\.$', t) if s.strip()]
    return len(parts)


def _is_valid_spoken_explanation(text: str, trade_name: str) -> bool:
    """Validates that output satisfies the Siri-style spoken explanation constraints."""
    if not text or len(text.strip()) == 0:
        return False
    if len(text) > 400:
        return False
    if any(c in text for c in "*#_[]"):
        return False
    # Ensure <= 3 sentences
    s_count = _count_sentences(text)
    if s_count > 3 or s_count == 0:
        return False
    # Ensure trade tokens are present in generated text
    if trade_name:
        trade_tokens = [tok for tok in re.split(r"[\s&,-/()]+", trade_name) if len(tok) >= 3]
        if trade_tokens and not any(tok.lower() in text.lower() for tok in trade_tokens):
            return False
    return True


def _call_groq_text(system_prompt: str, user_message: str, timeout: float = 4.0) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").replace("GROQ_API_KEY=", "").strip()
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
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("No response choice returned by Groq API")
    return choices[0].get("message", {}).get("content", "")


def _call_gemini_text(system_prompt: str, user_message: str, timeout: float = 4.0) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").replace("GEMINI_API_KEY=", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 300,
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No candidate returned by Gemini API")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def _call_llm(system_prompt: str, user_message: str, timeout: float = 4.0) -> Optional[str]:
    """Calls Groq or Gemini with 4s timeout. Returns text or raises/returns None."""
    if os.getenv("GROQ_API_KEY"):
        try:
            return _call_groq_text(system_prompt, user_message, timeout=timeout)
        except Exception as e:
            logger.warning(f"Groq spoken explanation error: {e}. Trying Gemini if available.")

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _call_gemini_text(system_prompt, user_message, timeout=timeout)
        except Exception as e:
            logger.warning(f"Gemini spoken explanation error: {e}")

    return None


def _make_cache_key(profile: dict, rec: dict, lang: str, session_id: Optional[str] = None) -> str:
    if session_id:
        return f"{session_id}:{lang}"
    name = str(profile.get("name", "")).strip()
    trade = str(rec.get("trade_key") or rec.get("recommended_trade") or "")
    skills = str(profile.get("skills", ""))
    interests = str(profile.get("interests", ""))
    edu = str(profile.get("education_level") or profile.get("education") or "")
    h = hashlib.sha256(f"{name}|{trade}|{skills}|{interests}|{edu}|{lang}".encode("utf-8")).hexdigest()
    return f"{h}:{lang}"


def build_spoken_explanation(
    profile: Dict[str, Any],
    rec: Dict[str, Any],
    lang: str = "en",
    session_id: Optional[str] = None
) -> str:
    """
    Builds a Siri-style spoken explanation of the livelihood recommendation.
    Returns plain text, max 3 short sentences, ~300 characters max, in session language (en, hi, ta, mr, pa).
    Never raises an exception under any circumstance.
    """
    try:
        if not rec:
            return ""

        # Gated / clarification path: return clarifying question directly
        if rec.get("needs_more_info"):
            return rec.get("clarifying_question") or rec.get("detail") or "Please provide more details."

        lang = (lang or "en").lower().strip()
        if lang not in ["en", "hi", "ta", "mr", "pa"]:
            lang = "en"

        cache_key = _make_cache_key(profile, rec, lang, session_id)
        if cache_key in _EXPLANATION_CACHE:
            return _EXPLANATION_CACHE[cache_key]

        name = (profile.get("name") or "").strip()
        if name.lower() in ["beneficiary", "candidate", "none", "null", ""]:
            name = None

        trade_key = rec.get("trade_key") or ""
        if trade_key in TRADE_NAMES and lang in TRADE_NAMES[trade_key]:
            trade = TRADE_NAMES[trade_key][lang]
        else:
            trade = rec.get("recommended_trade") or "PM-AJAY Vocational Trade"

        reason = _extract_reason(profile, lang)
        centre = (rec.get("training_centre") or "").strip()
        if not centre or "pending" in centre.lower():
            centre = {
                "en": "your local district skill center",
                "hi": "जिला कौशल केंद्र",
                "ta": "மாவட்ட திறன் மையம்",
                "mr": "जिल्हा कौशल्य केंद्र",
                "pa": "ਜ਼ਿਲ੍ਹਾ ਹੁਨਰ ਕੇਂਦਰ"
            }.get(lang, "your local district skill center")

        # 1. Attempt LLM generation if configured
        llm_text = None
        has_key = bool(os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY"))
        if has_key:
            try:
                lang_names = {
                    "en": "English",
                    "hi": "Hindi",
                    "ta": "Tamil",
                    "mr": "Marathi",
                    "pa": "Punjabi"
                }
                lang_name = lang_names.get(lang, "English")
                sys_prompt = (
                    f"You are Nivara, a spoken livelihood guidance assistant. "
                    f"Reply ONLY in {lang_name}. Output exactly 3 short spoken sentences, natural speech, "
                    f"no lists, no markdown (*, #, _, []), no bullet points, no emojis, no QP codes, no NSQF level numbers. "
                    f"Maximum 300 characters total."
                )
                user_msg = (
                    f"Create a 3-sentence spoken livelihood explanation using only these facts:\n"
                    f"- Beneficiary Name: {name or 'Candidate'}\n"
                    f"- Recommended Trade: {trade}\n"
                    f"- Reason from background: {reason}\n"
                    f"- Nearest Training Centre: {centre}\n"
                    f"Must end with an offer asking if they want to go through other options."
                )
                raw = _call_llm(sys_prompt, user_msg, timeout=4.0)
                if raw:
                    cleaned = _clean_spoken_text(raw)
                    if _is_valid_spoken_explanation(cleaned, trade):
                        llm_text = cleaned
            except Exception as e:
                logger.warning(f"LLM explanation path failed: {e}. Falling back to template.")
                llm_text = None

        if llm_text:
            result = llm_text
        else:
            result = _build_template_explanation(name, trade, reason, centre, lang)

        # Final safety cleanup
        result = _clean_spoken_text(result)
        _EXPLANATION_CACHE[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"Unexpected error in build_spoken_explanation: {e}")
        return "Based on your preferences, we have generated your PM-AJAY livelihood pathway. You can join free skill training at your local center. Want me to go through the other options?"
