"""
Script to apply primary source corrections to schemes.json and ncs_jobs.json.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMES_FILE = os.path.join(BASE_DIR, "data", "delhi", "schemes.json")
JOBS_FILE = os.path.join(BASE_DIR, "data", "delhi", "ncs_jobs.json")

# 1. New verified scheme entries
VERIFIED_SCHEMES = {
    "pm-ajay-gia": {
        "id": "pm-ajay-gia",
        "name": "PM-AJAY: Grants-in-Aid (Comprehensive Livelihood Projects)",
        "level": "central",
        "department": "Dept. of Social Justice & Empowerment, MoSJE",
        "active": True,
        "eligibility": {
            "category": ["SC"],
            "min_age": None,
            "max_age": None,
            "income_limit": None,
            "income_priority_below": 250000,
            "income_rule_type": "priority_not_cutoff",
            "notes": "No fixed income limit. Priority to persons/families with annual income up to Rs 2.5 lakh. SC-majority groups also eligible."
        },
        "benefits": [
            "Skill development linked to livelihood projects (RPL 32-80 hrs, short-term 200-600 hrs, EDP ~80 hrs, long-term 6 months+)",
            "Financial assistance up to Rs 50,000 or 50% of project cost, whichever is less, where the beneficiary takes a loan for livelihood assets",
            "No standalone individual asset distribution"
        ],
        "how_to_apply": "Benefits are delivered through approved State/District projects and implementing agencies, not a direct individual application. Beneficiaries are mobilised and selected by the State/District administration or the training partner through a selection committee. Ask the District Social Welfare/SC Welfare office (suggested contact, not named in the guidelines).",
        "official_url": "https://pmajay.dosje.gov.in",
        "guidelines_url": "https://pmajay.dosje.gov.in/Writereaddata/Guidelines.pdf",
        "source_url": "https://pmajay.dosje.gov.in",
        "helpline": None,
        "helpline_note": "No helpline printed in the May 2023 guidelines.",
        "verification_status": "verified",
        "last_verified": "2026-09-29",
        "verified_by": "Antigravity",
        "notes": "Verified against Revised Guidelines (May 2023), Ch. 3. Approved period in the guidelines runs to 2025-26; confirm the current cycle on the portal."
    },
    "dsfdc-composite-loan": {
        "id": "dsfdc-composite-loan",
        "name": "DSFDC Composite Loan Scheme",
        "level": "state",
        "department": "Delhi SC/ST/OBC/Minorities & Handicapped Finance & Development Corporation",
        "active": True,
        "eligibility": {
            "category": ["SC", "ST", "OBC", "Minority", "PwD"],
            "residency": "Delhi",
            "min_age": 18,
            "max_age": 50,
            "income_limit": 120000,
            "income_priority_below": None,
            "income_rule_type": "hard_cap",
            "other": [
                "Owned or rented workplace for the activity",
                "Not a defaulter under any DSFDC scheme"
            ]
        },
        "benefits": [
            "Need-based loan up to Rs 3 lakh (SC)",
            "Need-based loan up to Rs 1 lakh (OBC, Minority, PwD)",
            "Loans up to Rs 50,000: guarantor/collateral not required (discretionary); two local references needed"
        ],
        "documents_required": [
            "Loan application form (free, from branches or website)",
            "Aadhaar (identity and residence)",
            "Caste certificate (Delhi Govt) / PwD certificate (min 40%) / affidavit for minorities",
            "Age proof; income affidavit",
            "Estimate of items/machines to be bought",
            "Workplace ownership proof or rent agreement with owner's ID",
            "Affidavit of no loan from other institutions; personal guarantee affidavit",
            "ECS mandate and post-dated cheques",
            "PMSBY/PMJJBY insurance receipt",
            "Rs 350 demand draft as processing fee",
            "Two witnesses with ID; guarantor documents for larger loans"
        ],
        "how_to_apply": "Apply directly at a DSFDC branch: Rajpur Road, Mangolpuri, Nand Nagri, or HQ at Rohini.",
        "official_url": "https://dsfdc.delhi.gov.in/sites/default/files/cls_schem_details.pdf",
        "source_url": "https://dsfdc.delhi.gov.in/sites/default/files/cls_schem_details.pdf",
        "helpline": None,
        "verification_status": "verified",
        "last_verified": "2026-09-29",
        "verified_by": "Antigravity",
        "notes": "Verified against the DSFDC scheme PDF. The PDF is undated and cites an old delhi.gov.in URL, so income and loan limits may have been revised; confirm at a branch. Loan limit for ST applicants is not stated in the PDF."
    },
    "stand-up-india": {
        "id": "stand-up-india",
        "name": "Stand-Up India (original scheme)",
        "level": "central",
        "department": "Dept. of Financial Services",
        "active": False,
        "status_note": "Original scheme ran to 31 Mar 2025 and has ended; a revamped version was announced but not confirmed as launched.",
        "eligibility": {
            "category": ["SC", "ST", "Women"],
            "min_age": 18,
            "income_limit": None,
            "income_priority_below": None,
            "income_rule_type": "hard_cap"
        },
        "benefits": [
            "Composite loan Rs 10 lakh - Rs 1 crore for greenfield enterprises",
            "Repayment up to 7 years incl. 18-month moratorium",
            "Margin money up to 15% via convergence; borrower contributes at least 10%"
        ],
        "how_to_apply": "Do not show as an open scheme. Watch for the successor scheme (standupmitra.in / jansamarth.in).",
        "official_url": "https://financialservices.gov.in/node/3468",
        "source_url": "https://financialservices.gov.in/node/3468",
        "helpline": None,
        "verification_status": "verified",
        "last_verified": "2026-09-29",
        "verified_by": "Antigravity",
        "notes": "Status verified from the DFS page and the Finance Minister's Lok Sabha reply (16 Mar 2026)."
    }
}

def update_schemes():
    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_schemes = []
    for s in data["schemes"]:
        sid = s["id"]
        if sid in ["delhi-pmajay-gia", "pm-ajay-gia"]:
            new_schemes.append(VERIFIED_SCHEMES["pm-ajay-gia"])
        elif sid in ["delhi-dsfdc-term-loan", "dsfdc-composite-loan"]:
            new_schemes.append(VERIFIED_SCHEMES["dsfdc-composite-loan"])
        elif sid in ["delhi-standup-india", "stand-up-india"]:
            new_schemes.append(VERIFIED_SCHEMES["stand-up-india"])
        else:
            # Add active and income rule fields if missing
            if "active" not in s:
                s["active"] = True
            elig = s.get("eligibility", {})
            if "income_rule_type" not in elig:
                elig["income_rule_type"] = "hard_cap"
            if "income_priority_below" not in elig:
                elig["income_priority_below"] = None
            s["eligibility"] = elig
            new_schemes.append(s)

    data["schemes"] = new_schemes
    with open(SCHEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Updated schemes.json successfully.")

QP_CODE_MAPPINGS = {
    "ncs-del-05": "AMH/Q1947",     # Tailor: Self Employed Tailor
    "ncs-del-20": "AMH/Q0305",     # Tailor (alt): Sewing Machine (operator)
    "ncs-del-11": "BWS/Q0102",     # Beautician: Beauty Therapist
    "ncs-del-07": "CON/Q0602",     # Electrician: Assistant Electrician
    "ncs-del-09": "ASC/Q9702",     # Driver: Light Motor Vehicle
    "ncs-del-12": "NARQ40040",     # Plumber: Plumbing and Sanitary Works
    "ncs-del-04": "none"          # Data Entry Operator: none
}

def update_jobs():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for j in data["jobs"]:
        jid = j["id"]
        if jid in QP_CODE_MAPPINGS:
            j["qp_code"] = QP_CODE_MAPPINGS[jid]
        elif "qp_code" not in j:
            j["qp_code"] = None

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Updated ncs_jobs.json successfully.")

if __name__ == "__main__":
    update_schemes()
    update_jobs()
