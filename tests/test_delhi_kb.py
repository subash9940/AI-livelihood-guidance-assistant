"""
Unit tests for Phase 1: Delhi Knowledge Base, Schemas, and Loader.
Verifies all minimum counts, pydantic schema validation, and region configurability.
"""
import pytest
import delhi_data_loader as ddl

def test_delhi_data_validation():
    res = ddl.validate_all_data(region="delhi")
    assert res["valid"] is True, f"Validation failed with errors: {res.get('errors')}"
    assert res["counts"]["schemes"] >= 15, f"Expected >= 15 schemes, got {res['counts']['schemes']}"
    assert res["counts"]["jobs"] >= 30, f"Expected >= 30 jobs, got {res['counts']['jobs']}"
    assert res["counts"]["training_centres"] >= 20, f"Expected >= 20 training centres, got {res['counts']['training_centres']}"
    assert res["counts"]["policies"] >= 4, f"Expected >= 4 policies, got {res['counts']['policies']}"

def test_schemes_schema_and_fields():
    schemes = ddl.load_delhi_schemes("delhi")
    assert len(schemes) >= 15
    for s in schemes:
        assert s["id"]
        assert s["name"]
        assert s["level"] in ["central", "state"]
        assert s["department"]
        assert s.get("description") or s.get("notes")
        assert "category" in s["eligibility"]
        assert "income_rule_type" in s["eligibility"]
        assert "active" in s
        assert "how_to_apply" in s
        assert s["official_url"].startswith("http")

def test_ncs_jobs_schema_and_fields():
    jobs = ddl.load_delhi_jobs("delhi")
    assert len(jobs) >= 30
    for j in jobs:
        assert j["id"]
        assert j["job_role"]
        assert isinstance(j["nsqf_level"], int)
        assert 1 <= j["nsqf_level"] <= 8
        assert j["sector"]
        assert len(j["required_skills"]) >= 2
        assert j["avg_wage_range"]
        assert len(j["delhi_districts_hiring"]) > 0

def test_training_registry_schema_and_fields():
    centres = ddl.load_delhi_training_centres("delhi")
    assert len(centres) >= 20
    for c in centres:
        assert c["id"]
        assert c["centre_name"]
        assert c["type"] in ["ITI", "PMKK", "JSS", "DSEU Campus", "NSDC Accredited"]
        assert c["course"]
        assert isinstance(c["nsqf_level"], int)
        assert c["duration"]
        assert c["fee"]
        assert c["district"]
        assert c["contact"]
        assert len(c["facilities"]) > 0

def test_policies_schema_and_fields():
    policies = ddl.load_delhi_policies("delhi")
    assert len(policies) >= 4
    for p in policies:
        assert p["id"]
        assert p["title"]
        assert p["authority"]
        assert p["summary"]
        assert len(p["key_provisions_sc"]) > 0
        assert p["source_url"].startswith("http")

def test_curated_sample_data_metadata():
    raw_schemes = ddl.load_raw_json("schemes.json", "delhi")
    raw_jobs = ddl.load_raw_json("ncs_jobs.json", "delhi")
    raw_training = ddl.load_raw_json("training_registry.json", "delhi")
    raw_policies = ddl.load_raw_json("policies.json", "delhi")

    for raw in [raw_schemes, raw_jobs, raw_training, raw_policies]:
        assert "_metadata" in raw
        assert raw["_metadata"]["dataset_type"] == "curated_sample_data"
        assert raw["_metadata"]["region"] == "delhi"

def test_search_functions():
    pmajay = ddl.get_scheme_by_id("delhi-pmajay-gia")
    assert pmajay is not None
    assert "PM-AJAY" in pmajay["name"]

    solar_jobs = ddl.search_jobs(query="Solar")
    assert len(solar_jobs) >= 1
    assert any("Solar" in j["job_role"] for j in solar_jobs)

    okhla_centres = ddl.search_training_centres(district="South East Delhi")
    assert len(okhla_centres) >= 1

def test_data_verification_metadata():
    import subprocess
    import sys
    import json
    from pathlib import Path

    schemes = ddl.load_delhi_schemes("delhi")
    centres = ddl.load_delhi_training_centres("delhi")
    policies = ddl.load_delhi_policies("delhi")

    verified_schemes = [s for s in schemes if s["verification_status"] == "verified"]
    unverified_schemes = [s for s in schemes if s["verification_status"] == "unverified"]

    # Exactly 3 verified schemes from primary sources
    assert len(verified_schemes) == 3
    for s in verified_schemes:
        assert s["id"] in ["pm-ajay-gia", "dsfdc-composite-loan", "stand-up-india"]
        assert s["last_verified"] == "2026-09-29"
        assert s["verified_by"] == "Antigravity"
        assert s.get("official_url", "").startswith("http")

    # Remaining 15 schemes remain unverified
    assert len(unverified_schemes) >= 15
    for s in unverified_schemes:
        assert s["last_verified"] is None
        assert s["verified_by"] is None
        assert s.get("source_url", "").startswith("http")
        assert "notes" in s

    for c in centres:
        assert c["verification_status"] == "unverified"
        assert c["last_verified"] is None
        assert c["verified_by"] is None
        assert c.get("source_url", "").startswith("http")
        assert "notes" in c

    for p in policies:
        assert p["verification_status"] == "unverified"
        assert p["last_verified"] is None
        assert p["verified_by"] is None
        assert p.get("source_url", "").startswith("http")
        assert "notes" in p

    # Verify checklist file exists and has rows
    checklist_path = Path("reports/kb_review_checklist.md")
    assert checklist_path.exists()
    content = checklist_path.read_text(encoding="utf-8")
    assert "PM-AJAY" in content
    assert "Verified? (Y/N)" in content

    # Test verify_kb.py integrity checker
    import scripts.verify_kb as verify_kb
    # Real data has all unverified, should pass integrity
    assert verify_kb.check_verified_integrity(schemes, centres, policies) is True

    # Corrupt data with verified status but null date must fail integrity
    corrupt_schemes = [{"id": "bad-scheme", "verification_status": "verified", "last_verified": None}]
    assert verify_kb.check_verified_integrity(corrupt_schemes, [], []) is False
