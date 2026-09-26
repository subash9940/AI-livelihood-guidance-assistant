"""
End-to-end API test script for PM-AJAY Livelihood Guidance Assistant.
Validates all endpoints:
1. POST /session/start
2. POST /session/{id}/voice-input
3. GET /session/{id}/recommendation
4. GET /dashboard/summary?district=
5. POST /followup/{beneficiary_id}
"""
from fastapi.testclient import TestClient
from api import app
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
    utterance = "I finished 10th, my family does farming, I want something food-related, I can't travel far"
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

if __name__ == "__main__":
    test_full_pipeline()
