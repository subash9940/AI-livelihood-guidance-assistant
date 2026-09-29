"""
Unit Tests for Phase 4: Security Hardening.
Tests:
1. Fernet encrypt/decrypt round trip for sensitive profile fields (caste category, income bracket, phone).
2. Verification of at-rest encryption in SQLite memory store (values stored as ciphertexts).
3. Hard deletion verification on UserMemoryStore.delete_user_data / DELETE /rag/memory/{user_id}.
4. WhatsApp webhook X-Twilio-Signature verification:
   - Rejection with 403 on invalid/missing signature when TWILIO_AUTH_TOKEN is set.
   - Acceptance with 200 on valid signature.
   - Simulator bypass with warning when X-Simulator header is present.
"""
import os
import json
import sqlite3
import pytest
import hmac
import hashlib
import base64
from starlette.testclient import TestClient

from api import app
import rag.memory_store as mem
from whatsapp_router import validate_twilio_signature

client = TestClient(app)


def test_fernet_key_and_round_trip():
    """Verifies that Fernet key is generated and encrypt/decrypt round trip preserves data."""
    f = mem.get_fernet()
    assert f is not None

    # Test round trip on sensitive values
    caste_original = "SC"
    caste_encrypted = mem.encrypt_value(caste_original)
    assert caste_encrypted != caste_original
    assert caste_encrypted.startswith("gAAAAA")
    assert mem.decrypt_value(caste_encrypted) == caste_original

    income_original = 180000
    income_encrypted = mem.encrypt_value(income_original)
    assert income_encrypted != income_original
    assert income_encrypted.startswith("gAAAAA")
    assert int(mem.decrypt_value(income_encrypted)) == income_original

    phone_original = "+919810123456"
    phone_encrypted = mem.encrypt_value(phone_original)
    assert phone_encrypted != phone_original
    assert phone_encrypted.startswith("gAAAAA")
    assert mem.decrypt_value(phone_encrypted) == phone_original


def test_sqlite_memory_store_at_rest_encryption_and_deletion():
    """
    Verifies that sensitive fields are stored encrypted AT REST in SQLite,
    retrieved as clean plaintext by applications, and deleted completely upon request.
    """
    test_uid = "sec_test_user_789"
    test_profile = {
        "name": "Amit Kumar",
        "category": "SC",
        "annual_income": 120000,
        "income_bracket": "< ₹2.5 Lakh",
        "phone": "9812345678",
        "district": "North Delhi",
        "education": "10th Standard"
    }

    # 1. Update profile in memory store
    mem.UserMemoryStore.update_profile(test_uid, test_profile)

    # 2. Check RAW SQLite row directly to verify AT-REST encryption
    conn = mem.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT profile_json FROM user_memory WHERE user_id = ?", (test_uid,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None, "User record must exist in user_memory"
    raw_stored_json = json.loads(row["profile_json"])

    # Non-sensitive field must remain readable
    assert raw_stored_json["name"] == "Amit Kumar"
    assert raw_stored_json["district"] == "North Delhi"

    # SENSITIVE fields MUST be encrypted at rest (must be Fernet tokens starting with gAAAAA)
    assert raw_stored_json["category"].startswith("gAAAAA")
    assert raw_stored_json["category"] != "SC"

    assert str(raw_stored_json["annual_income"]).startswith("gAAAAA")
    assert raw_stored_json["annual_income"] != 120000

    assert raw_stored_json["phone"].startswith("gAAAAA")
    assert raw_stored_json["phone"] != "9812345678"

    # 3. Verify transparent decryption via UserMemoryStore
    retrieved = mem.UserMemoryStore.get_or_create(test_uid)
    retrieved_profile = retrieved["profile"]
    assert retrieved_profile["name"] == "Amit Kumar"
    assert retrieved_profile["category"] == "SC"
    assert retrieved_profile["annual_income"] == 120000
    assert retrieved_profile["phone"] == "9812345678"

    # 4. Verify DELETE endpoint works and purges all data
    del_resp = client.delete(f"/rag/memory/{test_uid}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["deleted"] is True
    assert del_data["user_id"] == test_uid

    # Verify user is completely removed from SQLite
    conn = mem.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_memory WHERE user_id = ?", (test_uid,))
    purged_row = cursor.fetchone()
    conn.close()
    assert purged_row is None, "User record must be completely deleted from user_memory"


def test_whatsapp_webhook_signature_validation():
    """
    Verifies that when TWILIO_AUTH_TOKEN is set:
    - Webhook rejects invalid/unsigned requests with HTTP 403
    - Webhook accepts correctly signed requests with HTTP 200
    - Webhook allows simulator requests with X-Simulator header and logs warning
    """
    test_token = "mock_secret_twilio_token_12345"
    os.environ["TWILIO_AUTH_TOKEN"] = test_token

    url = "http://testserver/webhook/whatsapp"
    form_params = {
        "From": "whatsapp:+919810123456",
        "To": "whatsapp:+14155238886",
        "Body": "1"
    }

    try:
        # Case A: Request without signature must be rejected with 403
        resp_no_sig = client.post("/webhook/whatsapp", data=form_params)
        assert resp_no_sig.status_code == 403
        assert "Invalid Twilio signature" in resp_no_sig.text

        # Case B: Request with bogus signature must be rejected with 403
        resp_bad_sig = client.post(
            "/webhook/whatsapp",
            data=form_params,
            headers={"X-Twilio-Signature": "invalid_bogus_signature_abc"}
        )
        assert resp_bad_sig.status_code == 403

        # Case C: Request with valid HMAC signature must be accepted with 200
        # Compute valid Twilio signature
        data_str = url
        for k in sorted(form_params.keys()):
            data_str += f"{k}{form_params[k]}"
        valid_sig = base64.b64encode(
            hmac.new(test_token.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha1).digest()
        ).decode("utf-8")

        resp_valid = client.post(
            "/webhook/whatsapp",
            data=form_params,
            headers={"X-Twilio-Signature": valid_sig}
        )
        assert resp_valid.status_code == 200
        assert "<Response>" in resp_valid.text
        assert "<Message>" in resp_valid.text

        # Case D: Simulator mode bypasses signature check with warning
        resp_sim = client.post(
            "/webhook/whatsapp",
            data=form_params,
            headers={"X-Simulator": "true"}
        )
        assert resp_sim.status_code == 200
        assert "<Response>" in resp_sim.text

    finally:
        # Clean up environment variable
        os.environ.pop("TWILIO_AUTH_TOKEN", None)
