"""
tests/test_ivr.py — Verification of Phase 7: 10+ Language IVR System & Integration
"""
import re
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_ivr_html_elements_present():
    """Verify IVR simulator UI contains feature phone, 10+ language keypad, and transcript panel."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Section ID
    assert 'id="viewIvr"' in html

    # Feature phone elements
    assert 'id="retroScreen"' in html
    assert 'id="callStatusBadge"' in html
    assert 'id="timerBadge"' in html
    assert 'id="lcdPrompt"' in html
    assert 'id="keyCall"' in html
    assert 'id="keyEnd"' in html
    assert 'id="keyNav"' in html

    # 12 tactile keys
    keypad_matches = re.findall(r'class="[^"]*keypad-btn[^"]*"[^>]*data-key="([^"]+)"', html)
    assert len(keypad_matches) >= 12
    for k in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']:
        assert k in keypad_matches

    # Transcript panel beside phone
    assert 'id="ivrTranscriptStream"' in html
    assert 'id="telemetryLangLabel"' in html
    assert 'id="telemetryMenuState"' in html
    assert 'id="telemetryDtmfFreq"' in html
    assert 'id="ivrSmsSlipText"' in html
    assert 'id="btnIvrMic"' in html
    assert 'id="ivrVoiceInputText"' in html

def test_ivr_app_js_languages_and_menu_tree():
    """Verify app.js contains 10+ languages config and menu prompts."""
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    # Check for IVR_LANGUAGES config list with at least 10 languages
    expected_langs = ['hi', 'en', 'pa', 'ur', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml']
    for lang in expected_langs:
        assert f"code: '{lang}'" in js or f'code: "{lang}"' in js

    # Check DTMF Web Audio implementation
    assert 'DTMF_FREQS' in js
    assert 'playDtmfTone' in js
    assert 'playLineRinging' in js

    # Check Menu state engine
    assert 'LANG_SELECT' in js
    assert 'MAIN_MENU' in js
    assert 'SUBMENU_SCHEMES' in js
    assert 'SUBMENU_CENTRES' in js
    assert 'ASSISTANT_TALK' in js

    # Check RAG integration for IVR
    assert '/rag/retrieve' in js
    assert '/rag/ask' in js
    assert 'submitIvrVoiceQuery' in js

def test_rag_query_from_ivr_endpoint():
    """Verify backend responds to IVR queries for schemes and centres."""
    res = client.get("/rag/retrieve?q=Delhi+SC+livelihood+schemes&k=3")
    assert res.status_code == 200
    records = res.json()
    assert len(records) > 0

    # Test Q&A pipeline used by IVR Option 3
    ask_res = client.post("/rag/ask", json={
        "query": "What electrician courses are available in Delhi under PM-AJAY?",
        "user_id": "ivr_caller_test",
        "language": "hi"
    })
    assert ask_res.status_code == 200
    assert "answer" in ask_res.json()
    assert len(ask_res.json()["answer"]) > 10
