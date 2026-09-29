"""
Bhashini (ULCA/Dhruva) Speech Client — ASR (Speech-to-Text) + TTS (Text-to-Speech)
National Language Translation Mission (NLTM), Ministry of Electronics & IT (MeitY), Govt. of India.

Configuration via environment variables or .env:
  BHASHINI_USER_ID
  BHASHINI_API_KEY (ulcaApiKey)
  MOCK_SPEECH=true (default: uses canned transcripts & fallback)
"""
import os
import logging
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("bhashini")

PIPELINE_CONFIG_ENDPOINT = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
DEFAULT_PIPELINE_ID = "64392f96daac500b55c543cd"  # Standard public ASR+TTS+NMT pipeline

MOCK_SPEECH = os.getenv("MOCK_SPEECH", "true").lower() in ("true", "1", "yes")

_cached_config: Optional[Dict[str, Any]] = None


def is_mock_mode() -> bool:
    """Returns True if mock mode is explicitly requested or required credentials are missing."""
    if MOCK_SPEECH:
        return True
    user_id = os.getenv("BHASHINI_USER_ID")
    api_key = os.getenv("BHASHINI_API_KEY")
    return not (user_id and api_key)


def get_pipeline_config() -> Dict[str, Any]:
    """
    Fetches and caches the dynamic pipeline inference endpoint and service IDs from MeitY ULCA.
    """
    global _cached_config
    if _cached_config:
        return _cached_config

    user_id = os.getenv("BHASHINI_USER_ID")
    api_key = os.getenv("BHASHINI_API_KEY")

    if not user_id or not api_key:
        raise ValueError("BHASHINI_USER_ID and BHASHINI_API_KEY must be set to call live Bhashini API")

    headers = {
        "Content-Type": "application/json",
        "userID": user_id,
        "ulcaApiKey": api_key,
    }

    payload = {
        "pipelineTasks": [{"taskType": "asr"}, {"taskType": "tts"}],
        "pipelineRequestConfig": {"pipelineId": DEFAULT_PIPELINE_ID},
    }

    resp = requests.post(PIPELINE_CONFIG_ENDPOINT, json=payload, headers=headers, timeout=12)
    resp.raise_for_status()
    data = resp.json()

    callback_url = data["pipelineInferenceAPIEndPoint"]["callbackUrl"]
    inference_key_header = data["pipelineInferenceAPIEndPoint"]["inferenceApiKey"]

    service_id_by_task = {}
    for task in data.get("pipelineResponseConfig", []):
        task_type = task.get("taskType")
        config_list = task.get("config", [])
        if config_list and task_type:
            service_id_by_task[task_type] = config_list[0].get("serviceId")

    _cached_config = {
        "callbackUrl": callback_url,
        "inferenceKeyHeader": inference_key_header,
        "serviceIdByTask": service_id_by_task,
    }
    return _cached_config


def speech_to_text(audio_base64: str, language_code: str = "hi") -> str:
    """
    Converts base64-encoded audio bytes to transcript via Bhashini ULCA ASR.
    Falls back to realistic regional mock if in mock mode.
    """
    if is_mock_mode():
        # Canned realistic Indian beneficiary utterance
        canned_utterances = {
            "hi": "नमस्ते, मैंने 10वीं पास की है और मैं अपने पिता के साथ बिजली का काम करता हूँ।",
            "mr": "मी दहावी पास झालो आहे आणि मला सौर तंत्रज्ञ बनायचे आहे.",
            "pa": "ਮੈਂ ਦਸਵੀਂ ਪਾਸ ਕੀਤੀ ਹੈ ਅਤੇ ਖੇਤੀਬਾੜੀ ਅਤੇ ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਵਿੱਚ ਦਿਲਚਸਪੀ ਰੱਖਦਾ ਹਾਂ।",
            "ta": "நான் பத்தாம் வகுப்பு முடித்துள்ளேன், இருசக்கர வாகன மெக்கானிக் வேலை செய்ய விரும்புகிறேன்.",
            "en": "I did my 10th standard and I help my father with electrical and wiring work at home."
        }
        return canned_utterances.get(language_code, canned_utterances["en"])

    config = get_pipeline_config()
    callback_url = config["callbackUrl"]
    inference_key = config["inferenceKeyHeader"]
    service_id = config["serviceIdByTask"].get("asr")

    body = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": language_code},
                    "serviceId": service_id,
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                },
            }
        ],
        "inputData": {"audio": [{"audioContent": audio_base64}]},
    }

    headers = {
        "Content-Type": "application/json",
        inference_key["name"]: inference_key["value"],
    }

    resp = requests.post(callback_url, json=body, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["pipelineResponse"][0]["output"][0]["source"]


EDGE_TTS_VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "mr": "mr-IN-AarohiNeural",
    "ta": "ta-IN-PallaviNeural",
    "pa": "hi-IN-SwaraNeural",  # Hindi neural voice smoothly vocalizes Gurmukhi phonetics
}


def split_into_sentences(text: str) -> list:
    """
    Splits text into natural sentence chunks respecting English and Indic punctuation.
    Removes markdown and cleans whitespace. Does NOT truncate.
    """
    if not text:
        return []
    import re
    clean = re.sub(r'[*_#`~\[\]]', '', text).strip()
    clean = re.sub(r'\s+', ' ', clean)
    if not clean:
        return []

    # Split by standard sentence delimiters (dot, question, exclamation, Devanagari danda / double danda, newline)
    raw_chunks = re.split(r'([.?!।॥\n]+)', clean)
    sentences = []
    current = ""
    for piece in raw_chunks:
        if re.match(r'^[.?!।॥\n]+$', piece):
            current += piece
            if current.strip():
                sentences.append(current.strip())
            current = ""
        else:
            current += piece
    if current.strip():
        sentences.append(current.strip())

    return [s for s in sentences if s.strip()]


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bit_depth: int = 16) -> bytes:
    """Wraps raw 16-bit PCM audio bytes in a standard 44-byte RIFF/WAVE header."""
    import struct
    byte_rate = sample_rate * channels * (bit_depth // 8)
    block_align = channels * (bit_depth // 8)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(pcm_data),
        b'WAVE',
        b'fmt ',
        16,
        1,  # PCM format
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bit_depth,
        b'data',
        len(pcm_data)
    )
    return header + pcm_data


def synthesize_gemini_sentence(sentence: str, lang: str = "en") -> Optional[bytes]:
    """
    Synthesizes a sentence via Gemini API (gemini-3.8-flash-tts / gemini-3.8-flash-lite-tts).
    Checks on-disk cache first. Returns valid WAV bytes with RIFF header.
    Uses direct REST with strict timeout to avoid SDK exponential backoff on 429 rate limits.
    """
    import hashlib
    import base64

    clean = sentence.strip()
    if not clean:
        return None

    lang_key = (lang or "en").lower().strip()
    cache_hash = hashlib.sha256(f"{lang_key}:{clean}".encode("utf-8")).hexdigest()[:24]
    cache_path = os.path.join(CACHE_DIR, f"{cache_hash}.wav")

    # 1. On-disk Cache Hit
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 44:
        try:
            with open(cache_path, "rb") as f:
                return f.read()
        except Exception:
            pass

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.warning("GEMINI_API_KEY is not set in environment or .env.")
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {
        "x-goog-api-key": gemini_key,
        "Content-Type": "application/json"
    }

    models_to_try = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"]
    for model_name in models_to_try:
        try:
            payload = {
                "model": model_name,
                "input": [{
                    "type": "user_input",
                    "content": [{
                        "type": "text",
                        "text": clean
                    }]
                }],
                "response_format": {
                    "type": "audio",
                    "mime_type": "audio/wav"
                },
                "generation_config": {
                    "speech_config": [
                        {"voice": "Kore"}
                    ]
                }
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                raw_b64 = None
                if "output_audio" in data and isinstance(data["output_audio"], dict):
                    raw_b64 = data["output_audio"].get("data")
                elif "steps" in data and isinstance(data["steps"], list):
                    for step in data["steps"]:
                        for c in step.get("content", []):
                            if c.get("type") == "audio" and c.get("data"):
                                raw_b64 = c["data"]
                                break
                        if raw_b64:
                            break

                if raw_b64:
                    raw = base64.b64decode(raw_b64)
                    # Ensure valid WAV container format (wrap PCM if raw PCM is returned)
                    if not raw.startswith(b"RIFF") or len(raw) < 44 or raw[8:12] != b"WAVE":
                        raw = pcm_to_wav(raw, sample_rate=24000)

                    # Save to on-disk cache
                    try:
                        with open(cache_path, "wb") as f:
                            f.write(raw)
                    except Exception as write_err:
                        logger.warning(f"Could not write TTS cache: {write_err}")

                    return raw

            elif resp.status_code == 429:
                logger.warning(f"Gemini model {model_name} rate-limited (429); checking alternative.")
                continue
            else:
                logger.warning(f"Gemini model {model_name} returned status {resp.status_code}: {resp.text[:120]}")

        except Exception as exc:
            logger.warning(f"Gemini TTS error with model {model_name} for '{clean[:30]}...': {exc}")

    return None


def _gurmukhi_to_devanagari(text: str) -> str:
    """Maps Gurmukhi characters (0x0A01-0x0A75) to Devanagari (0x0901-0x0975) for neural voice phonetic rendering."""
    res = []
    for ch in text:
        code = ord(ch)
        if 0x0A01 <= code <= 0x0A75:
            res.append(chr(code - 0x0100))
        else:
            res.append(ch)
    return "".join(res)


async def _synthesize_edge_chunk_async(sentence: str, voice: str) -> Optional[bytes]:
    """Synthesizes a single text sentence chunk via edge-tts."""
    try:
        import edge_tts
        text_to_speak = sentence
        # If text contains Gurmukhi script and Hindi voice is used, transliterate for smooth pronunciation
        if voice.startswith("hi-") and any(0x0A00 <= ord(c) <= 0x0A7F for c in sentence):
            text_to_speak = _gurmukhi_to_devanagari(sentence)

        comm = edge_tts.Communicate(text_to_speak, voice)
        parts = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                parts.append(chunk["data"])
        return b"".join(parts)
    except Exception as e:
        logger.warning(f"Edge-TTS chunk synthesis error: {e}")
        return None


async def _synthesize_single_sentence_async(sentence: str, lang: str, idx: int = 0) -> dict:
    """
    Synthesizes a single sentence chunk with hierarchical fallbacks:
    1. Disk Cache -> 2. Gemini TTS (gemini-3.8-flash-tts) -> 3. Edge-TTS -> 4. Error dict
    """
    import base64
    clean = sentence.strip()

    # 1. Try Gemini TTS (with disk caching)
    wav_bytes = synthesize_gemini_sentence(clean, lang)
    if wav_bytes:
        return {
            "index": idx,
            "text": clean,
            "audio_base64": base64.b64encode(wav_bytes).decode("utf-8"),
            "format": "audio/wav",
            "error": None
        }

    # 2. Keyless Edge-TTS fallback
    voice = EDGE_TTS_VOICES.get(lang.lower(), EDGE_TTS_VOICES["en"])
    mp3_bytes = await _synthesize_edge_chunk_async(clean, voice)
    if mp3_bytes:
        return {
            "index": idx,
            "text": clean,
            "audio_base64": base64.b64encode(mp3_bytes).decode("utf-8"),
            "format": "audio/mpeg",
            "error": None
        }

    # 3. Failed synthesis - explicit error flag, not null
    return {
        "index": idx,
        "text": clean,
        "audio_base64": None,
        "format": "audio/wav",
        "error": "TTS synthesis failed or credentials unavailable"
    }


async def synthesize_chunks_async(text: str, language_code: str = "en", lang: str = None) -> list:
    """
    Requirement 4: Split replies into sentences, synthesize the first sentence immediately,
    and prefetch the rest while it plays.
    """
    target_lang = (lang if lang is not None else language_code or "en").lower().strip()
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    # 1. Synthesize first sentence immediately
    first_chunk = await _synthesize_single_sentence_async(sentences[0], target_lang, idx=0)

    # 2. Prefetch and synthesize the rest concurrently
    if len(sentences) > 1:
        import asyncio
        rest_chunks = await asyncio.gather(
            *(_synthesize_single_sentence_async(s, target_lang, idx=i) for i, s in enumerate(sentences[1:], 1))
        )
        return [first_chunk] + list(rest_chunks)
    else:
        return [first_chunk]


def synthesize_chunks(text: str, language_code: str = "en", lang: str = None) -> list:
    """Synchronous wrapper for synthesize_chunks_async."""
    import asyncio
    import concurrent.futures

    target_lang = lang if lang is not None else language_code

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, synthesize_chunks_async(text, target_lang)).result()
    else:
        return asyncio.run(synthesize_chunks_async(text, target_lang))


def text_to_speech(text: str, language_code: str = "hi", lang: str = None) -> Optional[str]:
    """
    Converts text to speech audio (base64-encoded string).
    Supports Gemini TTS, disk cache, edge-tts fallback, and multi-sentence WAV concatenation.
    """
    target_lang = lang if lang is not None else language_code
    if not text or not text.strip():
        return None

    try:
        chunks = synthesize_chunks(text, target_lang)
        if not chunks:
            return None

        valid_chunks = [c for c in chunks if c.get("audio_base64")]
        if not valid_chunks:
            return None

        if len(valid_chunks) == 1:
            return valid_chunks[0]["audio_base64"]

        # Concatenate audio frames
        import base64
        chunk_raw = [base64.b64decode(c["audio_base64"]) for c in valid_chunks]

        # If chunks are WAV, combine the raw PCM payloads and re-pack header
        if chunk_raw[0].startswith(b"RIFF") and chunk_raw[0][8:12] == b"WAVE":
            pcm_payload = b"".join(c[44:] if c.startswith(b"RIFF") else c for c in chunk_raw)
            combined_wav = pcm_to_wav(pcm_payload, sample_rate=24000)
            return base64.b64encode(combined_wav).decode("utf-8")
        else:
            # MP3 stream concatenation
            combined_bytes = b"".join(chunk_raw)
            return base64.b64encode(combined_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning(f"text_to_speech error: {exc}")
        return None


# Pre-cache fixed prompts on disk per language
FIXED_PROMPTS = {
    "hi": "नमस्ते! आप अपने बारे में बताएं — आपकी पढ़ाई कितनी हुई है, और आप किस तरह का काम सीखना या करना चाहते हैं?",
    "mr": "नमस्कार! तुमच्याबद्दल सांगा — तुमचे शिक्षण किती झाले आहे आणि तुम्हाला कोणत्या प्रकारचे काम शिकायला आवडेल?",
    "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ — ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ ਅਤੇ ਤੁਸੀਂ ਕਿਸ ਤਰ੍ਹਾਂ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
    "ta": "வணக்கம்! உங்களைப் பற்றி கூறுங்கள் — உங்கள் கல்வித்தகுதி என்ன, என்ன வேலை செய்ய விரும்புகிறீர்கள்?",
    "en": "Welcome! Please tell me about yourself — what is your education level, and what kind of work interests you?",
    "test_en": "Welcome! Nivara PM-AJAY Livelihood Guide voice output is active and working clearly.",
    "health": "Nivara speech engine online and functional."
}


def init_tts_cache():
    """Initializes and pre-caches fixed greeting prompts on disk."""
    try:
        for key, text in FIXED_PROMPTS.items():
            l = "en" if "_" in key or key == "health" else key
            synthesize_gemini_sentence(text, l)
    except Exception as e:
        logger.warning(f"Fixed prompts pre-caching note: {e}")

