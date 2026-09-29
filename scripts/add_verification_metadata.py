"""
scripts/add_verification_metadata.py — Adds standardized verification metadata fields
to every entry in data/delhi/schemes.json, training_registry.json, policies.json.

Fields added:
- verification_status: "unverified"
- last_verified: null
- verified_by: null
- source_url: official URL
- notes: string note
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELHI_DIR = os.path.join(BASE_DIR, "data", "delhi")

SCHEMES_FILE = os.path.join(DELHI_DIR, "schemes.json")
TRAINING_FILE = os.path.join(DELHI_DIR, "training_registry.json")
POLICIES_FILE = os.path.join(DELHI_DIR, "policies.json")


def update_schemes():
    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for s in data.get("schemes", []):
        s["verification_status"] = "unverified"
        s["last_verified"] = None
        s["verified_by"] = None
        s["source_url"] = s.get("official_url", "https://socialjustice.gov.in")
        s["notes"] = "Curated public government scheme information; requires formal departmental verification."

    with open(SCHEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {len(data.get('schemes', []))} schemes in {SCHEMES_FILE}")


def update_training_registry():
    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Official source mapping per centre type
    type_urls = {
        "ITI": "https://itidelhi.admissions.nic.in",
        "JSS": "https://jss.gov.in",
        "PMKK": "https://www.pmkvyofficial.org",
        "DSEU Campus": "https://dseu.ac.in",
        "NSDC Accredited": "https://www.skillindiadigital.gov.in"
    }

    for c in data.get("centres", []):
        c["verification_status"] = "unverified"
        c["last_verified"] = None
        c["verified_by"] = None
        c["source_url"] = type_urls.get(c.get("type", "ITI"), "https://www.skillindiadigital.gov.in")
        c["notes"] = "Empanelled training partner facility; pending physical verification of batch capacity & lab equipment."

    with open(TRAINING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {len(data.get('centres', []))} training centres in {TRAINING_FILE}")


def update_policies():
    with open(POLICIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for p in data.get("policies", []):
        p["verification_status"] = "unverified"
        p["last_verified"] = None
        p["verified_by"] = None
        p["source_url"] = p.get("source_url", "https://socialjustice.gov.in")
        p["notes"] = "Statutory policy guidelines excerpt; requires periodic review against official gazette notifications."

    with open(POLICIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {len(data.get('policies', []))} policies in {POLICIES_FILE}")


if __name__ == "__main__":
    update_schemes()
    update_training_registry()
    update_policies()
    print("All KB JSON files successfully updated with unverified metadata.")
