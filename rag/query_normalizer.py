"""
rag/query_normalizer.py — Cross-Language Retrieval Normalizer for Nivara.
Solves TF-IDF token mismatch between Indic queries (Hindi, Tamil, etc.) and English KB:
1. Detects language from UI selection or Unicode script ranges.
2. Translates to English via:
   (a) LLM translation call with SQLite + in-memory cache.
   (b) Offline glossary term substitution fallback (data/glossary/intent_terms.json).
3. Provides helper to format scheme names with local-script name in brackets.
"""

import os
import re
import json
import sqlite3
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("query_normalizer")

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "livelihood.db")
GLOSSARY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "glossary", "intent_terms.json")

# In-memory cache
_TRANSLATION_MEM_CACHE: Dict[str, Dict[str, str]] = {}

# Script range regexes
SCRIPT_PATTERNS = {
    "hi": re.compile(r"[\u0900-\u097F]"),  # Devanagari (Hindi, Marathi)
    "pa": re.compile(r"[\u0A00-\u0A7F]"),  # Gurmukhi (Punjabi)
    "bn": re.compile(r"[\u0980-\u09FF]"),  # Bengali
    "ta": re.compile(r"[\u0B80-\u0BFF]"),  # Tamil
    "te": re.compile(r"[\u0C00-\u0C7F]"),  # Telugu
    "gu": re.compile(r"[\u0A80-\u0AFF]"),  # Gujarati
    "kn": re.compile(r"[\u0C80-\u0CFF]"),  # Kannada
    "ml": re.compile(r"[\u0D00-\u0D7F]"),  # Malayalam
    "ur": re.compile(r"[\u0600-\u06FF]"),  # Arabic / Urdu
    "en": re.compile(r"[a-zA-Z]"),          # Latin
}

# Scheme local name dictionary
SCHEME_LOCAL_NAMES: Dict[str, Dict[str, str]] = {
    "delhi-pmajay-gia": {
        "hi": "प्रधानमंत्री अनुसूचित जाति अभ्युदय योजना (पीएम-अजय)",
        "ta": "பிரதம மந்திரி அனுசூசித் ஜாதி அப்யுதய யோஜனா (பிஎம்-அஜய்)",
        "te": "ప్రధాన మంత్రి అనుసూచిత జాతి అభ్యుదయ యోజన",
        "mr": "पंतप्रधान अनुसूचित जाती अभ्युदय योजना",
        "pa": "ਪ੍ਰਧਾਨ ਮੰਤਰੀ ਅਨੁਸੂਚਿਤ ਜਾਤੀ ਅਭਿਉਦੈ ਯੋਜਨਾ"
    },
    "delhi-iti-electrician-sc": {
        "hi": "दिल्ली सरकारी आईटीआई इलेक्ट्रीशियन शिल्पकार प्रशिक्षण योजना",
        "ta": "டெல்லி அரசு ஐடிஐ எலக்ட்ரீஷியன் பயிற்சித் திட்டம்",
        "te": "ఢిల్లీ ప్రభుత్వ ఐటీఐ ఎలక్ట్రీషియన్ శిక్షణ పథకం"
    },
    "delhi-sc-skill-development": {
        "hi": "दिल्ली अनुसूचित जाति कौशल विकास एवं रोजगार प्रशिक्षण योजना",
        "ta": "டெல்லி எஸ்சி திறன் மேம்பாட்டுத் திட்டம்"
    },
    "delhi-nsfdc-elst": {
        "hi": "एनएसएफडीसी रोजगार-उन्मुख कौशल प्रशिक्षण कार्यक्रम",
        "ta": "என்.எஸ்.எஃப்.டி.சி வேலைவாய்ப்புடன் கூடிய திறன் பயிற்சி",
        "te": "ఎన్ఎస్ఎఫ్ డిసి నైపుణ్య శిక్షణ కార్యక్రమం"
    },
    "delhi-post-matric-sc": {
        "hi": "अनुसूचित जाति छात्रों हेतु पोस्ट-मैट्रिक छात्रवृत्ति योजना",
        "ta": "பட்டியல் சாதி மாணவர்களுக்கான போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை",
        "te": "ఎస్సీ విద్యార్థులకు పోస్ట్-మెట్రిక్ స్కాలర్‌షిప్"
    },
    "delhi-standup-india": {
        "hi": "स्टैंड-अप इंडिया योजना",
        "ta": "ஸ்டாண்ட்-அப் இந்தியா திட்டம்",
        "mr": "स्टँड-अप इंडिया योजना"
    },
    "delhi-pmkvy-4": {
        "hi": "प्रधानमंत्री कौशल विकास योजना 4.0",
        "ta": "பிரதம மந்திரி கௌஷல் விகாஸ் யோஜனா 4.0"
    },
    "delhi-pmegp": {
        "hi": "प्रधानमंत्री रोजगार सृजन कार्यक्रम (पीएमईजीपी)",
        "ta": "பிரதம மந்திரி வேலைவாய்ப்பு உருவாக்கும் திட்டம்"
    },
    "delhi-dsfdc-term-loan": {
        "hi": "डीएसएफडीसी स्वरोजगार मियादी ऋण योजना",
        "ta": "டி.எஸ்.எஃப்.டி.சி சுயதொழில் தவணைக் கடன் திட்டம்"
    },
    "delhi-dilli-swarojgar-yojna": {
        "hi": "दिल्ली स्वरोजगार योजना (डीएसएफडीसी माइक्रो-क्रेडिट)",
        "ta": "டெல்லி சுயதொழில் திட்டம்"
    },
    "delhi-pm-surya-ghar": {
        "hi": "पीएम सूर्य घर: मुफ्त बिजली योजना (सूर्यमित्र)",
        "ta": "பிஎம் சூர்யா கர்: இலவச மின்சாரத் திட்டம்"
    },
    "delhi-sc-women-empowerment": {
        "hi": "दिल्ली अनुसूचित जाति महिला स्वयं सहायता समूह आजीविका अनुदान",
        "ta": "டெல்லி எஸ்சி மகளிர் சுயஉதவிக்குழு வாழ்வாதார மானியம்"
    },
    "delhi-pm-vishwakarma": {
        "hi": "पीएम विश्वकर्मा योजना",
        "ta": "பிஎம் விஸ்வகர்மா திட்டம்"
    },
    "delhi-sc-nursing-gda": {
        "hi": "दिल्ली स्वास्थ्य सेवा कौशल मिशन (जीडीए एवं नर्सिंग)",
        "ta": "டெல்லி சுகாதாரப் பணி திறன் திட்டம்"
    }
}


def get_localized_scheme_name(scheme_id: str, scheme_name: str, lang: str) -> str:
    """Returns scheme name in English with local-script name in brackets where available."""
    if not lang or lang.lower() == "en":
        return scheme_name
    lang_key = lang.lower()
    local_dict = SCHEME_LOCAL_NAMES.get(scheme_id, {})
    local_name = local_dict.get(lang_key)
    if local_name:
        return f"{scheme_name} ({local_name})"
    return scheme_name


def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_cache_table():
    try:
        conn = _get_sqlite_conn()
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS query_translation_cache (
                original_text TEXT PRIMARY KEY,
                english_text TEXT NOT NULL,
                detected_lang TEXT NOT NULL,
                method TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        conn.close()
    except Exception as e:
        logger.warning(f"Could not initialize query_translation_cache table: {e}")


# Initialize table on import
_init_cache_table()


def _get_from_cache(text: str) -> Optional[Dict[str, str]]:
    clean = text.strip()
    # 1. In-memory
    if clean in _TRANSLATION_MEM_CACHE:
        return _TRANSLATION_MEM_CACHE[clean]

    # 2. SQLite
    try:
        conn = _get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT original_text, english_text, detected_lang, method FROM query_translation_cache WHERE original_text = ?", (clean,))
        row = cursor.fetchone()
        conn.close()
        if row:
            res = {
                "original": row["original_text"],
                "english": row["english_text"],
                "detected_lang": row["detected_lang"],
                "method": row["method"]
            }
            _TRANSLATION_MEM_CACHE[clean] = res
            return res
    except Exception as e:
        logger.debug(f"Cache read error: {e}")
    return None


def _save_to_cache(original: str, english: str, detected_lang: str, method: str):
    clean = original.strip()
    data = {
        "original": clean,
        "english": english,
        "detected_lang": detected_lang,
        "method": method
    }
    _TRANSLATION_MEM_CACHE[clean] = data
    try:
        conn = _get_sqlite_conn()
        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO query_translation_cache (original_text, english_text, detected_lang, method)
            VALUES (?, ?, ?, ?)
            """, (clean, english, detected_lang, method))
        conn.close()
    except Exception as e:
        logger.debug(f"Cache write error: {e}")


def detect_language(text: str, ui_lang: Optional[str] = None) -> str:
    """
    Language detection:
    - Use the UI-selected language if provided, unless text contains an obvious Indic script.
    - Otherwise detect by Unicode script ranges (Devanagari, Gurmukhi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Arabic/Urdu).
    - Treat Latin script as English.
    - Non-matching unknown scripts return 'unknown'.
    """
    if not text or not text.strip():
        return ui_lang or "en"

    # Count script matches
    script_counts = {}
    for code, pattern in SCRIPT_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            script_counts[code] = matches

    if not script_counts:
        # Check if text contains non-ASCII characters that don't match our 10 scripts
        non_ascii = [c for c in text if ord(c) > 127 and not c.isspace()]
        if non_ascii:
            return "unknown"
        return ui_lang or "en"

    # Find winning script
    best_script = max(script_counts, key=script_counts.get)

    if best_script == "hi":
        # Disambiguate Marathi vs Hindi using ui_lang
        if ui_lang and ui_lang.lower() == "mr":
            return "mr"
        return "hi"

    if best_script == "en":
        # If UI selected an Indic language but user typed in Latin script
        if ui_lang and ui_lang.lower() not in ["en", "auto"]:
            return ui_lang.lower()
        return "en"

    return best_script


# Mockable hook for LLM translation
_MOCK_LLM_TRANSLATOR = None

def set_mock_llm_translator(fn):
    """Sets a mock translator function fn(text: str) -> Optional[str] for testing."""
    global _MOCK_LLM_TRANSLATOR
    _MOCK_LLM_TRANSLATOR = fn


def call_llm_translation(text: str) -> Optional[str]:
    """
    Step 1: LLM translation call with prompt:
    "Translate to English, keep scheme names and numbers unchanged, output only the translation".
    Returns None if LLM is unavailable, rate-limited, or fails.
    """
    global _MOCK_LLM_TRANSLATOR
    if _MOCK_LLM_TRANSLATOR is not None:
        try:
            return _MOCK_LLM_TRANSLATOR(text)
        except Exception as e:
            logger.debug(f"Mock LLM failed: {e}")
            return None

    prompt = "Translate to English, keep scheme names and numbers unchanged, output only the translation"
    user_msg = f"{prompt}\n\nText: {text}"

    # Try Groq API
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import requests
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a professional translator. Output only the English translation."},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 150
                },
                timeout=4
            )
            if resp.status_code == 200:
                translation = resp.json()["choices"][0]["message"]["content"].strip()
                if translation:
                    return translation
        except Exception as exc:
            logger.debug(f"Groq translation call failed: {exc}")

    # Try Gemini API
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": user_msg}]}
                ],
                "generationConfig": {"temperature": 0.0, "maxOutputTokens": 150}
            }
            resp = requests.post(url, json=payload, timeout=4)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    translation = candidates[0]["content"]["parts"][0]["text"].strip()
                    if translation:
                        return translation
        except Exception as exc:
            logger.debug(f"Gemini translation call failed: {exc}")

    return None


_GLOSSARY_CACHE: Optional[Dict[str, Any]] = None

def _load_glossary() -> Dict[str, Any]:
    global _GLOSSARY_CACHE
    if _GLOSSARY_CACHE is None:
        if os.path.exists(GLOSSARY_PATH):
            try:
                with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                    _GLOSSARY_CACHE = json.load(f)
            except Exception as e:
                logger.error(f"Error loading glossary from {GLOSSARY_PATH}: {e}")
                _GLOSSARY_CACHE = {}
        else:
            _GLOSSARY_CACHE = {}
    return _GLOSSARY_CACHE


def translate_via_glossary(text: str, detected_lang: str) -> Optional[str]:
    """
    Step 2: Fall back to an OFFLINE glossary mapping ~60 core terms from each of the 11 IVR languages
    to English, and rewrite the query by term substitution.
    """
    glossary = _load_glossary()
    if not glossary:
        return None

    by_lang = glossary.get("by_language", {})
    # Get terms for detected language
    lang_dict = by_lang.get(detected_lang, {})
    
    # Also collect terms from other languages in case query has mixed words or language detection was partial
    all_terms = {}
    if lang_dict:
        all_terms.update(lang_dict)
    else:
        # Fall back to checking all languages
        for l_code, l_terms in by_lang.items():
            all_terms.update(l_terms)

    if not all_terms:
        return None

    # Sort terms by length descending so multi-word phrases match before single words
    sorted_terms = sorted(all_terms.keys(), key=lambda x: len(x), reverse=True)
    
    rewritten = text
    matched = False
    
    for term in sorted_terms:
        # Case insensitive replacement for Unicode words
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(rewritten):
            eng_sub = all_terms[term]
            rewritten = pattern.sub(f" {eng_sub} ", rewritten)
            matched = True

    if matched:
        # Clean up whitespace
        clean_rewritten = re.sub(r"\s+", " ", rewritten).strip()
        return clean_rewritten

    return None


def normalize_query(text: str, ui_lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entrypoint:
    normalize_query(text, ui_lang) -> {original, english, detected_lang, method}
    method is one of: "llm" | "glossary" | "none"
    """
    if not text or not text.strip():
        return {
            "original": text or "",
            "english": text or "",
            "detected_lang": ui_lang or "en",
            "method": "none"
        }

    clean_text = text.strip()
    detected_lang = detect_language(clean_text, ui_lang=ui_lang)

    # If already English, no translation needed
    if detected_lang == "en":
        return {
            "original": clean_text,
            "english": clean_text,
            "detected_lang": "en",
            "method": "none"
        }

    # If unknown script, return gracefully without crashing
    if detected_lang == "unknown":
        # Check if glossary or LLM can handle it, otherwise fallback gracefully
        pass

    # Check cache first
    cached = _get_from_cache(clean_text)
    if cached:
        return cached

    # 1. Attempt LLM translation
    llm_translated = call_llm_translation(clean_text)
    if llm_translated and llm_translated.lower() != clean_text.lower():
        _save_to_cache(clean_text, llm_translated, detected_lang, "llm")
        return {
            "original": clean_text,
            "english": llm_translated,
            "detected_lang": detected_lang,
            "method": "llm"
        }

    # 2. Fall back to OFFLINE glossary
    glossary_translated = translate_via_glossary(clean_text, detected_lang)
    if glossary_translated and glossary_translated.strip():
        _save_to_cache(clean_text, glossary_translated, detected_lang, "glossary")
        return {
            "original": clean_text,
            "english": glossary_translated,
            "detected_lang": detected_lang,
            "method": "glossary"
        }

    # 3. None / Fallback to original text
    return {
        "original": clean_text,
        "english": clean_text,
        "detected_lang": detected_lang,
        "method": "none"
    }


def clear_query_normalizer_cache():
    """Helper to clear both in-memory and SQLite cache (useful for testing)."""
    _TRANSLATION_MEM_CACHE.clear()
    try:
        conn = _get_sqlite_conn()
        with conn:
            conn.execute("DELETE FROM query_translation_cache;")
        conn.close()
    except Exception:
        pass
