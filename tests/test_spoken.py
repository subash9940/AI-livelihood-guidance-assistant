"""
Unit and Integration Tests for Spoken Explanation & TTS Resilience (Nivara Livelihood Assistant).
Validates requirements d through i:
- Test d: 4 demo profiles x 5 languages (20 cases) constraint checks.
- Test e: LLM failure/timeout/empty/unset fallback to grammatical templates.
- Test f: Bhashini text_to_speech failure returns 200 with audio_base64: null.
- Test g: Endpoints return spoken_explanation for 4 demo profiles.
- Test h: Incomplete profile returns needs_more_info with clarifying_question as spoken_explanation.
- Test i: Second GET recommendation returns from cache.
"""
import os
import re
import sys
import time
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure root import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spoken
import nsqf_rules
import bhashini
from api import app

client = TestClient(app)

DEMO_PROFILES = {
    "Sunita": {
        "name": "Sunita Verma",
        "education": "8th Standard",
        "education_level": "8th Standard",
        "location": "Delhi",
        "state": "Delhi",
        "interests": ["Tailoring & Garment Making"],
        "skills": ["Basic Stitching & Fabric Cutting"],
        "family_occupation": "Tailoring / Weaving",
        "mobility_constraint": "Cannot travel far",
        "transcript": "My name is Sunita Verma from Delhi. I am 8th pass and do tailoring."
    },
    "Ramkishan": {
        "name": "Ramkishan Yadav",
        "education": "10th Standard",
        "education_level": "10th Standard",
        "location": "Varanasi",
        "state": "Uttar Pradesh",
        "interests": ["Food Processing & Preservation"],
        "skills": ["Food Handling & Raw Ingredient Quality"],
        "family_occupation": "Agriculture & Farming",
        "mobility_constraint": "Cannot travel far",
        "transcript": "My name is Ramkishan Yadav from Varanasi. I passed 10th standard and work in agriculture."
    },
    "Karthik": {
        "name": "Karthik Raja",
        "education": "12th Standard",
        "education_level": "12th Standard",
        "location": "Madurai",
        "state": "Tamil Nadu",
        "interests": ["Two-Wheeler & EV Maintenance"],
        "skills": ["Hand Tools & Mechanical Maintenance"],
        "family_occupation": "Daily Wage Labor",
        "mobility_constraint": "Willing to commute to District center",
        "transcript": "My name is Karthik Raja from Madurai. I completed 12th standard and have mechanical skills."
    },
    "Amit": {
        "name": "Amit Shinde",
        "education": "12th Standard",
        "education_level": "12th Standard",
        "location": "Pune",
        "state": "Maharashtra",
        "interests": ["Solar PV & Electrical Installations"],
        "skills": ["Basic Electrical Wiring & Circuit Safety"],
        "family_occupation": "Agriculture & Farming",
        "mobility_constraint": "Willing to commute to District center",
        "transcript": "My name is Amit Shinde from Pune. I passed 12th standard and know electrical wiring."
    }
}

LANGUAGES = ["en", "hi", "ta", "mr", "pa"]

EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010ffff]")
FORBIDDEN_CHARS = set("*#_[]")
QP_CODE_PATTERN = re.compile(r"\b[A-Z]{2,4}/Q\d{4}\b", re.IGNORECASE)


# ============================================================================
# Test d: 4 demo profiles x 5 languages = 20 cases
# ============================================================================
@pytest.mark.parametrize("profile_key", list(DEMO_PROFILES.keys()))
@pytest.mark.parametrize("lang", LANGUAGES)
def test_demo_profile_spoken_explanation_constraints(profile_key, lang):
    profile = DEMO_PROFILES[profile_key]
    rec = nsqf_rules.analyze_skill_gap(profile)

    spoken.clear_cache()
    expl = spoken.build_spoken_explanation(profile, rec, lang=lang)

    # 1. Non-empty string
    assert isinstance(expl, str) and len(expl.strip()) > 0, "Spoken explanation must not be empty"

    # 2. Length <= 400 characters
    assert len(expl) <= 400, f"Spoken explanation exceeded 400 chars ({len(expl)} chars): {expl}"

    # 3. Max 3 sentences
    sentence_count = spoken._count_sentences(expl)
    assert 1 <= sentence_count <= 3, f"Expected 1 to 3 sentences, got {sentence_count}: {expl}"

    # 4. No forbidden characters: * # _ [ ]
    for char in FORBIDDEN_CHARS:
        assert char not in expl, f"Forbidden markdown char '{char}' found in: {expl}"

    # 5. No emojis
    assert not EMOJI_PATTERN.search(expl), f"Emoji found in: {expl}"

    # 6. No QP codes (e.g. AMH/Q1947) or NSQF level references
    assert not QP_CODE_PATTERN.search(expl), f"QP code pattern found in: {expl}"
    assert "nsqf level" not in expl.lower(), f"NSQF Level jargon found in: {expl}"

    # 7. Contains trade name or translated equivalent
    trade_key = rec.get("trade_key")
    expected_trade = None
    if trade_key and trade_key in spoken.TRADE_NAMES and lang in spoken.TRADE_NAMES[trade_key]:
        expected_trade = spoken.TRADE_NAMES[trade_key][lang]
    elif rec.get("recommended_trade"):
        expected_trade = rec["recommended_trade"]

    if expected_trade:
        # Check if either full trade name or significant substring is in the explanation
        trade_tokens = [tok for tok in re.split(r"[\s&,-/()]+", expected_trade) if len(tok) >= 3]
        matched = any(tok.lower() in expl.lower() for tok in trade_tokens)
        assert matched, f"Trade token from '{expected_trade}' not found in spoken explanation: {expl}"


# ============================================================================
# Test e: Monkeypatch LLM path (raise, timeout, empty, unset) -> template fallback
# ============================================================================
def test_llm_failure_falls_back_to_template():
    profile = DEMO_PROFILES["Sunita"]
    rec = nsqf_rules.analyze_skill_gap(profile)

    # Sub-case 1: LLM raises exception
    spoken.clear_cache()
    with patch("spoken._call_llm", side_effect=Exception("Groq/Gemini connection failed")):
        expl = spoken.build_spoken_explanation(profile, rec, lang="en")
        assert len(expl) > 0
        assert "Sunita" in expl
        assert "Want me to go through the other options?" in expl
        assert spoken._count_sentences(expl) <= 3

    # Sub-case 2: LLM returns empty string
    spoken.clear_cache()
    with patch("spoken._call_llm", return_value=""):
        expl = spoken.build_spoken_explanation(profile, rec, lang="hi")
        assert len(expl) > 0
        assert "सुनीता" in expl or "Sunita" in expl
        assert "विकल्प" in expl
        assert spoken._count_sentences(expl) <= 3

    # Sub-case 3: LLM times out or sleeps past timeout
    def mock_sleep_timeout(*args, **kwargs):
        time.sleep(0.05)
        raise TimeoutError("LLM call timed out after 4 seconds")

    spoken.clear_cache()
    with patch("spoken._call_llm", side_effect=mock_sleep_timeout):
        expl = spoken.build_spoken_explanation(profile, rec, lang="ta")
        assert len(expl) > 0
        assert spoken._count_sentences(expl) <= 3

    # Sub-case 4: GROQ_API_KEY and GEMINI_API_KEY unset
    spoken.clear_cache()
    with patch.dict(os.environ, {"GROQ_API_KEY": "", "GEMINI_API_KEY": ""}, clear=True):
        expl = spoken.build_spoken_explanation(profile, rec, lang="pa")
        assert len(expl) > 0
        assert spoken._count_sentences(expl) <= 3
        assert "ਵਿਕਲਪ" in expl


# ============================================================================
# Test f: Monkeypatch bhashini.text_to_speech to raise -> 200 with null audio
# ============================================================================
def test_bhashini_failure_returns_200_with_null_audio():
    with patch("bhashini.text_to_speech", side_effect=Exception("Bhashini neural down")):
        # 1. POST /session/start
        res_start = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
        assert res_start.status_code == 200, f"Expected 200, got {res_start.status_code}: {res_start.text}"
        data_start = res_start.json()
        assert data_start.get("initial_audio_base64") is None, "Expected initial_audio_base64 to be null on TTS failure"

        # 2. POST /api/tts
        res_tts = client.post("/api/tts", json={"text": "Hello world", "language": "en"})
        assert res_tts.status_code == 200, f"Expected 200, got {res_tts.status_code}: {res_tts.text}"
        data_tts = res_tts.json()
        assert data_tts.get("audio_base64") is None, "Expected audio_base64 to be null on TTS failure"
        assert data_tts.get("language") == "en"


# ============================================================================
# Test g: 4 demo profiles via session and direct POST /recommendation
# ============================================================================
@pytest.mark.parametrize("profile_key", list(DEMO_PROFILES.keys()))
def test_demo_profile_endpoints_spoken_explanation(profile_key):
    profile = DEMO_PROFILES[profile_key]

    # Test via direct POST /recommendation
    spoken.clear_cache()
    res_direct = client.post("/recommendation", json={"profile": profile, "language": "en"})
    assert res_direct.status_code == 200
    data_direct = res_direct.json()
    assert "spoken_explanation" in data_direct
    assert isinstance(data_direct["spoken_explanation"], str)
    assert len(data_direct["spoken_explanation"].strip()) > 0
    assert "spoken_summary" in data_direct  # Backward compatibility check

    # Test via session intake pipeline: /session/start -> /session/{id}/voice-input -> /session/{id}/recommendation
    spoken.clear_cache()
    res_start = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    assert res_start.status_code == 200
    session_id = res_start.json()["session_id"]

    # Post utterance to populate profile
    res_voice = client.post(
        f"/session/{session_id}/voice-input",
        json={"text": profile["transcript"], "language": "en"}
    )
    assert res_voice.status_code == 200

    # If single utterance is complete, fetch recommendation
    if res_voice.json().get("profile_complete"):
        res_rec = client.get(f"/session/{session_id}/recommendation")
        assert res_rec.status_code == 200
        data_rec = res_rec.json()
        assert "spoken_explanation" in data_rec
        assert isinstance(data_rec["spoken_explanation"], str)
        assert len(data_rec["spoken_explanation"].strip()) > 0


# ============================================================================
# Test h: Incomplete profile returns needs_more_info with clarifying question
# ============================================================================
def test_incomplete_profile_clarifying_question_spoken():
    incomplete_profile = {
        "name": "Ravi",
        "location": "Bhopal"
        # missing skills, interests, and education
    }
    res = client.post("/recommendation", json={"profile": incomplete_profile, "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("needs_more_info") is True
    assert "spoken_explanation" in data
    assert "clarifying_question" in data
    assert data["spoken_explanation"] == data["clarifying_question"]


# ============================================================================
# Test i: Second GET returns recommendation from cache
# ============================================================================
def test_recommendation_cache_lookup():
    res_start = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id = res_start.json()["session_id"]

    profile = DEMO_PROFILES["Sunita"]
    res_voice = client.post(
        f"/session/{session_id}/voice-input",
        json={"text": profile["transcript"], "language": "en"}
    )
    assert res_voice.status_code == 200

    # Ensure profile complete in DB session for testing
    import database
    database.update_session(
        session_id=session_id,
        profile_data=profile,
        profile_complete=True
    )

    spoken.clear_cache()
    # First GET: cache miss, builds explanation and caches
    res1 = client.get(f"/session/{session_id}/recommendation")
    assert res1.status_code == 200
    expl1 = res1.json()["spoken_explanation"]
    assert len(expl1) > 0

    # Check cache key exists
    cache_key = f"{session_id}:en"
    assert cache_key in spoken._EXPLANATION_CACHE

    # Second GET: must return exactly the cached explanation without re-invoking LLM
    with patch("spoken._call_llm", side_effect=Exception("Should not be called on cache hit")):
        res2 = client.get(f"/session/{session_id}/recommendation")
        assert res2.status_code == 200
        expl2 = res2.json()["spoken_explanation"]
        assert expl1 == expl2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
