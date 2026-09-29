"""
Comprehensive Unit Tests for Phase 2: RAG + Memory Layer + Deterministic Eligibility Engine.
"""
import pytest
from starlette.testclient import TestClient

import rag
import delhi_data_loader as ddl
from api import app

client = TestClient(app)


def test_vector_store_retrieval():
    # 1. General search
    results = rag.retrieve("solar rooftop electrician technician", k=3)
    assert len(results) > 0
    top = results[0]
    assert "text" in top
    assert "title" in top
    assert top["score"] > 0
    assert any(term in top["text"].lower() for term in ["solar", "electrician", "suryamitra"])

    # 2. Filter by type
    scheme_results = rag.retrieve("loan", k=5, filter_type="scheme")
    assert len(scheme_results) > 0
    for r in scheme_results:
        assert r["entity_type"] == "scheme"


def test_deterministic_eligibility_engine_eligible():
    pmajay = ddl.get_scheme_by_id("delhi-pmajay-gia")
    assert pmajay is not None

    eligible_profile = {
        "name": "Rohan Kumar",
        "category": "SC",
        "age": 22,
        "education": "10th Standard",
        "income": 150000,
        "gender": "male",
        "location": "Delhi",
        "documents_held": ["Aadhaar Card", "Caste Certificate (SC)", "Income Certificate"]
    }

    eval_res = rag.check_eligibility(eligible_profile, pmajay)
    assert eval_res["eligible"] is True
    assert eval_res["match_percentage"] == 100
    assert len(eval_res["unmet_criteria"]) == 0
    assert len(eval_res["met_criteria"]) >= 4

    # Missing documents verified against DSFDC composite loan which has documents_required list
    dsfdc = ddl.get_scheme_by_id("dsfdc-composite-loan")
    assert dsfdc is not None
    eval_dsfdc = rag.check_eligibility(eligible_profile, dsfdc)
    assert any("processing fee" in doc or "Loan application" in doc or "Workplace" in doc for doc in eval_dsfdc["missing_documents"])


def test_deterministic_eligibility_engine_ineligible():
    pmajay = ddl.get_scheme_by_id("delhi-pmajay-gia")
    assert pmajay is not None

    # Ineligible profile: General category (PM-AJAY restricted to SC)
    ineligible_profile = {
        "name": "Test User",
        "category": "General",
        "age": 55,
        "education": "None",
        "income": 500000,
        "gender": "male",
        "location": "Delhi"
    }

    eval_res = rag.check_eligibility(ineligible_profile, pmajay)
    assert eval_res["eligible"] is False
    assert len(eval_res["unmet_criteria"]) >= 1
    unmet_text = " ".join(eval_res["unmet_criteria"]).lower()
    assert "category mismatch" in unmet_text


def test_pmajay_income_priority_not_cutoff():
    """PM-AJAY with income 4 lakh stays eligible with lower priority note."""
    pmajay = ddl.get_scheme_by_id("pm-ajay-gia")
    assert pmajay is not None
    profile_4lakh = {
        "name": "Suresh Kumar",
        "category": "SC",
        "age": 28,
        "education": "12th Standard",
        "income": 400000,
        "gender": "male",
        "location": "Delhi"
    }
    eval_res = rag.check_eligibility(profile_4lakh, pmajay)
    assert eval_res["eligible"] is True
    assert len(eval_res["unmet_criteria"]) == 0
    notes_text = " ".join(eval_res["notes"]).lower()
    assert "lower priority" in notes_text or "priority" in notes_text


def test_dsfdc_hard_cap_ineligible():
    """DSFDC with income 1.5 lakh exceeds the 1.20 lakh hard cap and is ineligible."""
    dsfdc = ddl.get_scheme_by_id("dsfdc-composite-loan")
    assert dsfdc is not None
    profile_1_5lakh = {
        "name": "Amit Kumar",
        "category": "SC",
        "age": 25,
        "education": "10th Standard",
        "income": 150000,
        "gender": "male",
        "location": "Delhi"
    }
    eval_res = rag.check_eligibility(profile_1_5lakh, dsfdc)
    assert eval_res["eligible"] is False
    assert any("Income Limit Exceeded" in c or "120,000" in c for c in eval_res["unmet_criteria"])


def test_stand_up_india_never_eligible():
    """Stand-Up India has active=false and never returns eligible; returns status note."""
    standup = ddl.get_scheme_by_id("stand-up-india")
    assert standup is not None
    perfect_profile = {
        "name": "Sunita Devi",
        "category": "SC",
        "age": 30,
        "education": "Graduate",
        "income": 100000,
        "gender": "female",
        "location": "Delhi"
    }
    eval_res = rag.check_eligibility(perfect_profile, standup)
    assert eval_res["eligible"] is False
    assert eval_res["active"] is False
    assert eval_res["status_note"] is not None
    assert any("Scheme Inactive" in c for c in eval_res["unmet_criteria"])


def test_user_memory_store_lifecycle():
    user_id = "test_user_memory_001"
    # Ensure fresh start
    rag.UserMemoryStore.delete_user_data(user_id)

    # 1. Create and update profile
    profile_data = {
        "name": "Pooja Rani",
        "age": 24,
        "category": "SC",
        "education": "12th Standard",
        "skills": ["Sewing", "Embroidery"],
        "district": "North East Delhi",
        "income": 120000
    }
    rag.UserMemoryStore.update_profile(user_id, profile_data)
    rag.UserMemoryStore.record_consent(user_id, True)

    bundle = rag.UserMemoryStore.get_full_memory_bundle(user_id)
    assert bundle["profile"]["name"] == "Pooja Rani"
    assert bundle["consent_given"] is True

    # 2. Add conversation history
    rag.UserMemoryStore.add_conversation_turn(user_id, "user", "What tailoring schemes are available in Delhi?")
    rag.UserMemoryStore.add_conversation_turn(user_id, "assistant", "You can apply for Dilli Swarojgar Yojna or JSS tailoring course.")
    history = rag.UserMemoryStore.get_conversation_history(user_id)
    assert len(history) == 2

    # 3. Set goal and track application
    rag.UserMemoryStore.set_user_goal(user_id, "Become certified apparel boutique owner", target_trade="apparel_tailoring", nsqf_level=4)
    rag.UserMemoryStore.save_scheme_to_plan(user_id, "delhi-dilli-swarojgar-yojna", "Dilli Swarojgar Yojna")
    rag.UserMemoryStore.update_application_progress(user_id, "delhi-dilli-swarojgar-yojna", "documents_verified", current_step=2)

    apps = rag.UserMemoryStore.get_applications(user_id)
    assert len(apps) == 1
    assert apps[0]["scheme_id"] == "delhi-dilli-swarojgar-yojna"
    assert apps[0]["status"] == "documents_verified"
    assert apps[0]["current_step"] == 2

    # 4. Clean up / right to be forgotten
    del_ok = rag.UserMemoryStore.delete_user_data(user_id)
    assert del_ok is True
    fresh_bundle = rag.UserMemoryStore.get_full_memory_bundle(user_id)
    assert fresh_bundle["profile"] == {}
    assert len(fresh_bundle["applications"]) == 0


def test_answer_pipeline_english_and_hindi():
    user_id = "test_eval_user_rag"
    rag.UserMemoryStore.update_profile(user_id, {
        "name": "Amit",
        "category": "SC",
        "education": "10th Standard",
        "age": 21,
        "income": 180000,
        "location": "Delhi"
    })

    # Test English query with eligibility evaluation
    res_en = rag.ask_rag(
        query="Am I eligible for PM-AJAY grants in Delhi and what are the benefits?",
        user_id=user_id,
        language="en"
    )
    assert res_en["answer"]
    assert len(res_en["citations"]) > 0
    assert res_en["citations"][0]["url"].startswith("http")
    assert len(res_en["scheme_cards"]) > 0
    assert len(res_en["eligibility_evaluations"]) > 0
    assert res_en["eligibility_evaluations"][0]["eligible"] is True

    # Test Hindi query
    res_hi = rag.ask_rag(
        query="दिल्ली स्वरोज़गार योजना के लिए क्या दस्तावेज़ चाहिए?",
        user_id=user_id,
        language="hi"
    )
    assert res_hi["answer"]
    assert "दस्तावेज़" in res_hi["answer"] or "Aadhaar" in res_hi["answer"] or "प्रमाण" in res_hi["answer"]

    rag.UserMemoryStore.delete_user_data(user_id)


def test_api_rag_endpoints():
    # POST /rag/retrieve
    ret_resp = client.post("/rag/retrieve", json={"query": "electrician", "k": 3})
    assert ret_resp.status_code == 200
    data = ret_resp.json()
    assert data["count"] > 0
    assert len(data["results"]) <= 3

    # POST /rag/ask
    ask_resp = client.post("/rag/ask", json={
        "query": "Where can I get solar training in Delhi?",
        "user_id": "api_test_user",
        "language": "en"
    })
    assert ask_resp.status_code == 200
    ask_data = ask_resp.json()
    assert "answer" in ask_data
    assert len(ask_data["citations"]) > 0

    # POST /rag/eligibility
    elig_resp = client.post("/rag/eligibility", json={
        "profile": {"category": "SC", "age": 25, "education": "10th Standard", "income": 100000, "location": "Delhi"},
        "scheme_id": "delhi-pmajay-gia"
    })
    assert elig_resp.status_code == 200
    elig_data = elig_resp.json()
    assert elig_data["eligible"] is True
    assert elig_data["match_percentage"] == 100

    # GET /rag/saathi/proactive/{user_id}
    pro_resp = client.get("/rag/saathi/proactive/api_test_user")
    assert pro_resp.status_code == 200
    pro_data = pro_resp.json()
    assert "next_best_step" in pro_data
    assert "goal_progress" in pro_data
    assert "reminders" in pro_data
    assert "suggested_schemes" in pro_data
    assert len(pro_data["reminders"]) >= 2
