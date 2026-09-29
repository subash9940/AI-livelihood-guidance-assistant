"""
tests/test_cross_language_rag.py — Verification of Change 1: Cross-Language Retrieval.
Requirements:
1. The same question in English, Hindi, and Tamil must return overlapping top-3 scheme IDs
   (at least 2 of 3 in common) using the glossary path.
2. The same question in English, Hindi, and Tamil must return overlapping top-3 scheme IDs
   (at least 2 of 3 in common) using the LLM path (mocked).
3. A query with an unknown language falls back gracefully without crashing.
4. Method ("llm" | "glossary" | "none") is returned in API responses.
5. Scheme names in answers are formatted in English with local-script name in brackets.
"""

import pytest
from fastapi.testclient import TestClient
from api import app
import rag
from rag.query_normalizer import (
    normalize_query,
    set_mock_llm_translator,
    clear_query_normalizer_cache,
    detect_language,
    get_localized_scheme_name
)

client = TestClient(app)


def get_scheme_ids_from_results(results):
    """Extracts unique scheme IDs from retrieval results."""
    ids = []
    for r in results:
        meta = r.get("metadata", {})
        s_id = meta.get("scheme_id") or (r["entity_id"] if r["entity_type"] == "scheme" else None)
        if s_id and s_id not in ids:
            ids.append(s_id)
    return ids


def test_language_detection_script_ranges():
    """Verify Unicode script detection for Indic languages and Latin as English."""
    assert detect_language("इलेक्ट्रीशियन कोर्स") == "hi"
    assert detect_language("எலக்ட்ரீஷியன் பயிற்சி") == "ta"
    assert detect_language("ఎలక్ట్రీషియన్ కోర్సు") == "te"
    assert detect_language("ਇਲੈਕਟ੍ਰੀਸ਼ੀਅਨ ਕੋਰਸ") == "pa"
    assert detect_language("ইলেকট্রিশিয়ান কোর্স") == "bn"
    assert detect_language("ઇલેક્ટ્રિશિયન કોર્સ") == "gu"
    assert detect_language("ಎಲೆಕ್ಟ್ರಿಷಿಯನ್ ಕೋರ್ಸ್") == "kn"
    assert detect_language("ഇലക്ട്രീഷ്യൻ കോഴ്സ്") == "ml"
    assert detect_language("الیکٹریشن کورس") == "ur"
    assert detect_language("electrician training course") == "en"
    assert detect_language("какие курсы электрика") == "unknown"


def test_cross_language_retrieval_glossary_path():
    """
    Test 1: With LLM unavailable/disabled, the offline glossary path translates
    Hindi and Tamil queries so that top-3 retrieved schemes overlap with English
    by at least 2 of 3.
    """
    clear_query_normalizer_cache()
    # Force LLM translator to return None (simulating unavailable / rate limited LLM)
    set_mock_llm_translator(lambda text: None)

    q_en = "electrician course training for SC youth in Delhi"
    q_hi = "दिल्ली में अनुसूचित जाति युवाओं के लिए इलेक्ट्रीशियन कोर्स प्रशिक्षण"
    q_ta = "டெல்லியில் பட்டியல் சாதி இளைஞர்களுக்கான எலக்ட்ரீஷியன் பயிற்சி படிப்பு"

    # POST /rag/retrieve with filter_type="scheme"
    res_en = client.post("/rag/retrieve", json={"query": q_en, "k": 5, "filter_type": "scheme"})
    res_hi = client.post("/rag/retrieve", json={"query": q_hi, "k": 5, "filter_type": "scheme"})
    res_ta = client.post("/rag/retrieve", json={"query": q_ta, "k": 5, "filter_type": "scheme"})

    assert res_en.status_code == 200
    assert res_hi.status_code == 200
    assert res_ta.status_code == 200

    data_en = res_en.json()
    data_hi = res_hi.json()
    data_ta = res_ta.json()

    # English query should have method "none"
    assert data_en["method"] == "none"
    # Hindi and Tamil should have method "glossary"
    assert data_hi["method"] == "glossary"
    assert data_ta["method"] == "glossary"

    ids_en = get_scheme_ids_from_results(data_en["results"])[:3]
    ids_hi = get_scheme_ids_from_results(data_hi["results"])[:3]
    ids_ta = get_scheme_ids_from_results(data_ta["results"])[:3]

    print(f"Glossary Path Top-3:\n EN: {ids_en}\n HI: {ids_hi}\n TA: {ids_ta}")

    common_en_hi = set(ids_en).intersection(set(ids_hi))
    common_en_ta = set(ids_en).intersection(set(ids_ta))

    assert len(common_en_hi) >= 2, f"Expected >= 2 common schemes between EN and HI, got {common_en_hi}"
    assert len(common_en_ta) >= 2, f"Expected >= 2 common schemes between EN and TA, got {common_en_ta}"


def test_cross_language_retrieval_llm_path():
    """
    Test 2: With mocked LLM translation, English, Hindi, and Tamil queries
    return overlapping top-3 scheme IDs (at least 2 of 3 in common) with method="llm".
    """
    clear_query_normalizer_cache()

    def mock_translator(text):
        if any(c in text for c in ["इलेक्ट्रीशियन", "எலக்ட்ரீஷியன்"]):
            return "electrician course training for SC youth in Delhi"
        return "electrician course training for SC youth in Delhi"

    set_mock_llm_translator(mock_translator)

    q_en = "electrician course training for SC youth in Delhi"
    q_hi = "दिल्ली में अनुसूचित जाति युवाओं के लिए इलेक्ट्रीशियन कोर्स प्रशिक्षण"
    q_ta = "டெல்லியில் பட்டியல் சாதி இளைஞர்களுக்கான எலக்ட்ரீஷியன் பயிற்சி படிப்பு"

    res_en = client.post("/rag/retrieve", json={"query": q_en, "k": 5, "filter_type": "scheme"})
    res_hi = client.post("/rag/retrieve", json={"query": q_hi, "k": 5, "filter_type": "scheme"})
    res_ta = client.post("/rag/retrieve", json={"query": q_ta, "k": 5, "filter_type": "scheme"})

    assert res_en.status_code == 200
    assert res_hi.status_code == 200
    assert res_ta.status_code == 200

    data_en = res_en.json()
    data_hi = res_hi.json()
    data_ta = res_ta.json()

    assert data_en["method"] == "none"
    assert data_hi["method"] == "llm"
    assert data_ta["method"] == "llm"

    ids_en = get_scheme_ids_from_results(data_en["results"])[:3]
    ids_hi = get_scheme_ids_from_results(data_hi["results"])[:3]
    ids_ta = get_scheme_ids_from_results(data_ta["results"])[:3]

    print(f"LLM Path Top-3:\n EN: {ids_en}\n HI: {ids_hi}\n TA: {ids_ta}")

    common_en_hi = set(ids_en).intersection(set(ids_hi))
    common_en_ta = set(ids_en).intersection(set(ids_ta))

    assert len(common_en_hi) >= 2, f"Expected >= 2 common schemes between EN and HI, got {common_en_hi}"
    assert len(common_en_ta) >= 2, f"Expected >= 2 common schemes between EN and TA, got {common_en_ta}"

    # Reset mock translator
    set_mock_llm_translator(None)


def test_unknown_language_fallback_graceful():
    """Test 3: Query with an unknown script falls back gracefully without crashing."""
    clear_query_normalizer_cache()
    set_mock_llm_translator(lambda text: None)

    cyrillic_q = "какие бесплатные курсы есть в Дели"
    
    # Direct normalizer test
    norm = normalize_query(cyrillic_q)
    assert norm["detected_lang"] == "unknown"
    assert norm["method"] == "none"
    assert norm["english"] == cyrillic_q

    # API /rag/retrieve test
    res = client.post("/rag/retrieve", json={"query": cyrillic_q, "k": 3})
    assert res.status_code == 200
    data = res.json()
    assert data["detected_lang"] == "unknown"
    assert data["method"] == "none"
    assert isinstance(data["results"], list)

    # API /rag/ask test
    ask_res = client.post("/rag/ask", json={"query": cyrillic_q, "user_id": "test_unk_user"})
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert "answer" in ask_data
    assert ask_data["method"] == "none"


def test_ask_rag_localized_scheme_names():
    """Test 4: Verify answer composition includes scheme name in English with local-script name in brackets."""
    clear_query_normalizer_cache()
    set_mock_llm_translator(None)

    # Helper check
    local_name = get_localized_scheme_name("delhi-pmajay-gia", "PM-AJAY", "hi")
    assert "(" in local_name and "प्रधानमंत्री" in local_name

    # Ask RAG in Hindi
    res = client.post("/rag/ask", json={
        "query": "इलेक्ट्रीशियन कोर्स के लिए क्या पात्रता और योजना है?",
        "user_id": "test_hindi_user",
        "language": "hi"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["detected_lang"] == "hi"
    assert data["method"] in ["glossary", "llm"]
    assert "answer" in data
    assert len(data["scheme_cards"]) > 0
    # Check that at least one scheme card has local script in brackets
    card_names = [c["name"] for c in data["scheme_cards"]]
    has_bracket_or_local = any("(" in name for name in card_names)
    assert has_bracket_or_local, f"Expected local name in brackets in cards: {card_names}"
