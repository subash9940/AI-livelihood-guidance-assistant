"""
FastAPI Backend for Nivara — AI Livelihood Guidance Assistant (SIH PS 26097).
Exposes the exact Section 5 API surface and serves the responsive frontend.
"""
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import json
import uuid

# Ensure local modules can be found regardless of current working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import profiler
import nsqf_rules
import region_schemes
import training_capacity

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    try:
        import seed_data
        seed_data.seed_database()
    except Exception as e:
        print(f"Seed note: {e}")
    yield

app = FastAPI(
    title="Nivara — AI Livelihood Guidance Assistant",
    description="Multilingual Voice-First Assistant for PM-AJAY Beneficiaries",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SessionStartRequest(BaseModel):
    entry_mode: Optional[str] = "app"  # 'app', 'call', 'facilitator'
    language: Optional[str] = "en"
    facilitator_id: Optional[str] = None

class VoiceInputRequest(BaseModel):
    text: Optional[str] = None
    transcript: Optional[str] = None
    language: Optional[str] = "en"
    audio_base64: Optional[str] = None

class FollowUpRequest(BaseModel):
    status: str  # 'enrolled', 'dropped', 'placed', 'no_contact'

# --- 1. POST /session/start ---
@app.post("/session/start")
def session_start(req: SessionStartRequest):
    entry_mode = req.entry_mode if req.entry_mode in ["app", "call", "facilitator"] else "app"
    session_id = database.create_session(entry_mode=entry_mode, language=req.language or "en")
    
    # Initial greeting prompt based on language
    initial_prompt = profiler.generate_next_prompt({}, language=req.language or "en")

    return {
        "session_id": session_id,
        "entry_mode": entry_mode,
        "language": req.language or "en",
        "initial_prompt": initial_prompt
    }

# --- 2. POST /session/{id}/voice-input ---
@app.post("/session/{session_id}/voice-input")
async def voice_input(session_id: str, request: Request):
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content_type = request.headers.get("content-type", "")
    input_text = ""
    lang = session.get("language", "en")

    profile_override = None
    if "application/json" in content_type:
        body = await request.json()
        input_text = body.get("transcript") or body.get("text") or ""
        if body.get("language"):
            lang = body.get("language")
        profile_override = body.get("profile_data") or body.get("profile")
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        input_text = form.get("text") or form.get("transcript") or ""
        if form.get("language"):
            lang = form.get("language")
    else:
        # Fallback try json
        try:
            body = await request.json()
            input_text = body.get("transcript") or body.get("text") or ""
            if body.get("language"):
                lang = body.get("language")
            profile_override = body.get("profile_data") or body.get("profile")
        except Exception:
            pass

    if not input_text.strip():
        if profile_override and isinstance(profile_override, dict):
            name = profile_override.get("name", "Beneficiary")
            trade_interest = ", ".join(profile_override.get("interests", [])) or "PM-AJAY Trade"
            loc = profile_override.get("location") or profile_override.get("state") or "Local District"
            input_text = f"Profile submission for {name} from {loc} interested in {trade_interest}."
        else:
            raise HTTPException(status_code=400, detail="No voice transcript or text provided")

    # 1. Update Conversation History
    history = session.get("conversation_history", [])
    history.append({"role": "user", "content": input_text})

    # 2. Extract profile fields
    current_profile = session.get("profile_data", {})
    current_profile["language"] = lang
    current_profile["entry_mode"] = session.get("entry_mode", "app")

    updated_profile, is_complete = profiler.extract_profile_from_text(input_text, current_profile)

    # Merge explicit profile override if passed (for direct profile or demo selector input)
    if profile_override and isinstance(profile_override, dict):
        for k, v in profile_override.items():
            if v is not None:
                updated_profile[k] = v
        if "education" in updated_profile and "education_level" not in updated_profile:
            updated_profile["education_level"] = updated_profile["education"]
        if "mobility" in updated_profile and "mobility_constraint" not in updated_profile:
            updated_profile["mobility_constraint"] = updated_profile["mobility"]
        if updated_profile.get("education_level") or updated_profile.get("education"):
            is_complete = True

    # 3. Next prompt generation
    if is_complete:
        if lang == "hi":
            next_prompt = "धन्यवाद! आपकी जानकारी दर्ज कर ली गई है। आपके लिए उपयुक्त पीएम-अजय कौशल योजना तैयार की जा रही है।"
        elif lang == "mr":
            next_prompt = "धन्यवाद! तुमची सर्व माहिती नोंदवली गेली आहे. तुमच्यासाठी योग्य कौशल्य प्रशिक्षण आराखडा तयार केला जात आहे."
        elif lang == "pa":
            next_prompt = "ਧੰਨਵਾਦ! ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਦਰਜ ਕਰ ਲਈ ਗਈ ਹੈ। ਤੁਹਾਡੇ ਲਈ ਢੁਕਵਾਂ ਰੋਜ਼ਗਾਰ ਰੋਡਮੈਪ ਤਿਆਰ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ।"
        else:
            next_prompt = "Thank you! We have captured your profile. Generating your customized PM-AJAY NSQF livelihood roadmap."
    else:
        next_prompt = profiler.generate_next_prompt(updated_profile, language=lang)

    history.append({"role": "assistant", "content": next_prompt})

    # 4. If complete, generate and persist Beneficiary, SkillGapResult, Recommendation, FollowUp
    beneficiary_id = session.get("beneficiary_id")
    if is_complete:
        if not beneficiary_id:
            raw_loc = updated_profile.get("state") or updated_profile.get("location") or "Delhi"
            c_state = region_schemes.get_canonical_state(raw_loc) or "Delhi"
            # Save Beneficiary with name
            beneficiary_id = database.save_beneficiary({
                "name": updated_profile.get("name"),
                "language": lang,
                "location": updated_profile.get("location", "Your Local District"),
                "state": c_state,
                "mobility_constraint": updated_profile.get("mobility_constraint") or updated_profile.get("mobility"),
                "education_level": updated_profile.get("education_level") or updated_profile.get("education", "10th Standard"),
                "family_occupation": updated_profile.get("family_occupation", "Agriculture"),
                "current_livelihood": updated_profile.get("current_livelihood", "Daily wage / Informal"),
                "skills": updated_profile.get("skills", []),
                "interests": updated_profile.get("interests", []),
                "employment_preference": updated_profile.get("employment_preference", "undecided"),
                "entry_mode": session.get("entry_mode", "app"),
                "facilitator_id": None
            })

            # Run Skill Gap Analysis & Recommendation
            skill_res = nsqf_rules.analyze_skill_gap(updated_profile)
            
            # Save SkillGapResult
            database.save_skill_gap(
                beneficiary_id=beneficiary_id,
                recommended_trade=skill_res["recommended_trade"],
                gap_summary=skill_res["gap_summary"],
                nsqf_alignment=skill_res["nsqf_alignment"]
            )

            # Save Recommendation
            database.save_recommendation(
                beneficiary_id=beneficiary_id,
                training_programme=skill_res["training_programme"],
                training_centre=skill_res["training_centre"],
                local_opportunity=skill_res["local_opportunity"],
                roadmap_steps=skill_res["roadmap_steps"],
                spoken_summary=skill_res["spoken_summary"]
            )

            # Save initial FollowUp
            database.update_followup(beneficiary_id, "enrolled")

            # Record demand signal event
            database.record_recommendation_demand(
                state=c_state,
                trade_key=skill_res.get("trade_key", "food_processing"),
                trade_name=skill_res["recommended_trade"],
                beneficiary_id=beneficiary_id,
                session_id=session_id
            )

    # Update session in db
    database.update_session(
        session_id=session_id,
        conversation_history=history,
        profile_data=updated_profile,
        profile_complete=is_complete,
        beneficiary_id=beneficiary_id
    )

    return {
        "transcript": input_text,
        "extracted_fields": updated_profile,
        "next_prompt": next_prompt,
        "profile_complete": is_complete,
        "session_id": session_id,
        "beneficiary_id": beneficiary_id
    }

# --- 3. GET /session/{id}/recommendation ---
@app.get("/session/{session_id}/recommendation")
def get_recommendation(session_id: str):
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.get("profile_complete"):
        raise HTTPException(
            status_code=409,
            detail="Profile incomplete — continue the voice intake before requesting a recommendation"
        )

    profile = session.get("profile_data", {})
    skill_res = nsqf_rules.analyze_skill_gap(profile)
    reg_schemes = region_schemes.get_schemes_for_profile(profile)

    return {
        "recommended_trade": skill_res["recommended_trade"],
        "trade_key": skill_res.get("trade_key"),
        "qp_name": skill_res.get("qp_name"),
        "qp_code": skill_res.get("qp_code"),
        "nsqf_level": skill_res.get("nsqf_level"),
        "ssc_name": skill_res.get("ssc_name"),
        "nsqf_alignment": skill_res["nsqf_alignment"],
        "gap_summary": skill_res["gap_summary"],
        "readiness_score": skill_res.get("readiness_score", 0),
        "readiness_relevant_count": skill_res.get("readiness_relevant_count", 0),
        "readiness_total_required": skill_res.get("readiness_total_required", 5),
        "skill_gap_breakdown": skill_res.get("skill_gap_breakdown", []),
        "regional_schemes": reg_schemes,
        "training_programme": skill_res["training_programme"],
        "training_centre": skill_res["training_centre"],
        "local_opportunity": skill_res["local_opportunity"],
        "roadmap_steps": skill_res["roadmap_steps"],
        "spoken_summary": skill_res["spoken_summary"],
        "duration_hours": skill_res.get("duration_hours"),
        "sector": skill_res.get("ssc_name") or skill_res.get("sector"),
        "beneficiary_id": session.get("beneficiary_id"),
        "profile": profile
    }

# --- GET & POST /recommendation ---
@app.api_route("/recommendation", methods=["GET", "POST"])
async def get_recommendation_direct(
    request: Request,
    session_id: Optional[str] = None,
    state: Optional[str] = None,
    location: Optional[str] = None
):
    if session_id:
        return get_recommendation(session_id)

    profile_data: Dict[str, Any] = {}
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "session_id" in body and body["session_id"]:
                    return get_recommendation(body["session_id"])
                profile_data = body.get("profile") or body.get("profile_data") or body
        except Exception:
            pass

    # Extract target state for schemes
    target_state = state or location or profile_data.get("state") or profile_data.get("location")

    # If full profile with trade/interests/skills was provided, compute full NSQF recommendation
    if profile_data and (profile_data.get("interests") or profile_data.get("skills") or profile_data.get("education") or profile_data.get("education_level")):
        skill_res = nsqf_rules.analyze_skill_gap(profile_data)
        reg_schemes = region_schemes.get_schemes_for_profile(profile_data)
        state_val = region_schemes.get_canonical_state(target_state) or "Delhi"
        database.record_recommendation_demand(
            state=state_val,
            trade_key=skill_res.get("trade_key", "food_processing"),
            trade_name=skill_res["recommended_trade"]
        )
        return {
            "recommended_trade": skill_res["recommended_trade"],
            "trade_key": skill_res.get("trade_key"),
            "qp_name": skill_res.get("qp_name"),
            "qp_code": skill_res.get("qp_code"),
            "nsqf_level": skill_res.get("nsqf_level"),
            "ssc_name": skill_res.get("ssc_name"),
            "nsqf_alignment": skill_res["nsqf_alignment"],
            "gap_summary": skill_res["gap_summary"],
            "readiness_score": skill_res.get("readiness_score", 0),
            "skill_gap_breakdown": skill_res.get("skill_gap_breakdown", []),
            "regional_schemes": reg_schemes,
            "training_programme": skill_res["training_programme"],
            "training_centre": skill_res["training_centre"],
            "local_opportunity": skill_res["local_opportunity"],
            "roadmap_steps": skill_res["roadmap_steps"],
            "spoken_summary": skill_res["spoken_summary"],
            "duration_hours": skill_res.get("duration_hours"),
            "sector": skill_res.get("ssc_name") or skill_res.get("sector"),
            "profile": profile_data
        }

    reg_schemes = region_schemes.get_regional_schemes(target_state) if target_state else []
    return {
        "readiness_score": 0,
        "regional_schemes": reg_schemes
    }



# --- 4. GET /dashboard/summary?district= ---
@app.get("/dashboard/summary")
def get_dashboard_summary(district: Optional[str] = None):
    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
    SELECT b.id, b.name, b.location, b.education_level, b.entry_mode, b.created_at,
           sg.recommended_trade, sg.nsqf_alignment,
           f.status, f.last_contact_date
    FROM beneficiaries b
    LEFT JOIN skill_gap_results sg ON b.id = sg.beneficiary_id
    LEFT JOIN follow_ups f ON b.id = f.beneficiary_id
    """
    params = []
    if district and district.lower() != "all":
        query += " WHERE LOWER(b.location) LIKE ?"
        params.append(f"%{district.lower()}%")

    query += " ORDER BY b.created_at DESC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    enrolments = 0
    dropouts = 0
    placements = 0
    no_contacts = 0
    trade_counts: Dict[str, int] = {}
    beneficiary_list = []

    for r in rows:
        st = r["status"] or "enrolled"
        if st == "enrolled":
            enrolments += 1
        elif st == "dropped":
            dropouts += 1
        elif st == "placed":
            placements += 1
        else:
            no_contacts += 1

        trade = r["recommended_trade"] or "Food Processing & Agri-Value Addition"
        trade_counts[trade] = trade_counts.get(trade, 0) + 1

        beneficiary_list.append({
            "id": r["id"],
            "name": r["name"] or "Beneficiary " + r["id"][:6],
            "location": r["location"],
            "education": r["education_level"],
            "entry_mode": r["entry_mode"],
            "trade": trade,
            "nsqf": r["nsqf_alignment"],
            "status": st,
            "last_contact": r["last_contact_date"] or "Recent"
        })

    conn.close()

    skill_demand_by_trade = [
        {"trade": k, "count": v} for k, v in trade_counts.items()
    ]
    # Sort descending
    skill_demand_by_trade.sort(key=lambda x: x["count"], reverse=True)

    # Compute Regional Training Capacity vs Demand Report
    default_state = "all" if not district or district.lower() == "all" else (region_schemes.get_canonical_state(district) or "Delhi")
    demand_by_trade = database.get_demand_counts_by_state(default_state)
    capacity_report = training_capacity.build_capacity_gap_report(default_state, demand_by_trade)

    return {
        "district": district or "All Districts",
        "enrolments": enrolments,
        "dropouts": dropouts,
        "placements": placements,
        "no_contacts": no_contacts,
        "total_beneficiaries": len(beneficiary_list),
        "skill_demand_by_trade": skill_demand_by_trade,
        "beneficiaries": beneficiary_list,
        "capacity_gap": capacity_report
    }

# --- GET /dashboard/capacity-gap ---
@app.get("/dashboard/capacity-gap")
def get_dashboard_capacity_gap(state: Optional[str] = "Delhi"):
    """
    Returns aggregate demand vs. illustrative training capacity per region with gap analysis.
    """
    req_state = state or "Delhi"
    if req_state.lower() == "all":
        target_state = "all"
    else:
        target_state = region_schemes.get_canonical_state(req_state) or req_state

    demand_by_trade = database.get_demand_counts_by_state(target_state)
    report = training_capacity.build_capacity_gap_report(target_state, demand_by_trade)
    return report

# --- 5. POST /followup/{beneficiary_id} ---
@app.post("/followup/{beneficiary_id}")
def update_followup(beneficiary_id: str, req: FollowUpRequest):
    if req.status not in ["enrolled", "dropped", "placed", "no_contact"]:
        raise HTTPException(status_code=400, detail="Invalid follow-up status")

    try:
        fu_id = database.update_followup(beneficiary_id, req.status)
    except ValueError:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    return {
        "success": True,
        "beneficiary_id": beneficiary_id,
        "status": req.status,
        "follow_up_id": fu_id
    }

# Serve Static UI Files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Nivara API is running"}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Nivara AI Livelihood Assistant on http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)

