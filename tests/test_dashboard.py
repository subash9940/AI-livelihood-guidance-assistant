"""
tests/test_dashboard.py — Tests for Rebuilt GIA Dashboard and Delhi Metrics
"""
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_dashboard_page_serves_html():
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "PM-AJAY GIA Coordination Dashboard" in res.text
    assert "theme.css" in res.text
    assert "Delhi 11-District Coverage" in res.text
    assert "Pending Beneficiary Applications" in res.text

def test_dashboard_summary_delhi_metrics():
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    data = res.json()

    # Base requirements
    assert "total_beneficiaries" in data
    assert "enrolments" in data
    assert "placements" in data
    assert "dropouts" in data
    assert "capacity_gap" in data
    assert "skill_demand_by_trade" in data
    assert "beneficiaries" in data

    # Delhi specific requirements
    assert data["region"] == "delhi"
    assert "nsqf_enrolments" in data
    assert len(data["nsqf_enrolments"]) == 4  # NSQF 3, 4, 5, 6
    assert "scheme_uptake" in data
    assert len(data["scheme_uptake"]) >= 5
    assert "district_coverage" in data
    assert len(data["district_coverage"]) == 11  # All 11 Delhi districts
    assert "pending_applications" in data
    assert len(data["pending_applications"]) >= 5
    assert "alerts" in data
    assert len(data["alerts"]) >= 3
    assert data["is_sample_data"] is True

def test_dashboard_district_filtering():
    res = client.get("/dashboard/summary?district=North%20East%20Delhi")
    assert res.status_code == 200
    data = res.json()
    assert data["selected_district"] == "North East Delhi"
    assert data["total_beneficiaries"] >= 100

    # Also test New Delhi district filtering
    res_nd = client.get("/dashboard/summary?district=New%20Delhi")
    assert res_nd.status_code == 200
    data_nd = res_nd.json()
    assert data_nd["selected_district"] == "New Delhi"
    assert data_nd["total_beneficiaries"] >= 40

def test_dashboard_application_action():
    res = client.post(
        "/dashboard/applications/APP-DL-2026-081/action",
        json={"action": "verify_docs", "note": "Documents verified via Delhi e-district"}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["action"] == "verify_docs"
