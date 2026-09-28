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


def synthesize_free_neural_tts(text: str, language_code: str = "en") -> Optional[str]:
    """
    Synthesizes speech audio (MP3 base64-encoded) without requiring any API key.
    Supports Indian regional languages: ta (Tamil), hi (Hindi), mr (Marathi), pa (Punjabi), en (English).
    """
    if not text or not text.strip():
        return None
    try:
        import urllib.request
        import urllib.parse
        import base64
        import re

        clean = re.sub(r'[*_#`~]', '', text).strip()
        # Truncate to reasonable sentence length for TTS chunk
        short_text = clean[:180]
        q = urllib.parse.quote(short_text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={language_code}&client=tw-ob&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                audio_bytes = response.read()
                return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.warning(f"Free neural TTS fallback error: {e}")
    return None


def text_to_speech(text: str, language_code: str = "hi") -> Optional[str]:
    """
    Converts text to speech audio WAV/MP3 (base64-encoded).
    Uses Bhashini ULCA TTS if credentials configured;
    Otherwise uses high-quality Indian regional neural TTS fallback (zero API keys needed!).
    """
    if not is_mock_mode():
        try:
            config = get_pipeline_config()
            callback_url = config["callbackUrl"]
            inference_key = config["inferenceKeyHeader"]
            service_id = config["serviceIdByTask"].get("tts")

            body = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": language_code},
                            "serviceId": service_id,
                            "gender": "female",
                            "samplingRate": 8000,
                        },
                    }
                ],
                "inputData": {"input": [{"source": text}]},
            }

            headers = {
                "Content-Type": "application/json",
                inference_key["name"]: inference_key["value"],
            }

            resp = requests.post(callback_url, json=body, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return data["pipelineResponse"][0]["audio"][0]["audioContent"]
        except Exception as e:
            logger.warning(f"Bhashini TTS error, falling back to neural TTS: {e}")

    # High-quality neural TTS fallback (supports Tamil, Hindi, Marathi, Punjabi, English)
    return synthesize_free_neural_tts(text, language_code)
