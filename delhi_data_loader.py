"""
Delhi Knowledge Base Loader & Schema Validator for Nivara.
Scopes data to Delhi by default, but is region-configurable (region="delhi")
so other state datasets can be loaded seamlessly in the future.
Validates structured JSON schemas for schemes, NCS jobs, training centres, and policies.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ValidationError

BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# -------------------------------------------------------------
# Pydantic Schemas for Strict Data Validation
# -------------------------------------------------------------

class NearestOfficeSchema(BaseModel):
    district: str
    name: str
    address: str
    contact: str


class SchemeEligibilitySchema(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    income_limit: Optional[int] = None
    income_priority_below: Optional[int] = None
    income_rule_type: Optional[str] = "hard_cap"
    category: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    gender: Optional[str] = "all"
    residency: Optional[str] = "Delhi"
    other: Optional[List[str]] = Field(default_factory=list)
    other_criteria: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class SchemeBenefitsSchema(BaseModel):
    financial_assistance: Optional[str] = None
    stipend: Optional[str] = None
    loan_subsidy: Optional[str] = None
    toolkit_support: Optional[str] = None
    details: Optional[str] = None


class SchemeSchema(BaseModel):
    id: str
    name: str
    level: str  # 'central' or 'state'
    department: str
    active: bool = True
    status_note: Optional[str] = None
    description: Optional[str] = ""
    eligibility: SchemeEligibilitySchema
    benefits: Any = Field(default_factory=list)
    documents_required: Optional[List[str]] = Field(default_factory=list)
    how_to_apply: Union[List[str], str] = Field(default_factory=list)
    official_url: str
    guidelines_url: Optional[str] = None
    helpline: Optional[str] = None
    helpline_note: Optional[str] = None
    nearest_offices: Optional[List[NearestOfficeSchema]] = Field(default_factory=list)
    verification_status: str = Field(default="unverified")
    last_verified: Optional[str] = None
    verified_by: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None

    def validate_verification(self):
        if self.verification_status not in ("unverified", "verified"):
            raise ValueError(f"Invalid verification_status: {self.verification_status}")
        if self.verification_status == "verified" and not self.last_verified:
            raise ValueError("Entries marked 'verified' must have a valid last_verified date.")


class NCSJobSchema(BaseModel):
    id: str
    job_role: str
    nsqf_level: int
    sector: str
    required_skills: List[str]
    avg_wage_range: str
    delhi_districts_hiring: List[str]
    minimum_education: str
    experience_required: str
    vacancies_sample: Optional[int] = None
    ncs_portal_code: Optional[str] = None
    qp_code: Optional[str] = None


class TrainingCentreSchema(BaseModel):
    id: str
    centre_name: str
    type: str  # 'ITI', 'PMKK', 'JSS', 'DSEU Campus', 'NSDC Accredited'
    course: str
    nsqf_level: int
    duration: str
    fee: str
    district: str
    address: str
    contact: str
    facilities: List[str] = Field(default_factory=list)
    accreditation: Optional[str] = None
    verification_status: str = Field(default="unverified")
    last_verified: Optional[str] = None
    verified_by: Optional[str] = None
    source_url: str
    notes: Optional[str] = None

    def validate_verification(self):
        if self.verification_status not in ("unverified", "verified"):
            raise ValueError(f"Invalid verification_status: {self.verification_status}")
        if self.verification_status == "verified" and not self.last_verified:
            raise ValueError("Entries marked 'verified' must have a valid last_verified date.")


class PolicySchema(BaseModel):
    id: str
    title: str
    authority: str
    year: str
    summary: str
    key_provisions_sc: List[str]
    source_url: str
    tags: List[str] = Field(default_factory=list)
    verification_status: str = Field(default="unverified")
    last_verified: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None

    def validate_verification(self):
        if self.verification_status not in ("unverified", "verified"):
            raise ValueError(f"Invalid verification_status: {self.verification_status}")
        if self.verification_status == "verified" and not self.last_verified:
            raise ValueError("Entries marked 'verified' must have a valid last_verified date.")


# -------------------------------------------------------------
# Data Loader Functions (Region-Configurable)
# -------------------------------------------------------------

def get_region_data_dir(region: str = "delhi") -> str:
    """Returns the absolute path to the region data directory."""
    return os.path.join(BASE_DATA_DIR, region.lower())


def load_raw_json(filename: str, region: str = "delhi") -> Dict[str, Any]:
    """Loads raw JSON file from region directory."""
    dir_path = get_region_data_dir(region)
    file_path = os.path.join(dir_path, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge file '{filename}' not found for region '{region}' at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_delhi_schemes(region: str = "delhi") -> List[Dict[str, Any]]:
    """Loads and validates all schemes for the given region."""
    data = load_raw_json("schemes.json", region)
    schemes_raw = data.get("schemes", [])
    validated = []
    for s in schemes_raw:
        item = SchemeSchema(**s)
        item.validate_verification()
        validated.append(item.model_dump())
    return validated


def load_delhi_jobs(region: str = "delhi") -> List[Dict[str, Any]]:
    """Loads and validates all NCS jobs for the given region."""
    data = load_raw_json("ncs_jobs.json", region)
    jobs_raw = data.get("jobs", [])
    validated = []
    for j in jobs_raw:
        item = NCSJobSchema(**j)
        validated.append(item.model_dump())
    return validated


def load_delhi_training_centres(region: str = "delhi") -> List[Dict[str, Any]]:
    """Loads and validates all training centres for the given region."""
    data = load_raw_json("training_registry.json", region)
    centres_raw = data.get("centres", [])
    validated = []
    for c in centres_raw:
        item = TrainingCentreSchema(**c)
        item.validate_verification()
        validated.append(item.model_dump())
    return validated


def load_delhi_policies(region: str = "delhi") -> List[Dict[str, Any]]:
    """Loads and validates all policy summaries for the given region."""
    data = load_raw_json("policies.json", region)
    policies_raw = data.get("policies", [])
    validated = []
    for p in policies_raw:
        item = PolicySchema(**p)
        item.validate_verification()
        validated.append(item.model_dump())
    return validated


def load_all_delhi_knowledge(region: str = "delhi") -> Dict[str, Any]:
    """Loads all knowledge entities for the specified region."""
    return {
        "region": region.lower(),
        "schemes": load_delhi_schemes(region),
        "jobs": load_delhi_jobs(region),
        "training_centres": load_delhi_training_centres(region),
        "policies": load_delhi_policies(region),
        "metadata": {
            "dataset_type": "curated_sample_data",
            "region": region.lower(),
            "schemes_count": len(load_delhi_schemes(region)),
            "jobs_count": len(load_delhi_jobs(region)),
            "centres_count": len(load_delhi_training_centres(region)),
            "policies_count": len(load_delhi_policies(region)),
        }
    }


def validate_all_data(region: str = "delhi") -> Dict[str, Any]:
    """Runs a complete validation check on all data files in the region folder."""
    errors = []
    schemes = []
    jobs = []
    centres = []
    policies = []

    try:
        schemes = load_delhi_schemes(region)
    except Exception as e:
        errors.append(f"Schemes validation failed: {e}")

    try:
        jobs = load_delhi_jobs(region)
    except Exception as e:
        errors.append(f"NCS jobs validation failed: {e}")

    try:
        centres = load_delhi_training_centres(region)
    except Exception as e:
        errors.append(f"Training registry validation failed: {e}")

    try:
        policies = load_delhi_policies(region)
    except Exception as e:
        errors.append(f"Policies validation failed: {e}")

    return {
        "valid": len(errors) == 0,
        "region": region.lower(),
        "errors": errors,
        "counts": {
            "schemes": len(schemes),
            "jobs": len(jobs),
            "training_centres": len(centres),
            "policies": len(policies),
        }
    }


def get_scheme_by_id(scheme_id: str, region: str = "delhi") -> Optional[Dict[str, Any]]:
    """Retrieves a specific scheme by ID, supporting canonical IDs and prefix aliases."""
    schemes = load_delhi_schemes(region)
    for s in schemes:
        if s["id"] == scheme_id:
            return s
        # Aliases between prefix variants
        s_norm = s["id"].replace("delhi-", "").replace("pmajay", "pm-ajay").replace("standup", "stand-up").replace("composite-loan", "term-loan")
        q_norm = scheme_id.replace("delhi-", "").replace("pmajay", "pm-ajay").replace("standup", "stand-up").replace("composite-loan", "term-loan")
        if s_norm == q_norm:
            return s
    return None


def search_schemes(query: str, region: str = "delhi") -> List[Dict[str, Any]]:
    """Simple keyword search across name, department, description, and benefits."""
    q = query.lower()
    results = []
    for s in load_delhi_schemes(region):
        b = s.get("benefits", "")
        b_text = " ".join(b) if isinstance(b, list) else (" ".join(str(v) for v in b.values()) if isinstance(b, dict) else str(b))
        desc = s.get("description", "") or s.get("notes", "")
        haystack = f"{s['name']} {s['department']} {desc} {b_text}".lower()
        if q in haystack:
            results.append(s)
    return results


def search_jobs(query: str = "", district: Optional[str] = None, region: str = "delhi") -> List[Dict[str, Any]]:
    """Filters NCS jobs by query and/or hiring district."""
    jobs = load_delhi_jobs(region)
    q = query.lower() if query else ""
    d = district.lower() if district else ""
    matched = []
    for j in jobs:
        haystack = f"{j['job_role']} {j['sector']} {' '.join(j['required_skills'])}".lower()
        dist_match = True
        if d:
            dist_match = any(d in dist.lower() for dist in j["delhi_districts_hiring"])
        text_match = True
        if q:
            text_match = q in haystack
        if text_match and dist_match:
            matched.append(j)
    return matched


def search_training_centres(district: Optional[str] = None, course: Optional[str] = None, region: str = "delhi") -> List[Dict[str, Any]]:
    """Filters training centres by district and/or course keywords."""
    centres = load_delhi_training_centres(region)
    d = district.lower() if district else ""
    c = course.lower() if course else ""
    matched = []
    for tc in centres:
        dist_match = not d or d in tc["district"].lower() or d in tc["address"].lower()
        course_match = not c or c in tc["course"].lower() or c in tc["centre_name"].lower()
        if dist_match and course_match:
            matched.append(tc)
    return matched
