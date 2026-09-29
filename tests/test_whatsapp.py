"""
Unit Tests for Phase 5: WhatsApp Integration & In-App Simulator.
Tests Twilio Webhook, TwiML generation, profile lookup by phone number,
reminders, and low-literacy numbered menu shortcuts.
"""
import pytest
from starlette.testclient import TestClient

from api import app
import whatsapp_service

client = TestClient(app)


def test_phone_normalization_and_profile_lookup():
    p1 = whatsapp_service.get_profile_by_phone("whatsapp:+919810123456")
    assert p1["name"] == "Rohan Kumar"
    assert p1["district"] == "South Delhi"
    assert p1["category"] == "SC"

    p2 = whatsapp_service.get_profile_by_phone("9876543210")
    assert p2["phone"] == "9876543210"


def test_whatsapp_menu_shortcuts():
    phone = "whatsapp:+919810123456"

    # 1. Main Menu
    res0 = whatsapp_service.handle_whatsapp_message(phone, "0", language="en")
    assert "Reply with a number" in res0["reply"] or "1" in res0["reply"]
    assert res0["menu_active"] is True

    # 2. Option 1: Schemes
    res1 = whatsapp_service.handle_whatsapp_message(phone, "1", language="en")
    assert "PM-AJAY" in res1["reply"] or "Scheme" in res1["reply"] or "Loan" in res1["reply"]

    # 3. Option 2: Centres
    res2 = whatsapp_service.handle_whatsapp_message(phone, "2", language="en")
    assert "Delhi" in res2["reply"]
    assert "ITI" in res2["reply"] or "Centre" in res2["reply"] or "PMKK" in res2["reply"]

    # 4. Option 3: Eligibility & Documents
    res3 = whatsapp_service.handle_whatsapp_message(phone, "3", language="en")
    assert "Eligibility" in res3["reply"] or "Documents" in res3["reply"] or "Caste Certificate" in res3["reply"]

    # 5. Option 4: Deadlines & Reminders
    res4 = whatsapp_service.handle_whatsapp_message(phone, "4", language="en")
    assert "Reminders" in res4["reply"] or "Deadline" in res4["reply"] or "batch" in res4["reply"].lower()

    # 6. Natural language query via RAG
    res_rag = whatsapp_service.handle_whatsapp_message(phone, "Can I get stipend during electrical course in Delhi?", language="en")
    assert len(res_rag["reply"]) > 20
    assert "PM" in res_rag["reply"] or "Scheme" in res_rag["reply"] or "http" in res_rag["reply"]


def test_twilio_webhook_endpoint():
    # Send form data as Twilio does
    resp = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919810123456",
            "To": "whatsapp:+14155238886",
            "Body": "1"
        }
    )
    assert resp.status_code == 200
    assert "application/xml" in resp.headers["content-type"]
    xml_content = resp.text
    assert "<Response>" in xml_content
    assert "<Message>" in xml_content
    assert "</Message>" in xml_content
    assert "</Response>" in xml_content


def test_whatsapp_simulator_endpoint_and_page():
    # API simulation
    sim_resp = client.post(
        "/api/whatsapp/simulate",
        json={
            "from_number": "9810123456",
            "body": "3",
            "language": "en"
        }
    )
    assert sim_resp.status_code == 200
    data = sim_resp.json()
    assert "reply" in data
    assert "profile" in data
    assert data["profile"]["name"] == "Rohan Kumar"

    # HTML page serve
    page_resp = client.get("/whatsapp")
    assert page_resp.status_code == 200
    assert "Nivara — WhatsApp Service Simulator" in page_resp.text
