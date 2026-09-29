"""
scripts/verify_kb.py — Knowledge Base Verification & URL Health Checker for Nivara.
Requirements:
(a) Checks that each source_url and official_url returns HTTP 200 and records the result in reports/kb_url_check.json.
(b) Prints a table of all entries whose helpline, URL or address is unverified.
(c) Exits non-zero if any entry marked "verified" has last_verified=null.
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "delhi")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

SCHEMES_FILE = os.path.join(DATA_DIR, "schemes.json")
TRAINING_FILE = os.path.join(DATA_DIR, "training_registry.json")
POLICIES_FILE = os.path.join(DATA_DIR, "policies.json")
URL_CHECK_REPORT = os.path.join(REPORTS_DIR, "kb_url_check.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def load_kb():
    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        schemes = json.load(f).get("schemes", [])
    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        centres = json.load(f).get("centres", [])
    with open(POLICIES_FILE, "r", encoding="utf-8") as f:
        policies = json.load(f).get("policies", [])
    return schemes, centres, policies


def check_urls(schemes, centres, policies):
    """Checks HTTP status of all official_url and source_url in KB."""
    url_map = {}

    for s in schemes:
        for key in ["official_url", "source_url"]:
            u = s.get(key)
            if u:
                if u not in url_map:
                    url_map[u] = []
                url_map[u].append(f"scheme:{s['id']}")

    for c in centres:
        u = c.get("source_url")
        if u:
            if u not in url_map:
                url_map[u] = []
            url_map[u].append(f"centre:{c['id']}")

    for p in policies:
        u = p.get("source_url")
        if u:
            if u not in url_map:
                url_map[u] = []
            url_map[u].append(f"policy:{p['id']}")

    results = []
    print(f"Checking {len(url_map)} unique URLs across Delhi Knowledge Base...")

    for url, entities in url_map.items():
        entry = {
            "url": url,
            "associated_entities": entities,
            "status_code": None,
            "http_200": False,
            "error": None,
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            # First try HEAD, fallback to GET if method not allowed
            resp = requests.head(url, headers=HEADERS, timeout=4, allow_redirects=True)
            if resp.status_code == 405:
                resp = requests.get(url, headers=HEADERS, timeout=4, stream=True)
            
            entry["status_code"] = resp.status_code
            entry["http_200"] = (resp.status_code == 200)
            if resp.status_code != 200:
                entry["error"] = f"HTTP {resp.status_code}"
        except Exception as exc:
            entry["error"] = str(exc)
            # Try GET once before giving up
            try:
                resp = requests.get(url, headers=HEADERS, timeout=4, stream=True)
                entry["status_code"] = resp.status_code
                entry["http_200"] = (resp.status_code == 200)
                if resp.status_code == 200:
                    entry["error"] = None
            except Exception as e2:
                entry["error"] = str(e2)

        results.append(entry)
        status_icon = "OK 200" if entry["http_200"] else f"ERR {entry['status_code'] or 'FAIL'}"
        print(f"  [{status_icon}] {url} ({', '.join(entities[:2])})")

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_urls_checked": len(results),
        "total_http_200": sum(1 for r in results if r["http_200"]),
        "results": results
    }

    with open(URL_CHECK_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nSaved URL check report to: {URL_CHECK_REPORT}")
    return report


def print_unverified_table(schemes, centres, policies):
    """Prints a structured table of all entries whose helpline, URL, or address is unverified."""
    unverified_entries = []

    for s in schemes:
        if s.get("verification_status") != "verified":
            offices = s.get("nearest_offices", [])
            office_addr = offices[0]["address"] if offices else "Not specified"
            unverified_entries.append({
                "type": "Scheme",
                "id": s["id"],
                "name": s["name"][:35],
                "helpline": s.get("helpline", "N/A")[:20],
                "url": s.get("official_url", "N/A")[:30],
                "address": office_addr[:30],
                "status": s.get("verification_status", "unverified")
            })

    for c in centres:
        if c.get("verification_status") != "verified":
            unverified_entries.append({
                "type": "Centre",
                "id": c["id"],
                "name": c["centre_name"][:35],
                "helpline": c.get("contact", "N/A")[:20],
                "url": c.get("source_url", "N/A")[:30],
                "address": c.get("address", "N/A")[:30],
                "status": c.get("verification_status", "unverified")
            })

    for p in policies:
        if p.get("verification_status") != "verified":
            unverified_entries.append({
                "type": "Policy",
                "id": p["id"],
                "name": p["title"][:35],
                "helpline": "MoSJE HQ",
                "url": p.get("source_url", "N/A")[:30],
                "address": "Shastri Bhawan, New Delhi",
                "status": p.get("verification_status", "unverified")
            })

    print("\n" + "=" * 130)
    print("UNVERIFIED KNOWLEDGE BASE ENTRIES (Pending Official Departmental Audit)")
    print("=" * 130)
    header = f"{'Type':<8} | {'ID':<25} | {'Name/Title':<36} | {'Helpline':<22} | {'Official URL':<32} | {'Address/Location':<32} | {'Status'}"
    print(header)
    print("-" * 130)

    for item in unverified_entries:
        line = f"{item['type']:<8} | {item['id']:<25} | {item['name']:<36} | {item['helpline']:<22} | {item['url']:<32} | {item['address']:<32} | {item['status']}"
        print(line)

    print("-" * 130)
    print(f"Total unverified entries requiring human review: {len(unverified_entries)}\n")


def check_verified_integrity(schemes, centres, policies):
    """
    Exits non-zero if ANY entry marked 'verified' has last_verified=null.
    """
    violations = []

    for s in schemes:
        if s.get("verification_status") == "verified" and not s.get("last_verified"):
            violations.append(f"Scheme '{s['id']}' is marked 'verified' but has last_verified=null")

    for c in centres:
        if c.get("verification_status") == "verified" and not c.get("last_verified"):
            violations.append(f"Centre '{c['id']}' is marked 'verified' but has last_verified=null")

    for p in policies:
        if p.get("verification_status") == "verified" and not p.get("last_verified"):
            violations.append(f"Policy '{p['id']}' is marked 'verified' but has last_verified=null")

    if violations:
        print("\n[CRITICAL ERROR] Data Verification Integrity Violations Detected:")
        for v in violations:
            print(f"  FAIL: {v}")
        return False

    print("[INTEGRITY PASS] No fabricated verifications found. All entries with status='verified' have valid last_verified dates.")
    return True


def main():
    schemes, centres, policies = load_kb()

    # (a) Check URLs & record result
    check_urls(schemes, centres, policies)

    # (b) Print unverified table
    print_unverified_table(schemes, centres, policies)

    # (c) Exit non-zero if any entry marked 'verified' has last_verified=null
    is_valid = check_verified_integrity(schemes, centres, policies)
    if not is_valid:
        sys.exit(1)

    print("KB Verification Script completed successfully.")


if __name__ == "__main__":
    main()
