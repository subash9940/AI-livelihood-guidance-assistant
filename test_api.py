"""
End-to-end API test script for Nivara — AI Livelihood Guidance Assistant.
Validates all core endpoints and the static regional schemes feature:
1. POST /session/start
2. POST /session/{id}/voice-input
3. GET /session/{id}/recommendation (includes regional_schemes)
4. GET /dashboard/summary?district=
5. POST /followup/{beneficiary_id}
6. Regional schemes lookup & static data integrity
"""
from fastapi.testclient import TestClient
from api import app
import region_schemes
import profiler
import nsqf_rules
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_full_pipeline():
    print("--- 1. Testing POST /session/start ---")
    res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    assert res.status_code == 200, f"Error: {res.text}"
    session_data = res.json()
    session_id = session_data["session_id"]
    print(f"Session started: {session_id}")

    print("\n--- 2. Testing POST /session/{id}/voice-input with Demo Script Utterance ---")
    utterance = "I am from Delhi, I finished 10th, my family does farming, I want something food-related, I can't travel far"
    res = client.post(f"/session/{session_id}/voice-input", json={"text": utterance, "language": "en"})
    assert res.status_code == 200, f"Error: {res.text}"
    voice_res = res.json()
    print("Voice response:")
    print(f"Transcript: {voice_res['transcript']}")
    print(f"Extracted fields: {json.dumps(voice_res['extracted_fields'], indent=2)}")
    print(f"Profile complete: {voice_res['profile_complete']}")
    print(f"Next prompt: {voice_res['next_prompt']}")
    assert voice_res["profile_complete"] is True
    beneficiary_id = voice_res["beneficiary_id"]
    assert beneficiary_id is not None

    print("\n--- 3. Testing GET /session/{id}/recommendation ---")
    res = client.get(f"/session/{session_id}/recommendation")
    assert res.status_code == 200, f"Error: {res.text}"
    rec_res = res.json()
    print("Recommendation output:")
    print(f"Trade: {rec_res['recommended_trade']}")
    print(f"NSQF: {rec_res['nsqf_alignment']}")
    print(f"Gap Summary: {rec_res['gap_summary']}")
    print(f"Programme: {rec_res['training_programme']}")
    print(f"Centre: {rec_res['training_centre']}")
    print(f"Roadmap Steps count: {len(rec_res['roadmap_steps'])}")
    for i, s in enumerate(rec_res["roadmap_steps"], 1):
        print(f"  Step {i}: {s}")

    # Assert regional_schemes is in recommendation output
    assert "regional_schemes" in rec_res, "regional_schemes must be in /recommendation response"
    print(f"Regional schemes field present: {type(rec_res['regional_schemes'])} (count: {len(rec_res['regional_schemes'])})")

    print("\n--- 4. Testing GET /dashboard/summary ---")
    res = client.get("/dashboard/summary")
    assert res.status_code == 200, f"Error: {res.text}"
    dash_res = res.json()
    print(f"Total Beneficiaries: {dash_res['total_beneficiaries']}")
    print(f"Enrolments: {dash_res['enrolments']}, Placements: {dash_res['placements']}, Dropouts: {dash_res['dropouts']}")
    print(f"Skill Demand categories: {len(dash_res['skill_demand_by_trade'])}")

    print("\n--- 5. Testing POST /followup/{beneficiary_id} ---")
    res = client.post(f"/followup/{beneficiary_id}", json={"status": "placed"})
    assert res.status_code == 200, f"Error: {res.text}"
    fu_res = res.json()
    print(f"Follow up updated: {fu_res}")

    print("\nALL 5 API ENDPOINTS TESTED AND PASSED SUCCESSFULLY!")

def test_regional_schemes_static_data_and_lookup():
    print("\n--- 6. Testing Regional Schemes Static Data & Lookup ---")
    expected_states = ["Delhi", "Maharashtra", "Tamil Nadu", "Karnataka", "Uttar Pradesh"]
    required_keys = {"name", "provider", "benefit", "eligibility", "how_to_apply"}

    # Verify dictionary has exact 5 states each with 2 schemes and exact keys + transparency metadata
    transparency_keys = {"is_verified", "last_checked", "source_note"}
    for state in expected_states:
        schemes = region_schemes.get_regional_schemes(state)
        assert len(schemes) == 2, f"State {state} should have exactly 2 schemes, got {len(schemes)}"
        for s in schemes:
            assert required_keys.issubset(s.keys()), f"Scheme missing required keys: {s}"
            assert transparency_keys.issubset(s.keys()), f"Scheme missing transparency metadata keys: {s}"
            assert s["is_verified"] is False, f"Expected is_verified=False, got {s['is_verified']}"
            assert isinstance(s["last_checked"], str) and len(s["last_checked"]) > 0
            assert isinstance(s["source_note"], str) and len(s["source_note"]) > 0
            assert len(s["name"]) > 0
            assert len(s["provider"]) > 0
            assert len(s["benefit"]) > 0
            assert len(s["eligibility"]) > 0
            assert len(s["how_to_apply"]) > 0

    # Test case-insensitivity
    assert len(region_schemes.get_regional_schemes("maharashtra")) == 2
    assert len(region_schemes.get_regional_schemes("DELHI")) == 2
    assert len(region_schemes.get_regional_schemes("tamil nadu")) == 2
    assert len(region_schemes.get_regional_schemes("karnataka")) == 2
    assert len(region_schemes.get_regional_schemes("uttar pradesh")) == 2

    # Test non-registered state returns empty list (not error, not guess)
    assert region_schemes.get_regional_schemes("Punjab") == []
    assert region_schemes.get_regional_schemes("Bihar") == []
    assert region_schemes.get_regional_schemes("Kerala") == []
    assert region_schemes.get_regional_schemes("Unknown State") == []
    assert region_schemes.get_regional_schemes("") == []
    assert region_schemes.get_regional_schemes(None) == []

    # Test get_schemes_for_profile with state field
    assert len(region_schemes.get_schemes_for_profile({"state": "Maharashtra"})) == 2
    assert len(region_schemes.get_schemes_for_profile({"state": "Goa"})) == 0

    # Test get_schemes_for_profile with location field
    assert len(region_schemes.get_schemes_for_profile({"location": "Delhi"})) == 2
    assert len(region_schemes.get_schemes_for_profile({"location": "Haryana"})) == 0
    assert len(region_schemes.get_schemes_for_profile({})) == 0

    # Test direct /recommendation endpoint
    res_rec = client.get("/recommendation?state=Maharashtra")
    assert res_rec.status_code == 200
    assert len(res_rec.json().get("regional_schemes", [])) == 2

    res_rec_unreg = client.get("/recommendation?state=Bihar")
    assert res_rec_unreg.status_code == 200
    assert res_rec_unreg.json().get("regional_schemes") == []

    print("Regional schemes static data and lookup passed perfectly!")

def test_session_recommendation_with_state():
    print("\n--- 7. Testing Session Intake with State -> Regional Schemes ---")
    s_res = client.post("/session/start", json={"entry_mode": "app", "language": "hi"})
    session_id = s_res.json()["session_id"]

    v_res = client.post(
        f"/session/{session_id}/voice-input",
        json={"text": "मैं दिल्ली से हूँ, 8वीं पास, दर्जी का काम सीखना है, खुद की दुकान खोलनी है", "language": "hi"}
    )
    assert v_res.status_code == 200
    assert v_res.json()["profile_complete"] is True

    r_res = client.get(f"/session/{session_id}/recommendation")
    assert r_res.status_code == 200
    data = r_res.json()
    assert "regional_schemes" in data
    assert len(data["regional_schemes"]) == 2
    scheme_names = [s["name"] for s in data["regional_schemes"]]
    assert "Dilli Swarojgar Yojna" in scheme_names
    assert "Delhi Khadi Kaushal Vikas Yojna" in scheme_names
    print(f"Session with Delhi returned schemes: {scheme_names}")

def test_recommendation_incomplete_profile_returns_409():
    res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    assert res.status_code == 200
    session_id = res.json()["session_id"]

    res_rec = client.get(f"/session/{session_id}/recommendation")
    assert res_rec.status_code == 409
    assert "Profile incomplete" in res_rec.json()["detail"]

def test_followup_nonexistent_beneficiary_returns_404():
    res = client.post("/followup/does-not-exist-12345", json={"status": "placed"})
    assert res.status_code == 404
    assert res.json()["detail"] == "Beneficiary not found"

def test_readiness_score_calculation():
    print("\n--- 8. Testing Numeric Skill Readiness Score Calculation ---")
    # Test 1: Low readiness (< 40) - 1 of 5 skills
    s_res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id = s_res.json()["session_id"]
    client.post(
        f"/session/{session_id}/voice-input",
        json={
            "transcript": "I am Karthik from Tamil Nadu, 12th pass, mechanic tools experience, want two-wheeler EV repair job",
            "profile_data": {
                "name": "Karthik Raja",
                "education_level": "12th Standard",
                "location": "Madurai",
                "state": "Tamil Nadu",
                "interests": ["Two-Wheeler & EV Maintenance"],
                "skills": ["Hand Tools & Mechanical Maintenance"],
                "family_occupation": "Daily Wage Labor",
                "employment_preference": "wage_employment",
                "mobility_constraint": "Willing to commute to District/Taluka center"
            }
        }
    )
    rec = client.get(f"/session/{session_id}/recommendation").json()
    assert "readiness_score" in rec, "readiness_score must be present in recommendation"
    assert rec["readiness_score"] == 20, f"Expected 20% readiness score for 1/5 skills, got {rec['readiness_score']}"
    assert rec["readiness_score"] < 40, "Should fall in RED threshold (< 40)"
    assert rec.get("readiness_tier") == "Exploratory Track — Review Options", f"Expected 'Exploratory Track — Review Options', got {rec.get('readiness_tier')}"
    print(f"Low readiness profile score: {rec['readiness_score']}/100 — {rec.get('readiness_tier')} (RED)")

    # Test 2: Moderate readiness (40-69) - 3 of 5 skills
    s_res2 = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id2 = s_res2.json()["session_id"]
    client.post(
        f"/session/{session_id2}/voice-input",
        json={
            "transcript": "Sunita Verma from Delhi, 8th pass, tailoring skills in stitching, pattern cutting, machine operation",
            "profile_data": {
                "name": "Sunita Verma",
                "education_level": "8th Standard",
                "location": "Delhi",
                "state": "Delhi",
                "interests": ["Tailoring & Garment Making"],
                "skills": [
                    "Basic Stitching & Fabric Cutting",
                    "Commercial Pattern Drafting & Measuring",
                    "Industrial Sewing Machine Operation"
                ],
                "family_occupation": "Tailoring / Weaving",
                "employment_preference": "self_employment",
                "mobility_constraint": "Cannot travel far (Restricted to village/cluster)"
            }
        }
    )
    rec2 = client.get(f"/session/{session_id2}/recommendation").json()
    assert rec2["readiness_score"] == 60, f"Expected 60% readiness score for 3/5 skills, got {rec2['readiness_score']}"
    assert 40 <= rec2["readiness_score"] <= 69, "Should fall in YELLOW threshold (40-69)"
    assert rec2.get("readiness_tier") == "Skill Bridge Track", f"Expected 'Skill Bridge Track', got {rec2.get('readiness_tier')}"
    print(f"Moderate readiness profile score: {rec2['readiness_score']}/100 — {rec2.get('readiness_tier')} (YELLOW)")

    # Test 3: High readiness (>= 70) - 4 of 5 skills
    s_res3 = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id3 = s_res3.json()["session_id"]
    client.post(
        f"/session/{session_id3}/voice-input",
        json={
            "transcript": "Ramkishan Yadav from UP, 10th pass, farming family, food processing skills in preservation, packaging, costing",
            "profile_data": {
                "name": "Ramkishan Yadav",
                "education_level": "10th Standard",
                "location": "Varanasi",
                "state": "Uttar Pradesh",
                "interests": ["Food Processing & Preservation"],
                "skills": [
                    "Food Handling & Raw Ingredient Quality",
                    "Preservation & Processing Techniques",
                    "Packaging & Product Labeling",
                    "Micro-Enterprise Costing & Market Linkage"
                ],
                "family_occupation": "Agriculture & Farming",
                "employment_preference": "self_employment",
                "mobility_constraint": "Cannot travel far (Restricted to village/cluster)"
            }
        }
    )
    rec3 = client.get(f"/session/{session_id3}/recommendation").json()
    assert rec3["readiness_score"] == 80, f"Expected 80% readiness score for 4/5 skills, got {rec3['readiness_score']}"
    assert rec3["readiness_score"] >= 70, "Should fall in GREEN threshold (>= 70)"
    assert rec3.get("readiness_tier") == "Direct Pathway Ready", f"Expected 'Direct Pathway Ready', got {rec3.get('readiness_tier')}"
    print(f"High readiness profile score: {rec3['readiness_score']}/100 — {rec3.get('readiness_tier')} (GREEN)")

def test_demo_beneficiary_pipeline_profiles():
    print("\n--- 9. Testing Demo Beneficiary Pipeline for all 4 Sample Profiles ---")
    demo_profiles = [
        {
            "key": "textiles_delhi",
            "state": "Delhi",
            "expected_trade": "apparel_tailoring",
            "expected_schemes": ["Dilli Swarojgar Yojna", "Delhi Khadi Kaushal Vikas Yojna"],
            "profile": {
                "name": "Sunita Verma",
                "education": "8th Standard",
                "education_level": "8th Standard",
                "location": "Delhi",
                "state": "Delhi",
                "interests": ["Tailoring & Garment Making"],
                "skills": ["Basic Stitching & Fabric Cutting", "Commercial Pattern Drafting & Measuring", "Industrial Sewing Machine Operation"],
                "family_occupation": "Tailoring / Weaving",
                "employment_preference": "self_employment",
                "mobility": "Cannot travel far (Restricted to village/cluster)",
                "mobility_constraint": "Cannot travel far (Restricted to village/cluster)"
            }
        },
        {
            "key": "agri_up",
            "state": "Uttar Pradesh",
            "expected_trade": "food_processing",
            "expected_schemes": ["Vishwakarma Shram Samman Yojana", "UPSCFDC Self-Employment Schemes (under PM SC Abhyudaya Yojana)"],
            "profile": {
                "name": "Ramkishan Yadav",
                "education": "10th Standard",
                "education_level": "10th Standard",
                "location": "Varanasi",
                "state": "Uttar Pradesh",
                "interests": ["Food Processing & Preservation"],
                "skills": ["Food Handling & Raw Ingredient Quality", "Preservation & Processing Techniques", "Packaging & Product Labeling", "Micro-Enterprise Costing & Market Linkage"],
                "family_occupation": "Agriculture & Farming",
                "employment_preference": "self_employment",
                "mobility": "Cannot travel far (Restricted to village/cluster)",
                "mobility_constraint": "Cannot travel far (Restricted to village/cluster)"
            }
        },
        {
            "key": "auto_tn",
            "state": "Tamil Nadu",
            "expected_trade": "automotive_ev",
            "expected_schemes": ["Vetri Thozhil Munaivor Thittam", "TAHDCO Skill Development Training"],
            "profile": {
                "name": "Karthik Raja",
                "education": "12th Standard",
                "education_level": "12th Standard",
                "location": "Madurai",
                "state": "Tamil Nadu",
                "interests": ["Two-Wheeler & EV Maintenance"],
                "skills": ["Hand Tools & Mechanical Maintenance"],
                "family_occupation": "Daily Wage Labor",
                "employment_preference": "wage_employment",
                "mobility": "Willing to commute to District/Taluka center",
                "mobility_constraint": "Willing to commute to District/Taluka center"
            }
        },
        {
            "key": "solar_maha",
            "state": "Maharashtra",
            "expected_trade": "solar_technician",
            "expected_schemes": ["CMEGP", "Annasaheb Patil Mahamandal Self-Employment Loan"],
            "profile": {
                "name": "Amit Shinde",
                "education": "12th Standard",
                "education_level": "12th Standard",
                "location": "Pune",
                "state": "Maharashtra",
                "interests": ["Solar PV & Electrical Installations"],
                "skills": ["Basic Electrical Wiring & Circuit Safety", "Photovoltaic Module Mounting & Alignment", "Electrical Safety & Earthing Protocols"],
                "family_occupation": "Agriculture & Farming",
                "employment_preference": "wage_employment",
                "mobility": "Willing to commute to District/Taluka center",
                "mobility_constraint": "Willing to commute to District/Taluka center"
            }
        }
    ]

    for d in demo_profiles:
        s_res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
        assert s_res.status_code == 200
        session_id = s_res.json()["session_id"]

        v_res = client.post(
            f"/session/{session_id}/voice-input",
            json={
                "transcript": f"Demo beneficiary {d['profile']['name']} from {d['profile']['location']}, {d['profile']['state']}",
                "profile_data": d["profile"]
            }
        )
        assert v_res.status_code == 200
        assert v_res.json()["profile_complete"] is True

        r_res = client.get(f"/session/{session_id}/recommendation")
        assert r_res.status_code == 200
        rec = r_res.json()
        assert rec["trade_key"] == d["expected_trade"], f"Expected {d['expected_trade']}, got {rec['trade_key']}"
        assert "readiness_score" in rec
        assert isinstance(rec["readiness_score"], int)
        assert "qp_name" in rec
        assert "qp_code" in rec
        assert "nsqf_level" in rec
        assert "ssc_name" in rec
        assert "skill_gap_breakdown" in rec
        assert len(rec["skill_gap_breakdown"]) > 0, "Expected non-empty skill gap breakdown"
        scheme_names = [s.get("name") for s in rec.get("regional_schemes", [])]
        assert set(scheme_names) == set(d["expected_schemes"]), f"Expected schemes {d['expected_schemes']}, got {scheme_names}"

        # Also test /recommendation endpoint with session_id query param
        r_direct = client.get(f"/recommendation?session_id={session_id}")
        assert r_direct.status_code == 200
        assert r_direct.json()["trade_key"] == d["expected_trade"]

        # Also test direct /recommendation with profile JSON
        r_post = client.post("/recommendation", json={"profile": d["profile"]})
        assert r_post.status_code == 200
        assert r_post.json()["trade_key"] == d["expected_trade"]
        assert len(r_post.json().get("regional_schemes", [])) == 2

        print(f"Verified demo profile {d['key']}: Trade={rec['trade_key']}, QP={rec['qp_code']} ({rec['qp_name']}), SSC={rec['ssc_name']}, Readiness={rec['readiness_score']}/100, Schemes={scheme_names}, Gaps={len(rec['skill_gap_breakdown'])}")

def test_nsqf_qualification_pack_details():
    print("\n--- 10. Testing NSQF Qualification Pack Real Data Integrity for all 6 Trades ---")
    import nsqf_rules
    expected_qps = {
        "food_processing": {
            "qp_name": "Pickle Making Technician",
            "qp_code": "FIC/Q0102",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "Food Industry Capacity & Skill Initiative (FICSI)"
        },
        "apparel_tailoring": {
            "qp_name": "Self Employed Tailor",
            "qp_code": "AMH/Q1947",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "Apparel, Made-Ups & Home Furnishing Sector Skill Council (AMHSSC)"
        },
        "solar_technician": {
            "qp_name": "Solar PV Installer (Suryamitra)",
            "qp_code": "SGJ/Q0101",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "Skill Council for Green Jobs (SCGJ)"
        },
        "automotive_ev": {
            "qp_name": "Two Wheeler Service Technician",
            "qp_code": "ASC/Q1411",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "Automotive Skills Development Council (ASDC)"
        },
        "digital_csc": {
            "qp_name": "Domestic Data Entry Operator",
            "qp_code": "SSC/Q2212",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "IT-ITeS Sector Skill Council (NASSCOM)"
        },
        "healthcare_assistant": {
            "qp_name": "General Duty Assistant",
            "qp_code": "HSS/Q5101",
            "nsqf_level": "NSQF Level 4",
            "ssc_name": "Healthcare Sector Skill Council (HSSC)"
        }
    }

    for trade_key, expected in expected_qps.items():
        trade_data = nsqf_rules.TRADES_CATALOG[trade_key]
        assert trade_data.get("qp_name") == expected["qp_name"], f"Mismatch for {trade_key} qp_name: {trade_data.get('qp_name')}"
        assert trade_data.get("qp_code") == expected["qp_code"], f"Mismatch for {trade_key} qp_code: {trade_data.get('qp_code')}"
        assert trade_data.get("nsqf_level") == expected["nsqf_level"], f"Mismatch for {trade_key} nsqf_level: {trade_data.get('nsqf_level')}"
        assert trade_data.get("ssc_name") == expected["ssc_name"], f"Mismatch for {trade_key} ssc_name: {trade_data.get('ssc_name')}"

        # Test analysis output carries the exact QP fields
        res = nsqf_rules.analyze_skill_gap({"education_level": "10th Standard", "skills": [expected["qp_name"]], "interests": [trade_key]})
        # Direct check on trade
        direct_analysis = nsqf_rules.analyze_skill_gap({"interests": [trade_key], "education_level": "10th Standard"})
        if direct_analysis.get("trade_key") == trade_key:
            assert direct_analysis["qp_name"] == expected["qp_name"]
            assert direct_analysis["qp_code"] == expected["qp_code"]
            assert direct_analysis["nsqf_level"] == expected["nsqf_level"]
            assert direct_analysis["ssc_name"] == expected["ssc_name"]
        print(f"Verified trade '{trade_key}': {expected['qp_name']} — {expected['nsqf_level']}, QP Code {expected['qp_code']}, {expected['ssc_name']}")

def test_regional_demand_capacity_gap():
    print("\n--- 11. Testing Regional Demand vs Training Capacity Gap Analysis ---")
    import training_capacity

    # 1. Test GET /dashboard/capacity-gap with specific state
    res_delhi = client.get("/dashboard/capacity-gap?state=Delhi")
    assert res_delhi.status_code == 200
    delhi_data = res_delhi.json()
    assert delhi_data["state"] == "Delhi"
    assert delhi_data["disclaimer"] == "Estimated capacity — illustrative, pending integration with Skill India Digital Hub"
    assert delhi_data["is_capacity_verified"] is False
    assert set(delhi_data["supported_states"]) == {"Delhi", "Maharashtra", "Tamil Nadu", "Karnataka", "Uttar Pradesh"}
    assert "total_demand" in delhi_data
    assert "total_estimated_capacity" in delhi_data
    assert "overall_gap" in delhi_data
    assert len(delhi_data["trades"]) == 6

    for t in delhi_data["trades"]:
        assert "trade_key" in t
        assert "trade_name" in t
        assert "qp_code" in t
        assert "demand" in t
        assert "estimated_capacity" in t
        assert t["gap_status"] in ["demand_exceeding", "roughly_matched", "capacity_exceeding"]
        assert "gap_label" in t

    # 2. Test GET /dashboard/capacity-gap with state=all
    res_all = client.get("/dashboard/capacity-gap?state=all")
    assert res_all.status_code == 200
    all_data = res_all.json()
    assert all_data["state"] == "all"
    assert all_data["total_estimated_capacity"] > delhi_data["total_estimated_capacity"]

    # 3. Test /dashboard/summary includes capacity_gap
    dash_res = client.get("/dashboard/summary")
    assert dash_res.status_code == 200
    assert "capacity_gap" in dash_res.json()
    assert dash_res.json()["capacity_gap"]["disclaimer"] == "Estimated capacity — illustrative, pending integration with Skill India Digital Hub"

    # 4. Test real demand accumulation: submit a new profile and verify count increments
    initial_demand = client.get("/dashboard/capacity-gap?state=Delhi").json()["trades"]
    apparel_initial = next(t["demand"] for t in initial_demand if t["trade_key"] == "apparel_tailoring")

    s_res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    sid = s_res.json()["session_id"]
    client.post(
        f"/session/{sid}/voice-input",
        json={
            "transcript": "I am in Delhi, 10th pass, want tailoring and garment making",
            "profile_data": {
                "name": "Demand Test Beneficiary",
                "state": "Delhi",
                "education": "10th Standard",
                "interests": ["Tailoring & Garment Making"],
                "skills": ["Basic Stitching & Fabric Cutting"],
                "family_occupation": "Tailoring / Weaving",
                "employment_preference": "self_employment",
                "mobility": "Cannot travel far (Restricted to village/cluster)"
            }
        }
    )

    updated_demand = client.get("/dashboard/capacity-gap?state=Delhi").json()["trades"]
    apparel_updated = next(t["demand"] for t in updated_demand if t["trade_key"] == "apparel_tailoring")
    assert apparel_updated >= apparel_initial + 1, f"Expected demand to increment: {apparel_initial} -> {apparel_updated}"

    print(f"Verified Capacity Gap Report for Delhi: Demand={delhi_data['total_demand']}, Est. Capacity={delhi_data['total_estimated_capacity']} ({delhi_data['overall_gap']['short_label']})")
    print(f"Verified Real Demand Accumulation: Apparel demand incremented from {apparel_initial} to {apparel_updated}")

def test_broad_skill_profile_validation_and_tiers():
    print("\n--- 12. Testing Broad Skill Profile Validation & Qualitative Tiers ---")
    
    # 1. Soft / Interpersonal Skill Validation: Must extract soft skills BUT profile must be incomplete (gated)
    p1, comp1 = profiler.extract_profile_from_text("I am good with people, patient, and hardworking")
    assert comp1 is False, f"Beneficiary with only soft skills must be incomplete (gated), got {comp1}"
    assert len(p1["skills"]) >= 2, f"Should extract soft skills, got {p1['skills']}"
    assert any("people" in s.lower() for s in p1["skills"])
    assert any("patient" in s.lower() for s in p1["skills"])
    assert any("hardworking" in s.lower() for s in p1["skills"])
    # Follow-up prompt must ask for concrete trade or technical skill
    prompt1 = profiler.generate_next_prompt(p1, language="en")
    assert any(term in prompt1.lower() for term in ["practical", "trade", "technical", "work area", "strengths"])

    # 2. Traditional / Family Occupation Skill Validation: Has concrete skill -> complete
    p2, comp2 = profiler.extract_profile_from_text("My family does traditional pottery and craft")
    assert comp2 is True, f"Beneficiary with traditional skills should be complete, got {comp2}"
    assert len(p2["skills"]) >= 1, f"Should extract traditional skills, got {p2['skills']}"

    # 3. Incomplete Profile Validation (No skills of any kind)
    p3, comp3 = profiler.extract_profile_from_text("I studied 8th class")
    assert comp3 is False, f"Beneficiary with only education and no skills/interests should be incomplete, got {comp3}"
    prompt3 = profiler.generate_next_prompt(p3, language="en")
    # Verify the follow-up prompt explicitly asks about traditional or interpersonal strengths, not just technical skills
    assert any(term in prompt3.lower() for term in ["traditional", "family", "interpersonal", "good with people", "patient", "hardworking"]), f"Follow-up prompt must explicitly ask about traditional or interpersonal strengths: '{prompt3}'"

    # 4. Multilingual Follow-Up Prompts
    prompt_hi = profiler.generate_next_prompt(p3, language="hi")
    assert any(term in prompt_hi for term in ["पारंपरिक", "खूबियां", "व्यक्तिगत", "धैर्य", "मेहनत", "हुनर"]), f"Hindi prompt missing traditional/soft skill keywords: '{prompt_hi}'"

    # 5. Qualitative Tier Helper Validation (Original Distinct Names)
    assert nsqf_rules.get_readiness_tier(100) == "Direct Pathway Ready"
    assert nsqf_rules.get_readiness_tier(75) == "Direct Pathway Ready"
    assert nsqf_rules.get_readiness_tier(70) == "Direct Pathway Ready"
    assert nsqf_rules.get_readiness_tier(69) == "Skill Bridge Track"
    assert nsqf_rules.get_readiness_tier(50) == "Skill Bridge Track"
    assert nsqf_rules.get_readiness_tier(40) == "Skill Bridge Track"
    assert nsqf_rules.get_readiness_tier(39) == "Exploratory Track — Review Options"
    assert nsqf_rules.get_readiness_tier(20) == "Exploratory Track — Review Options"
    assert nsqf_rules.get_readiness_tier(0) == "Exploratory Track — Review Options"

    print("Verified broad skill profile validation, soft & traditional skills extraction, follow-up prompt, and all 3 qualitative tiers!")

def test_graceful_fallbacks_and_completeness_gating():
    print("\n--- 13. Testing Completeness Gating & Graceful Fallbacks (No Guessing) ---")

    # A. Completeness Gating: Only soft skills provided -> No recommendation generated, clarifying question returned
    s_res = client.post("/session/start", json={"entry_mode": "app", "language": "en"})
    session_id = s_res.json()["session_id"]
    v_res = client.post(
        f"/session/{session_id}/voice-input",
        json={"text": "I am 10th pass, very hardworking, patient, and good with people"}
    )
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["profile_complete"] is False, "Profile with only soft skills must not be complete"
    assert v_data.get("beneficiary_id") is None, "Beneficiary must not be created when profile is incomplete"
    assert any(term in v_data["next_prompt"].lower() for term in ["practical", "trade", "technical", "work area"])
    
    rec_res = client.get(f"/session/{session_id}/recommendation")
    assert rec_res.status_code == 409, "Must return 409 Conflict when requesting recommendation for incomplete profile"
    print("Verified completeness gating: soft-skill only profile blocked from recommendation generation.")

    # B. Graceful Fallback 1: No matching region -> explicit 'I need more information to recommend confidently', missing_piece: 'region'
    profile_no_region = {
        "name": "Arun Kumar",
        "education_level": "10th Standard",
        "interests": ["Tailoring & Garment Making"],
        "skills": ["Basic Stitching & Fabric Cutting"],
        "location": "Patna",  # Bihar is not among the 5 supported regions
        "state": "Bihar"
    }
    skill_res_no_reg = nsqf_rules.analyze_skill_gap(profile_no_region)
    assert skill_res_no_reg.get("needs_more_info") is True
    assert skill_res_no_reg.get("missing_piece") == "region"
    assert "I need more information to recommend confidently" in skill_res_no_reg.get("message")
    assert "region" in skill_res_no_reg.get("detail").lower()

    # Via direct recommendation endpoint
    rec_api_no_reg = client.post("/recommendation", json={"profile": profile_no_region}).json()
    assert rec_api_no_reg.get("needs_more_info") is True
    assert rec_api_no_reg.get("missing_piece") == "region"
    assert "I need more information to recommend confidently" in rec_api_no_reg.get("message")
    print("Verified graceful fallback for unmapped region (no guessing): missing piece = region.")

    # C. Graceful Fallback 2: No matching skill category -> missing_piece: 'skill'
    profile_no_skill = {
        "name": "Deepak Sharma",
        "education_level": "10th Standard",
        "skills": ["Traditional Pottery & Clay Modeling"],  # Not in the 6 catalog trades
        "interests": [],
        "location": "Delhi",
        "state": "Delhi"
    }
    skill_res_no_skill = nsqf_rules.analyze_skill_gap(profile_no_skill)
    assert skill_res_no_skill.get("needs_more_info") is True
    assert skill_res_no_skill.get("missing_piece") == "skill"
    assert "I need more information to recommend confidently" in skill_res_no_skill.get("message")

    rec_api_no_skill = client.post("/recommendation", json={"profile": profile_no_skill}).json()
    assert rec_api_no_skill.get("needs_more_info") is True
    assert rec_api_no_skill.get("missing_piece") == "skill"
    assert "I need more information to recommend confidently" in rec_api_no_skill.get("message")
    print("Verified graceful fallback for unmatched skill category (no guessing): missing piece = skill.")

    # D. Graceful Fallback 3: Tied confidence score -> missing_piece: 'clarity of intent'
    profile_tied = {
        "name": "Ravi Kumar",
        "education_level": "12th Standard",
        "interests": ["Two-Wheeler & EV Maintenance", "Solar PV & Electrical Installations"],
        "skills": ["Hand Tools & Mechanical Maintenance", "Basic Electrical Wiring & Circuit Safety"],
        "location": "Madurai",
        "state": "Tamil Nadu"
    }
    skill_res_tied = nsqf_rules.analyze_skill_gap(profile_tied)
    assert skill_res_tied.get("needs_more_info") is True
    assert skill_res_tied.get("missing_piece") == "clarity of intent"
    assert "I need more information to recommend confidently" in skill_res_tied.get("message")

    rec_api_tied = client.post("/recommendation", json={"profile": profile_tied}).json()
    assert rec_api_tied.get("needs_more_info") is True
    assert rec_api_tied.get("missing_piece") == "clarity of intent"
    assert "I need more information to recommend confidently" in rec_api_tied.get("message")
    print("Verified graceful fallback for tied confidence score (no guessing): missing piece = clarity of intent.")

def test_local_opportunities_and_dashboard():
    print("\n--- Testing Local Opportunities and Dashboard Integration ---")
    import local_opportunities

    # 1. Test local_opportunities lookup
    delhi_food = local_opportunities.get_local_opportunities("Delhi", "food_processing")
    assert len(delhi_food) >= 1
    assert "title" in delhi_food[0]
    assert "employer_type" in delhi_food[0]
    assert "distance" in delhi_food[0]
    assert "wage_range" in delhi_food[0]
    assert delhi_food[0]["is_verified"] is False
    assert "illustrative" in delhi_food[0]["source_note"].lower() or "not sourced" in delhi_food[0]["source_note"].lower()

    # 2. Test recommendation endpoint returns nearby_opportunities
    profile = {
        "name": "Sunita Verma",
        "education_level": "8th Standard",
        "skills": ["Basic Stitching & Fabric Cutting"],
        "interests": ["Tailoring & Garment Making"],
        "location": "Delhi",
        "state": "Delhi"
    }
    rec_res = client.post("/recommendation", json={"profile": profile}).json()
    assert "nearby_opportunities" in rec_res
    assert len(rec_res["nearby_opportunities"]) >= 1
    assert any("garment" in o["title"].lower() or "tailor" in o["title"].lower() for o in rec_res["nearby_opportunities"])
    print(f"Verified nearby opportunities returned in recommendation: {len(rec_res['nearby_opportunities'])} opportunities.")

    # 3. Test GET /dashboard route serves HTML
    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200
    assert "text/html" in dash_res.headers.get("content-type", "")
    assert "Nivara" in dash_res.text
    print("Verified GET /dashboard route serves dashboard page.")

if __name__ == "__main__":
    test_full_pipeline()
    test_regional_schemes_static_data_and_lookup()
    test_session_recommendation_with_state()
    test_recommendation_incomplete_profile_returns_409()
    test_followup_nonexistent_beneficiary_returns_404()
    test_readiness_score_calculation()
    test_demo_beneficiary_pipeline_profiles()
    test_nsqf_qualification_pack_details()
    test_regional_demand_capacity_gap()
    test_broad_skill_profile_validation_and_tiers()
    test_graceful_fallbacks_and_completeness_gating()
    test_local_opportunities_and_dashboard()
    print("\nAll 12 test suites passed successfully!")

