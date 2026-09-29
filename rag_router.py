"""
FastAPI APIRouter for Nivara RAG, lexical (TF-IDF) retrieval with translate-then-retrieve; embedding-based retrieval planned, Deterministic Eligibility, and Memory Store.
Endpoints:
- POST /rag/retrieve
- POST /rag/ask
- GET /rag/memory/{user_id}
- POST /rag/memory/{user_id}
- POST /rag/memory/{user_id}/consent
- DELETE /rag/memory/{user_id}
- POST /rag/memory/{user_id}/save-scheme
- POST /rag/memory/{user_id}/progress
- POST /rag/eligibility
- GET /rag/schemes
- GET /rag/schemes/{scheme_id}
- GET /rag/jobs
- GET /rag/training-centres
- GET /rag/policies
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

import rag
import delhi_data_loader as ddl

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Layer"])


class RAGRetrieveRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    filter_type: Optional[str] = None  # 'scheme', 'job', 'training_centre', 'policy', 'office'
    region: Optional[str] = "delhi"


class RAGAskRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    language: Optional[str] = "en"
    pathway_context: Optional[Dict[str, Any]] = None
    region: Optional[str] = "delhi"


class UpdateProfileRequest(BaseModel):
    profile: Dict[str, Any]
    active_goal: Optional[str] = None
    goal_target_trade: Optional[str] = None
    goal_nsqf_level: Optional[int] = None


class ConsentRequest(BaseModel):
    consented: bool = True


class SaveSchemeRequest(BaseModel):
    scheme_id: str
    scheme_name: str


class ProgressUpdateRequest(BaseModel):
    scheme_id: str
    status: str  # 'saved', 'applied', 'documents_verified', 'enrolled', 'certified'
    current_step: Optional[int] = None
    notes: Optional[str] = None


class EligibilityCheckRequest(BaseModel):
    profile: Dict[str, Any]
    scheme_id: str
    region: Optional[str] = "delhi"


@router.post("/retrieve")
def retrieve_endpoint(req: RAGRetrieveRequest):
    """Lexical (TF-IDF) retrieval with translate-then-retrieve against Delhi knowledge base."""
    norm = rag.normalize_query(req.query)
    results = rag.retrieve(
        query=norm["english"],
        k=req.k or 5,
        filter_type=req.filter_type,
        region=req.region or "delhi"
    )
    return {
        "query": req.query,
        "normalized_query": norm["english"],
        "detected_lang": norm["detected_lang"],
        "method": norm["method"],
        "region": req.region or "delhi",
        "count": len(results),
        "results": results
    }


@router.get("/retrieve")
def retrieve_get_endpoint(
    q: str = Query(..., description="Search query string"),
    k: int = Query(5, description="Number of results"),
    filter_type: Optional[str] = None,
    region: Optional[str] = "delhi"
):
    """GET lexical (TF-IDF) retrieval with translate-then-retrieve against Delhi knowledge base."""
    norm = rag.normalize_query(q)
    results = rag.retrieve(
        query=norm["english"],
        k=k,
        filter_type=filter_type,
        region=region or "delhi"
    )
    return {
        "query": q,
        "normalized_query": norm["english"],
        "detected_lang": norm["detected_lang"],
        "method": norm["method"],
        "region": region or "delhi",
        "count": len(results),
        "results": results
    }


@router.post("/ask")
def ask_endpoint(req: RAGAskRequest):
    """
    Main RAG Q&A endpoint.
    Performs retrieval, runs deterministic eligibility, and synthesizes grounded answer with citations.
    """
    user_id = req.user_id or "guest_beneficiary"
    result = rag.ask_rag(
        query=req.query,
        user_id=user_id,
        language=req.language or "en",
        pathway_context=req.pathway_context,
        region=req.region or "delhi"
    )
    return result


@router.get("/memory/{user_id}")
def get_user_memory_endpoint(user_id: str):
    """Retrieves full persistent memory bundle: profile, conversation history, goals, applications."""
    bundle = rag.UserMemoryStore.get_full_memory_bundle(user_id)
    return bundle


@router.post("/memory/{user_id}")
def update_user_memory_endpoint(user_id: str, req: UpdateProfileRequest):
    """Updates structured profile and optional livelihood goals."""
    profile = rag.UserMemoryStore.update_profile(user_id, req.profile)
    if req.active_goal:
        rag.UserMemoryStore.set_user_goal(
            user_id=user_id,
            goal=req.active_goal,
            target_trade=req.goal_target_trade,
            nsqf_level=req.goal_nsqf_level
        )
    return rag.UserMemoryStore.get_full_memory_bundle(user_id)


@router.post("/memory/{user_id}/consent")
def update_consent_endpoint(user_id: str, req: ConsentRequest):
    """Records explicit user consent for profile storage & processing."""
    rag.UserMemoryStore.record_consent(user_id, req.consented)
    return {"user_id": user_id, "consented": req.consented}


@router.delete("/memory/{user_id}")
def delete_user_data_endpoint(user_id: str):
    """Purges all stored data for user (Right to be Forgotten)."""
    success = rag.UserMemoryStore.delete_user_data(user_id)
    return {"user_id": user_id, "deleted": success}


@router.post("/memory/{user_id}/save-scheme")
def save_scheme_endpoint(user_id: str, req: SaveSchemeRequest):
    """Adds a scheme to the user's progress tracker."""
    res = rag.UserMemoryStore.save_scheme_to_plan(user_id, req.scheme_id, req.scheme_name)
    return res


@router.post("/memory/{user_id}/progress")
def update_progress_endpoint(user_id: str, req: ProgressUpdateRequest):
    """Updates status and current step of a saved scheme."""
    res = rag.UserMemoryStore.update_application_progress(
        user_id=user_id,
        scheme_id=req.scheme_id,
        status=req.status,
        current_step=req.current_step,
        notes=req.notes
    )
    return res


@router.get("/saathi/proactive/{user_id}")
def get_saathi_proactive_endpoint(user_id: str, region: str = "delhi"):
    """
    Returns proactive guidance:
    - Daily "next best step" card
    - Deadline & document reminders
    - Progress tracker toward user's stated goal
    - Suggested schemes dynamically evaluated from profile changes
    """
    bundle = rag.UserMemoryStore.get_full_memory_bundle(user_id)
    profile = bundle.get("profile", {})
    goal = bundle.get("active_goal") or "Become a certified Solar PV Installer, NSQF 4"
    apps = bundle.get("applications", [])

    # Evaluate all schemes for this profile deterministically
    all_schemes = ddl.load_delhi_schemes(region=region)
    evaluated = rag.evaluate_all_schemes_for_profile(profile, all_schemes)
    top_schemes = evaluated[:4]

    # Calculate goal progress
    total_steps = 4
    current_step = 1
    if apps:
        latest = apps[0]
        st = latest.get("status", "saved")
        if st == "saved":
            current_step = 1
        elif st == "applied":
            current_step = 2
        elif st == "documents_verified":
            current_step = 2
        elif st == "enrolled":
            current_step = 3
        elif st == "certified":
            current_step = 4
    
    pct = int((current_step / total_steps) * 100)
    steps_titles = [
        "1. Career Mapping & Profile Verification",
        "2. PM-AJAY Centre Admission & Document Verification",
        "3. NSQF Practical Training & Stipend Disbursement",
        "4. National Certification & Livelihood/Mudra Loan Linkage"
    ]

    # Compute Next Best Step
    district = profile.get("district") or profile.get("location") or "Delhi"
    edu = profile.get("education_level") or profile.get("education") or "10th Standard"
    
    if current_step == 1:
        next_step = {
            "title": f"Complete Document Verification in {district}",
            "description": f"Gather your Aadhaar, Delhi SC Caste Certificate, and {edu} marksheet. Visit the nearest JSS or ITI center to confirm your batch enrollment.",
            "action_text": "View Center Address",
            "action_type": "view_center"
        }
    elif current_step == 2:
        next_step = {
            "title": "Biometric Attendance & Stipend Setup",
            "description": "Ensure your Aadhaar is linked to your bank account for receiving the monthly DBT stipend of ₹1,500 under PM-AJAY.",
            "action_text": "Check DBT Link Status",
            "action_type": "dbt_check"
        }
    elif current_step == 3:
        next_step = {
            "title": "Prepare for NSQF Practical Examination",
            "description": "Review the sector skill standards and safety protocols for your Sector Skill Council certification test.",
            "action_text": "View Syllabus",
            "action_type": "view_syllabus"
        }
    else:
        next_step = {
            "title": "Apply for Mudra Shishu Enterprise Loan",
            "description": "Submit your NSQF Level 4 certificate at DSFDC or lead bank branch to claim 30% capital subsidy on equipment.",
            "action_text": "Start Loan Application",
            "action_type": "apply_loan"
        }

    # Reminders
    reminders = [
        {
            "id": "rem-doc-1",
            "type": "document",
            "title": "Delhi SC Caste Certificate Required",
            "detail": "Must be issued by Revenue Dept, GNCTD with digital barcode or SDM signature.",
            "due_date": "Before batch orientation"
        },
        {
            "id": "rem-dead-1",
            "type": "deadline",
            "title": "PM-AJAY Q4 Batch Registration Cycle",
            "detail": "Upcoming admissions for free stipend-linked batches close on the 15th of next month.",
            "due_date": "15th Next Month"
        },
        {
            "id": "rem-bank-1",
            "type": "document",
            "title": "Bank Passbook with Aadhaar Seeding",
            "detail": "Required for direct DBT disbursement of monthly ₹1,500 stipend & toolkit voucher.",
            "due_date": "Immediate"
        }
    ]

    return {
        "user_id": user_id,
        "active_goal": goal,
        "goal_progress": {
            "goal": goal,
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": pct,
            "current_step_title": steps_titles[current_step - 1],
            "all_steps": steps_titles
        },
        "next_best_step": next_step,
        "reminders": reminders,
        "suggested_schemes": top_schemes
    }


@router.post("/eligibility")
def check_eligibility_endpoint(req: EligibilityCheckRequest):
    """
    Computes deterministic eligibility using JSON rules without LLM guesswork.
    Returns met criteria, unmet criteria, missing documents, and match score.
    """
    scheme = ddl.get_scheme_by_id(req.scheme_id, region=req.region or "delhi")
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.scheme_id}' not found")
    
    evaluation = rag.check_eligibility(req.profile, scheme)
    return evaluation


@router.get("/schemes")
def get_schemes_list(region: str = "delhi", q: Optional[str] = None):
    """Lists all schemes in the knowledge base with optional keyword filter."""
    if q:
        return ddl.search_schemes(q, region=region)
    return ddl.load_delhi_schemes(region=region)


@router.get("/schemes/{scheme_id}")
def get_scheme_detail(scheme_id: str, region: str = "delhi"):
    """Returns full structured details for a specific scheme."""
    s = ddl.get_scheme_by_id(scheme_id, region=region)
    if not s:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")
    return s


@router.get("/jobs")
def get_jobs_list(q: Optional[str] = None, district: Optional[str] = None, region: str = "delhi"):
    """Lists NCS jobs in Delhi with optional trade or district filters."""
    return ddl.search_jobs(query=q or "", district=district, region=region)


@router.get("/training-centres")
def get_training_centres_list(district: Optional[str] = None, course: Optional[str] = None, region: str = "delhi"):
    """Lists training centres in Delhi with optional district or course filters."""
    return ddl.search_training_centres(district=district, course=course, region=region)


@router.get("/policies")
def get_policies_list(region: str = "delhi"):
    """Lists policy summaries for Delhi SC livelihood & skilling."""
    return ddl.load_delhi_policies(region=region)
