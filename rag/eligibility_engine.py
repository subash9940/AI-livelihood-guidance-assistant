"""
Deterministic Eligibility Engine for Nivara.
CRITICAL RULE: Never let the LLM decide eligibility.
Eligibility is computed strictly by this deterministic rules function using only the JSON scheme rules.
The LLM only explains the resulting computation.
"""

from typing import Dict, List, Any, Optional
import re


EDUCATION_HIERARCHY = {
    "none": 0,
    "uneducated": 0,
    "below 8th": 1,
    "8th pass": 2,
    "8th standard": 2,
    "class 8": 2,
    "10th standard": 3,
    "10th pass": 3,
    "class 10": 3,
    "matric": 3,
    "12th standard": 4,
    "12th pass": 4,
    "class 12": 4,
    "intermediate": 4,
    "iti": 4,
    "diploma": 5,
    "polytechnic": 5,
    "graduate": 6,
    "post graduate": 7
}

def parse_edu_rank(edu_str: Optional[str]) -> int:
    if not edu_str:
        return 0
    clean = edu_str.lower().strip()
    for key, rank in EDUCATION_HIERARCHY.items():
        if key in clean:
            return rank
    return 2  # default assume 8th if unspecified


def check_eligibility(profile: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes deterministic eligibility of a candidate profile against a scheme's JSON rules.
    Returns:
    {
        "scheme_id": str,
        "scheme_name": str,
        "eligible": bool,
        "match_percentage": int,
        "met_criteria": List[str],
        "unmet_criteria": List[str],
        "missing_documents": List[str],
        "required_documents": List[str],
        "notes": List[str]
    }
    """
    rules = scheme.get("eligibility", {})
    scheme_id = scheme.get("id", "unknown")
    scheme_name = scheme.get("name", "Unknown Scheme")

    met_criteria: List[str] = []
    unmet_criteria: List[str] = []
    notes: List[str] = []

    # 0. Active status check
    is_active = scheme.get("active", True)
    status_note = scheme.get("status_note")
    if not is_active:
        msg = status_note or "This scheme is currently closed / inactive and not accepting applications."
        unmet_criteria.append(f"Scheme Inactive: {msg}")
        notes.append(f"Status Note: {msg}")

    # 1. Category / Caste verification
    allowed_categories = [c.upper() for c in rules.get("category", [])]
    user_category = str(profile.get("category") or "SC").upper().strip()
    
    if "ALL" in allowed_categories:
        met_criteria.append(f"Category: Open to all categories including '{user_category}'")
    elif user_category in allowed_categories or "SC" in allowed_categories and user_category == "SC":
        met_criteria.append(f"Category: Matches target category '{user_category}'")
    else:
        unmet_criteria.append(f"Category mismatch: Scheme requires {', '.join(allowed_categories)}, but profile indicates '{user_category}'")

    # 2. Age verification
    min_age = rules.get("min_age")
    max_age = rules.get("max_age")
    raw_age = profile.get("age")
    user_age: Optional[int] = None
    if raw_age is not None:
        try:
            user_age = int(raw_age)
        except (ValueError, TypeError):
            pass

    if user_age is not None:
        if min_age is not None and user_age < min_age:
            unmet_criteria.append(f"Age: Applicant is {user_age} years old; minimum required age is {min_age}")
        elif max_age is not None and user_age > max_age:
            unmet_criteria.append(f"Age: Applicant is {user_age} years old; maximum permissible age is {max_age}")
        else:
            range_desc = f"{min_age or 'any'} to {max_age or 'any'}"
            met_criteria.append(f"Age: {user_age} falls within allowed bracket ({range_desc})")
    else:
        # Age not specified in profile
        notes.append(f"Age not verified in profile (Scheme range: {min_age or 18} - {max_age or 45})")

    # 3. Income verification
    income_rule_type = rules.get("income_rule_type", "hard_cap")
    income_limit = rules.get("income_limit")
    income_priority_below = rules.get("income_priority_below")
    raw_income = profile.get("income") or profile.get("annual_income") or profile.get("family_income")
    user_income: Optional[int] = None
    if raw_income is not None:
        try:
            if isinstance(raw_income, str):
                # Clean strings like "1.5 Lakh", "₹150000", "< 2 Lakh"
                clean_inc = re.sub(r"[^\d.]", "", raw_income)
                if "lakh" in raw_income.lower() and float(clean_inc) < 100:
                    user_income = int(float(clean_inc) * 100000)
                else:
                    user_income = int(float(clean_inc)) if clean_inc else None
            else:
                user_income = int(raw_income)
        except Exception:
            pass

    if income_rule_type == "priority_not_cutoff":
        threshold = income_priority_below or 250000
        if user_income is not None:
            if user_income <= threshold:
                met_criteria.append(f"Family Income: ₹{user_income:,} qualifies for high priority selection (priority threshold: ₹{threshold:,}/yr)")
                notes.append(f"Priority status: High priority (family income ₹{user_income:,} up to ₹{threshold:,}/yr)")
            else:
                met_criteria.append(f"Family Income: ₹{user_income:,} is eligible (no fixed income cutoff; priority given to families earning up to ₹{threshold:,}/yr)")
                notes.append(f"Priority status: Lower priority (family income ₹{user_income:,} exceeds priority threshold of ₹{threshold:,}/yr, but applicant remains eligible)")
        else:
            met_criteria.append(f"Income Limit: No fixed ceiling (priority given to families earning up to ₹{threshold:,}/yr)")
            notes.append(f"Priority status: Standard priority (income certificate required at verification)")
    else:
        # Hard cap behavior
        if income_limit is not None:
            if user_income is not None:
                if user_income <= income_limit:
                    met_criteria.append(f"Family Income: ₹{user_income:,} is within income ceiling of ₹{income_limit:,}")
                else:
                    unmet_criteria.append(f"Income Limit Exceeded: Annual family income ₹{user_income:,} exceeds ceiling of ₹{income_limit:,}")
            else:
                notes.append(f"Income ceiling is ₹{income_limit:,}/year. Income certificate required at verification.")
        else:
            met_criteria.append("Income Limit: No family income ceiling restriction")

    # 4. Gender restriction
    gender_req = str(rules.get("gender") or "all").lower()
    user_gender = str(profile.get("gender") or "all").lower()
    if gender_req != "all" and user_gender != "all":
        if gender_req in user_gender or user_gender in gender_req:
            met_criteria.append(f"Gender: Target beneficiary '{gender_req}' matched")
        else:
            unmet_criteria.append(f"Gender restriction: Scheme is specifically reserved for {gender_req.capitalize()} candidates")
    else:
        met_criteria.append("Gender: Open to all genders")

    # 5. Education requirement
    edu_req = rules.get("education")
    user_edu = profile.get("education_level") or profile.get("education")
    if edu_req and edu_req.lower() not in ["none", "any"]:
        req_rank = parse_edu_rank(edu_req)
        user_rank = parse_edu_rank(user_edu)
        if user_rank >= req_rank:
            met_criteria.append(f"Education: Completed {user_edu or 'required standard'} (Minimum required: {edu_req})")
        else:
            unmet_criteria.append(f"Education: Scheme requires minimum {edu_req}, but candidate education is '{user_edu or 'below required'}'")
    else:
        met_criteria.append("Education: No minimum educational qualification barrier")

    # 6. Residency requirement (Delhi scoping)
    res_req = rules.get("residency", "Delhi")
    user_loc = str(profile.get("location") or profile.get("state") or profile.get("district") or "Delhi").lower()
    
    if "delhi resident for 3+ years" in res_req.lower():
        res_years = profile.get("delhi_residence_years")
        if res_years is not None and int(res_years) < 3:
            unmet_criteria.append("Delhi Residency: Requires minimum 3 years domicile/residency in Delhi NCT")
        else:
            met_criteria.append("Delhi Residency: 3+ years Delhi residency criterion met")
    elif "delhi" in res_req.lower():
        if "delhi" in user_loc or not user_loc:
            met_criteria.append("Residency: Delhi NCT resident")
        else:
            unmet_criteria.append(f"Residency: Scheme is scoped to Delhi NCT; user profile mentions '{user_loc}'")
    else:
        met_criteria.append("Residency: Pan-India coverage")

    # 7. Document Readiness Check
    required_docs = scheme.get("documents_required", [])
    user_held_docs = profile.get("documents_held", [])
    if isinstance(user_held_docs, str):
        user_held_docs = [d.strip() for d in user_held_docs.split(",")]
    
    missing_docs = []
    for doc in required_docs:
        doc_lower = doc.lower()
        has_doc = any(d.lower() in doc_lower or doc_lower in d.lower() for d in user_held_docs)
        if not has_doc:
            missing_docs.append(doc)

    # Determine eligibility verdict
    eligible = (len(unmet_criteria) == 0) and is_active
    total_checks = len(met_criteria) + len(unmet_criteria)
    match_percentage = int((len(met_criteria) / total_checks) * 100) if total_checks > 0 else 100

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "eligible": eligible,
        "active": is_active,
        "status_note": status_note,
        "match_percentage": match_percentage,
        "met_criteria": met_criteria,
        "unmet_criteria": unmet_criteria,
        "missing_documents": missing_docs,
        "required_documents": required_docs,
        "notes": notes
    }


def evaluate_all_schemes_for_profile(profile: Dict[str, Any], schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluates candidate eligibility across all schemes in dataset."""
    evaluations = []
    for s in schemes:
        res = check_eligibility(profile, s)
        evaluations.append(res)
    # Sort eligible schemes first, then by match percentage
    evaluations.sort(key=lambda x: (x["eligible"], x["match_percentage"]), reverse=True)
    return evaluations
