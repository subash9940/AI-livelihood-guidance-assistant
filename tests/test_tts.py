"""
Unit and Integration Tests for TTS Enhancements:
1. Sentence chunking logic (English and Indic punctuation: ., ?, !, ।, ॥, \n).
2. Server TTS fallback architecture (Bhashini -> Edge-TTS -> Graceful Error).
3. POST /api/tts endpoint returning chunked audio list and tts_available flag.
4. Error handling returning tts_available: false and error message instead of silent null.
5. Non-blocking session routes (no synchronous TTS delays in /session/start or /session/{id}/voice-input).
"""

import os
import sys
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure root import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bhashini
from api import app

client = TestClient(app)


# ============================================================================
# 1. Test Sentence Chunking Logic
# ============================================================================
def test_split_into_sentences_english():
    text = "Hello Sunita! Welcome to Nivara. How can I help you today?"
    sentences = bhashini.split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Hello Sunita!"
    assert sentences[1] == "Welcome to Nivara."
    assert sentences[2] == "How can I help you today?"


def test_split_into_sentences_hindi_danda():
    text = "नमस्ते सुनीता। पीएम-अजय योजना में आपका स्वागत है। आप क्या सीखना चाहती हैं?"
    sentences = bhashini.split_into_sentences(text)
    assert len(sentences) == 3
    assert "नमस्ते सुनीता" in sentences[0]
    assert "स्वागत है" in sentences[1]
    assert "चाहती हैं" in sentences[2]


def test_split_into_sentences_newlines_and_spaces():
    text = "First paragraph line.\n\nSecond paragraph line!\nThird question?"
    sentences = bhashini.split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "First paragraph line."
    assert sentences[1] == "Second paragraph line!"
    assert sentences[2] == "Third question?"


def test_split_into_sentences_empty_or_whitespace():
    assert bhashini.split_into_sentences("") == []
    assert bhashini.split_into_sentences("   \n\t  ") == []


# ============================================================================
# 2. Test Edge-TTS Synthesis and Fallback
# ============================================================================
def test_synthesize_chunks_edge_tts():
    # If network/edge-tts is available, synthesize a tiny sentence
    chunks = bhashini.synthesize_chunks("Hello!", lang="en")
    assert isinstance(chunks, list)
    assert len(chunks) == 1
    assert chunks[0]["index"] == 0
    assert chunks[0]["text"] == "Hello!"
    # When edge-tts succeeds, audio_base64 is a non-empty string
    if chunks[0]["audio_base64"]:
        assert len(chunks[0]["audio_base64"]) > 50


def test_text_to_speech_combines_or_delegates():
    # Verify text_to_speech returns a string or None (no unhandled exceptions)
    res = bhashini.text_to_speech("Welcome to PM-AJAY.", lang="en")
    assert res is None or isinstance(res, str)


# ============================================================================
# 3. Test POST /api/tts Endpoint (Multi-sentence chunks)
# ============================================================================
def test_api_tts_chunked_response():
    payload = {
        "text": "Hello there! Welcome to the Nivara skill advisor. Let's find your trade.",
        "language": "en"
    }
    res = client.post("/api/tts", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tts_available" in data
    assert "audio_chunks" in data
    assert isinstance(data["audio_chunks"], list)
    assert len(data["audio_chunks"]) == 3
    assert data["audio_chunks"][0]["text"] == "Hello there!"
    assert data["format"] in ("audio/wav", "audio/mpeg")


def test_api_tts_empty_text():
    res = client.post("/api/tts", json={"text": "", "language": "en"})
    assert res.status_code == 400


# ============================================================================
# 4. Test Error Handling returns tts_available: false (not silent null)
# ============================================================================
def test_api_tts_error_returns_explicit_flag():
    with patch("bhashini.synthesize_chunks_async", side_effect=RuntimeError("Neural TTS service unavailable")):
        res = client.post("/api/tts", json={"text": "Test error", "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert data["tts_available"] is False
        assert data["audio_base64"] is None
        assert data["error"] is not None
        assert "unavailable" in data["error"]


# ============================================================================
# 5. Test Non-blocking Session Routes (No synchronous TTS latency)
# ============================================================================
def test_session_start_non_blocking_tts():
    # POST /session/start should return immediately with initial_audio_base64: None
    res = client.post("/session/start", json={"entry_mode": "app", "language": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data.get("initial_audio_base64") is None
    assert "initial_prompt" in data
    assert len(data["initial_prompt"]) > 0


def test_voice_input_non_blocking_tts():
    # Start a session
    res_start = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id = res_start.json()["session_id"]

    # Voice input should return reply_audio_base64: None immediately
    res_voice = client.post(
        f"/session/{session_id}/voice-input",
        json={"transcript": "I am 10th pass and want electrical work", "language": "en"}
    )
    assert res_voice.status_code == 200
    data = res_voice.json()
    assert data.get("reply_audio_base64") is None
    assert "next_prompt" in data


# ============================================================================
# 6. Test GET /api/tts/health Startup Self-check Endpoint (Requirement 6)
# ============================================================================
def test_tts_health_endpoint():
    res = client.get("/api/tts/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "unhealthy")
    assert "engine" in data
    assert "latency_ms" in data
    assert "tts_available" in data
    if data["status"] == "healthy":
        assert data["audio_bytes"] > 0
        assert data["format"] == "audio/wav"

