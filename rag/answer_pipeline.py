"""
Grounded RAG Answer Pipeline for Nivara (MoSJE / PM-AJAY).
Pipeline steps:
1. Retrieve top-k chunks from Delhi vector store.
2. Run deterministic eligibility engine on any referenced or context schemes.
3. Synthesize grounded answer with strict citations (official URLs & helplines).
4. Never let LLM decide eligibility; LLM or fallback synthesizer strictly explains rule results.
5. Multilingual support: Hindi, English, and regional Indic languages.
"""

import os
import json
from typing import Dict, List, Any, Optional

from rag.vector_store import retrieve
from rag.eligibility_engine import check_eligibility, evaluate_all_schemes_for_profile
from rag.memory_store import UserMemoryStore
from rag.query_normalizer import normalize_query, get_localized_scheme_name
import delhi_data_loader as ddl
import llm_extractor

# Optional external LLM clients from existing modules
import requests
from dotenv import load_dotenv

load_dotenv()


def format_context_prompt(chunks: List[Dict[str, Any]], eligibility_evals: List[Dict[str, Any]], language: str = "en") -> str:
    """Formats retrieved knowledge chunks and deterministic eligibility into clean markdown context."""
    sections = []
    
    sections.append("### KNOWLEDGE BASE EXCERPTS (DELHI REGION):")
    for idx, c in enumerate(chunks, 1):
        sections.append(f"[{idx}] {c['title']} ({c['entity_type']}):\n{c['text']}")

    if eligibility_evals:
        sections.append("\n### DETERMINISTIC ELIGIBILITY CALCULATION (OFFICIAL RULES):")
        for ev in eligibility_evals:
            status = "ELIGIBLE ✓" if ev["eligible"] else "NOT FULLY ELIGIBLE ✗"
            s_name = get_localized_scheme_name(ev.get("scheme_id", ""), ev["scheme_name"], language)
            sections.append(f"- Scheme: {s_name} -> Status: {status} (Match: {ev['match_percentage']}%)")
            if ev["met_criteria"]:
                sections.append(f"  Criteria Met: {'; '.join(ev['met_criteria'])}")
            if ev["unmet_criteria"]:
                sections.append(f"  Unmet Criteria: {'; '.join(ev['unmet_criteria'])}")
            if ev["missing_documents"]:
                sections.append(f"  Documents Needed: {', '.join(ev['missing_documents'])}")

    return "\n\n".join(sections)


def fallback_synthesizer(
    query: str,
    chunks: List[Dict[str, Any]],
    eligibility_evals: List[Dict[str, Any]],
    language: str = "en",
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """
    High-quality deterministic synthesizer when external LLM API is unavailable / 429.
    Adheres strictly to the ground truth in the knowledge base without hallucination.
    Composes answer in the user's original language, keeping scheme names in English
    with the local-script name in brackets where available.
    """
    lang = language.lower() if language else "en"
    q_lower = query.lower()

    if not chunks:
        if lang == "hi":
            return "माफ़ कीजिए, दिल्ली ज्ञान कोष (Delhi Knowledge Base) में इस विषय पर कोई आधिकारिक जानकारी दर्ज नहीं है। कृपया MoSJE की आधिकारिक वेबसाइट (socialjustice.gov.in) देखें।"
        elif lang == "ta":
            return "மன்னிக்கவும், டெல்லி அறிவுத் தொகுப்பில் இது பற்றிய அதிகாரப்பூர்வ தகவல் இல்லை. தயவுசெய்து அதிகாரப்பூர்வ இணையதளத்தைப் பார்க்கவும்: https://socialjustice.gov.in அல்லது 1800-11-762529 என்ற எண்ணை அழைக்கவும்."
        return "I apologize, but this specific detail is not found in the verified Delhi knowledge base. Please consult the official Ministry portal at https://socialjustice.gov.in or call toll-free helpline 1800-11-762529."

    primary_chunk = chunks[0]
    meta = primary_chunk.get("metadata", {})
    raw_title = primary_chunk.get("title", "Government Scheme")
    scheme_id = meta.get("scheme_id") or primary_chunk.get("entity_id", "")
    title = get_localized_scheme_name(scheme_id, raw_title, lang)
    is_pmajay = str(scheme_id).lower() in ["pm-ajay-gia", "delhi-pmajay-gia", "pmajay"] or "pm-ajay" in raw_title.lower()
    helpline_str = ""
    if not is_pmajay and meta.get("helpline"):
        helpline_str = f"\nHelpline: {meta.get('helpline')}"
        helpline_hi = f"\nहेल्पलाइन: {meta.get('helpline')}"
        helpline_ta = f"\nஉதவி எண்: {meta.get('helpline')}"
    else:
        helpline_hi = ""
        helpline_ta = ""

    # If asking about eligibility
    if any(k in q_lower for k in ["eligible", "patrata", "पात्र", "योग्यता", "am i", "can i", "தகுதி", "அர்ஹత"]):
        if eligibility_evals:
            ev = eligibility_evals[0]
            ev_scheme_name = get_localized_scheme_name(ev.get("scheme_id", ""), ev["scheme_name"], lang)
            status_text = "आप पूरी तरह पात्र हैं (Eligible)" if ev["eligible"] else "आपकी पात्रता में कुछ शर्तें अभी पूरी नहीं हैं (Check Unmet Criteria)"
            if lang == "hi":
                lines = [
                    f"**{ev_scheme_name}** के लिए आपकी पात्रता का मूल्यांकन सरकारी नियमों के आधार पर किया गया है:",
                    f"• **स्थिति**: {status_text} (मैच स्कोर: {ev['match_percentage']}%)",
                ]
                if ev["met_criteria"]:
                    lines.append(f"• **पूरी हुई शर्तें**: {', '.join(ev['met_criteria'])}")
                if ev["unmet_criteria"]:
                    lines.append(f"• **अधूरी शर्तें**: {', '.join(ev['unmet_criteria'])}")
                if ev["missing_documents"]:
                    lines.append(f"• **आवश्यक दस्तावेज़**: {', '.join(ev['missing_documents'])}")
                if is_pmajay:
                    lines.append("\n**महत्वपूर्ण**: पीएम-अजय में सीधा व्यक्तिगत आवेदन नहीं होता। लाभार्थियों का चयन राज्य/ज़िला परियोजनाओं एवं कार्यान्वयन एजेंसियों के माध्यम से किया जाता है। (मई 2023 दिशा-निर्देशों में कोई हेल्पलाइन नहीं है)")
                lines.append(f"\nअधिक जानकारी के लिए आधिकारिक पोर्टल देखें: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}{helpline_hi}")
                return "\n".join(lines)
            elif lang == "ta":
                lines = [
                    f"**{ev_scheme_name}** திட்டத்திற்கான உங்கள் தகுதி அரசு விதிகளின்படி சரிபார்க்கப்பட்டது:",
                    f"• **தகுதி நிலை**: {'தகுதியுடையவர் ✓' if ev['eligible'] else 'நிபந்தனைகள் முழுமையாக பூர்த்தியாகவில்லை ✗'} ({ev['match_percentage']}% பொருத்தம்)",
                ]
                if ev["met_criteria"]:
                    lines.append(f"• **பூர்த்தியான நிபந்தனைகள்**: {'; '.join(ev['met_criteria'])}")
                if ev["unmet_criteria"]:
                    lines.append(f"• **பூர்த்தியாகாத நிபந்தனைகள்**: {'; '.join(ev['unmet_criteria'])}")
                if ev["missing_documents"]:
                    lines.append(f"• **தேவையான ஆவணங்கள்**: {', '.join(ev['missing_documents'])}")
                if is_pmajay:
                    lines.append("\n**குறிப்பு**: நேரடி தனிநபர் விண்ணப்பம் இல்லை. மாநில/மாவட்ட திட்டங்கள் மூலம் பயனாளிகள் தேர்வு செய்யப்படுகிறார்கள்.")
                lines.append(f"\nஅதிகாரப்பூர்வ தளம்: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_ta}")
                return "\n".join(lines)
            else:
                lines = [
                    f"Based on official government rules for **{ev_scheme_name}**, here is your eligibility evaluation:",
                    f"• **Status**: {'Eligible ✓' if ev['eligible'] else 'Criteria Not Fully Met ✗'} ({ev['match_percentage']}% match score)",
                ]
                if ev["met_criteria"]:
                    lines.append(f"• **Met Criteria**: {'; '.join(ev['met_criteria'])}")
                if ev["unmet_criteria"]:
                    lines.append(f"• **Unmet Criteria**: {'; '.join(ev['unmet_criteria'])}")
                if ev["missing_documents"]:
                    lines.append(f"• **Required Documents to Provide**: {', '.join(ev['missing_documents'])}")
                if is_pmajay:
                    lines.append("\n**Note on Selection**: Beneficiaries are selected through approved State/District projects and implementing agencies, not by direct application. There is no direct individual application form or helpline in the May 2023 guidelines.")
                lines.append(f"\nOfficial Portal: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}{helpline_str}")
                return "\n".join(lines)

    # If asking about documents
    if any(k in q_lower for k in ["document", "kagaz", "दस्तावेज़", "दस्तावेज", "kaagaz", "certificate", "praman patra", "ஆவணங்கள்", "சான்றிதழ்"]):
        docs = meta.get("documents_required", [])
        if not docs:
            for c in chunks:
                d = c.get("metadata", {}).get("documents_required", [])
                if d:
                    docs = d
                    break
        if docs:
            doc_list = "\n".join([f"{i+1}. {d}" for i, d in enumerate(docs)])
            if lang == "hi":
                return f"**{title}** के लिए आवश्यक दस्तावेज़:\n\n{doc_list}\n\nआधिकारिक पोर्टल: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}{helpline_hi}"
            elif lang == "ta":
                return f"**{title}** திட்டத்திற்கு தேவையான ஆவணங்கள்:\n\n{doc_list}\n\nஅதிகாரப்பூர்வ தளம்: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_ta}"
            else:
                return f"Here are the mandatory documents required for **{title}**:\n\n{doc_list}\n\nOfficial Portal: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}{helpline_str}"

    # If asking where to apply / steps
    if any(k in q_lower for k in ["where", "apply", "kahan", "kaise", "आवेदन", "फॉर्म", "kaha", "விண்ணப்பிக்க", "எங்கே"]):
        if is_pmajay:
            if lang == "hi":
                return (
                    f"**{title}** में लाभ प्राप्त करने की प्रक्रिया:\n\n"
                    "• **सीधा व्यक्तिगत आवेदन नहीं**: पीएम-अजय में कोई प्रत्यक्ष ऑनलाइन या व्यक्तिगत आवेदन पत्र नहीं होता।\n"
                    "• **परियोजना चयन**: लाभार्थियों को राज्य/ज़िला प्रशासन या प्रशिक्षण भागीदारों द्वारा अनुमोदित राज्य/ज़िला आजीविका परियोजनाओं के माध्यम से चयन समिति द्वारा चुना जाता है।\n"
                    "• **संपर्क**: मार्गदर्शन के लिए अपने ज़िला समाज कल्याण/SC कल्याण कार्यालय या निकटतम अनुमोदित प्रशिक्षण केंद्र से संपर्क करें।\n"
                    "• आधिकारिक पोर्टल: https://pmajay.dosje.gov.in (मई 2023 दिशा-निर्देशों में कोई हेल्पलाइन मुद्रित नहीं है)।"
                )
            else:
                return (
                    f"How to access benefits under **{title}**:\n\n"
                    "• **No Direct Individual Application**: Benefits are delivered through approved State/District projects and implementing agencies, not a direct individual application.\n"
                    "• **Selection Process**: Beneficiaries are mobilised and selected by the State/District administration or the training partner through a selection committee.\n"
                    "• **Where to Inquire**: Contact your District Social Welfare / SC Welfare office or an approved local training partner.\n"
                    "• Official Portal: https://pmajay.dosje.gov.in (No helpline printed in the May 2023 guidelines; no direct application form)."
                )

        steps = meta.get("how_to_apply", [])
        if isinstance(steps, str):
            steps = [steps]
        offices = meta.get("nearest_offices", [])
        if steps or offices:
            if lang == "hi":
                lines = [f"**{title}** के लिए आवेदन करने की प्रक्रिया:"]
                for i, st in enumerate(steps, 1):
                    lines.append(f"{i}. {st}")
                if offices:
                    lines.append("\n**दिल्ली में निकटतम कार्यालय / केंद्र:**")
                    for off in offices[:3]:
                        lines.append(f"• {off.get('name')} ({off.get('district')}): {off.get('address')} (फ़ोन: {off.get('contact')})")
                lines.append(f"\nऑनलाइन आवेदन लिंक: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_hi}")
                return "\n".join(lines)
            elif lang == "ta":
                lines = [f"**{title}** திட்டத்திற்கு விண்ணப்பிக்கும் முறை:"]
                for i, st in enumerate(steps, 1):
                    lines.append(f"{i}. {st}")
                if offices:
                    lines.append("\n**டெல்லியில் உள்ள அருகிலுள்ள அலுவலகங்கள் / மையங்கள்:**")
                    for off in offices[:3]:
                        lines.append(f"• {off.get('name')} ({off.get('district')}): {off.get('address')} (தொலைபேசி: {off.get('contact')})")
                lines.append(f"\nவிண்ணப்ப இணைப்பு: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_ta}")
                return "\n".join(lines)
            else:
                lines = [f"How to apply for **{title}**:"]
                for i, st in enumerate(steps, 1):
                    lines.append(f"{i}. {st}")
                if offices:
                    lines.append("\n**Nearest Delhi Offices / Centers:**")
                    for off in offices[:3]:
                        lines.append(f"• {off.get('name')} ({off.get('district')}): {off.get('address')} (Phone: {off.get('contact')})")
                lines.append(f"\nOnline Application: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_str}")
                return "\n".join(lines)

    # General grounded overview
    if is_pmajay:
        if lang == "hi":
            return f"**{title}**\n\n{primary_chunk['text']}\n\n• **चयन प्रक्रिया**: लाभार्थी अनुमोदित राज्य/ज़िला परियोजनाओं के माध्यम से चुने जाते हैं, सीधा व्यक्तिगत आवेदन नहीं।\n• आधिकारिक पोर्टल: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}"
        return f"**{title}**\n\n{primary_chunk['text']}\n\n• **Selection Process**: Beneficiaries are mobilised and selected through approved State/District projects and implementing agencies, not by direct application. (No individual application form; no helpline printed in May 2023 guidelines).\n• Official Portal: {meta.get('official_url', 'https://pmajay.dosje.gov.in')}"

    if lang == "hi":
        return f"**{title}**\n\n{primary_chunk['text']}\n\nआधिकारिक पोर्टल: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_hi}"
    elif lang == "ta":
        return f"**{title}**\n\n{primary_chunk['text']}\n\nஅதிகாரப்பூர்வ தளம்: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_ta}"
    return f"**{title}**\n\n{primary_chunk['text']}\n\nOfficial Portal: {meta.get('official_url', 'https://socialjustice.gov.in')}{helpline_str}"


def ask_rag(
    query: str,
    user_id: str,
    language: str = "en",
    pathway_context: Optional[Dict[str, Any]] = None,
    region: str = "delhi"
) -> Dict[str, Any]:
    """
    Main RAG question-answering pipeline with translate-then-retrieve.
    Steps:
    1. Normalize query to English via LLM / offline glossary.
    2. Retrieve memory & profile for user_id.
    3. Retrieve top-k chunks from vector store using normalized English query.
    4. Compute deterministic eligibility for any relevant schemes.
    5. Call LLM or fallback grounded synthesizer in user's original language.
    6. Return response with method ('llm' | 'glossary' | 'none') and local-script scheme names.
    """
    # 0. Query Normalization (Translate-then-retrieve)
    norm = normalize_query(query, ui_lang=language)
    english_query = norm["english"]
    detected_lang = norm["detected_lang"]
    norm_method = norm["method"]

    # Original user language for answer synthesis
    target_lang = language if language and language != "auto" else detected_lang
    if target_lang == "en" and detected_lang != "en" and detected_lang != "unknown":
        target_lang = detected_lang

    user_bundle = UserMemoryStore.get_full_memory_bundle(user_id)
    profile = user_bundle.get("profile", {})
    if pathway_context and isinstance(pathway_context, dict):
        if "recommended_trade" in pathway_context:
            profile["recommended_trade"] = pathway_context["recommended_trade"]
        if "sector" in pathway_context:
            profile["sector"] = pathway_context["sector"]

    # 1. Retrieve knowledge using English normalized query
    search_q = english_query
    if pathway_context and pathway_context.get("recommended_trade"):
        search_q = f"{english_query} {pathway_context.get('recommended_trade')}"

    chunks = retrieve(search_q, k=5, region=region)
    if not chunks:
        chunks = retrieve(english_query, k=5, region=region)

    # 2. Extract schemes in context and evaluate deterministic eligibility
    schemes_in_context = []
    eligibility_evals = []

    for c in chunks:
        meta = c.get("metadata", {})
        scheme_id = meta.get("scheme_id") or (c["entity_id"] if c["entity_type"] == "scheme" else None)
        if scheme_id:
            scheme_obj = ddl.get_scheme_by_id(scheme_id, region=region)
            if scheme_obj and scheme_obj["id"] not in [s["id"] for s in schemes_in_context]:
                schemes_in_context.append(scheme_obj)
                ev = check_eligibility(profile, scheme_obj)
                eligibility_evals.append(ev)

    # If query was specifically asking about eligibility and no schemes matched, check PM-AJAY default
    if any(w in english_query.lower() for w in ["eligible", "eligibility", "criteria", "apply"]) and not schemes_in_context:
        pmajay = ddl.get_scheme_by_id("delhi-pmajay-gia", region=region)
        if pmajay:
            schemes_in_context.append(pmajay)
            eligibility_evals.append(check_eligibility(profile, pmajay))

    # 3. Grounded Answer Synthesis
    context_str = format_context_prompt(chunks, eligibility_evals, language=target_lang)
    system_prompt = (
        "You are 'Nivara Saathi', an empathetic, highly knowledgeable AI livelihood & skilling guide for the "
        "Ministry of Social Justice & Empowerment (MoSJE), Government of India, focused on PM-AJAY in Delhi NCT.\n"
        "RULES:\n"
        "1. Ground your answer ONLY in the provided Knowledge Base Excerpts.\n"
        "2. NEVER invent, hallucinate, or alter scheme benefits, grants, or qualifications.\n"
        "3. NEVER decide eligibility yourself. Eligibility is already calculated by the deterministic rules engine in the context. "
        "Explain that exact calculation faithfully.\n"
        "4. Always include the official portal URL and helpline number from the context.\n"
        f"5. Respond concisely, respectfully, and warmly in the user's requested language ({target_lang}). "
        "Keep scheme names in English with the local-script name in brackets where available (e.g. 'PM-AJAY (प्रधानमंत्री अनुसूचित जाति अभ्युदय योजना)')."
    )

    user_msg = f"User Question: {query}\n\nEnglish Normalized: {english_query}\n\nUser Profile: {json.dumps(profile)}\n\nContext:\n{context_str}"
    
    answer_text = ""
    # Try free LLM APIs
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")


    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 600
                },
                timeout=5
            )
            if resp.status_code == 200:
                answer_text = resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    if not answer_text and gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_msg}"}]}
                ],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
            }
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    answer_text = candidates[0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    # If external LLM failed, use our deterministic grounded synthesizer
    if not answer_text:
        answer_text = fallback_synthesizer(query, chunks, eligibility_evals, language=target_lang, profile=profile)

    # 4. Extract Citations & Inline Scheme Cards with Localized Names where available
    citations = []
    scheme_cards = []
    for s in schemes_in_context:
        ev = next((e for e in eligibility_evals if e["scheme_id"] == s["id"]), None)
        loc_name = get_localized_scheme_name(s["id"], s["name"], target_lang)
        v_status = s.get("verification_status", "unverified")
        last_v = s.get("last_verified")
        badge_text = f"Verified {last_v}" if (v_status == "verified" and last_v) else "Sample data - verify on official site"
        is_pmajay = s["id"] in ["pm-ajay-gia", "delhi-pmajay-gia"]

        citations.append({
            "name": loc_name,
            "url": s["official_url"],
            "helpline": None if is_pmajay else s.get("helpline"),
            "department": s["department"],
            "verification_status": v_status,
            "last_verified": last_v,
            "verification_badge": badge_text
        })

        how_to = s.get("how_to_apply", [])
        if isinstance(how_to, str):
            how_to_list = [how_to]
        elif isinstance(how_to, list):
            how_to_list = how_to
        else:
            how_to_list = [str(how_to or "")]

        scheme_cards.append({
            "id": s["id"],
            "name": loc_name,
            "level": s["level"],
            "department": s["department"],
            "active": s.get("active", True),
            "status_note": s.get("status_note"),
            "description": s.get("description") or s.get("notes") or "",
            "benefits": s.get("benefits", []),
            "eligibility_verdict": ev["eligible"] if ev else True,
            "match_percentage": ev["match_percentage"] if ev else 100,
            "met_criteria": ev["met_criteria"] if ev else [],
            "unmet_criteria": ev["unmet_criteria"] if ev else [],
            "documents_required": s.get("documents_required", []),
            "how_to_apply": how_to_list,
            "has_application_form": False if is_pmajay else True,
            "official_url": s["official_url"],
            "guidelines_url": s.get("guidelines_url"),
            "source_url": s.get("source_url") or s["official_url"],
            "helpline": None if is_pmajay else s.get("helpline"),
            "helpline_note": s.get("helpline_note") if is_pmajay else None,
            "nearest_offices": s.get("nearest_offices", []),
            "verification_status": v_status,
            "last_verified": last_v,
            "verified_by": s.get("verified_by"),
            "verification_badge": badge_text
        })

    # 5. Persist turns in user conversation history
    UserMemoryStore.add_conversation_turn(user_id, "user", query)
    UserMemoryStore.add_conversation_turn(user_id, "assistant", answer_text)

    return {
        "user_id": user_id,
        "query": query,
        "normalized_query": english_query,
        "detected_lang": detected_lang,
        "method": norm_method,
        "language": target_lang,
        "answer": answer_text,
        "citations": citations,
        "scheme_cards": scheme_cards,
        "eligibility_evaluations": eligibility_evals,
        "retrieved_chunks_count": len(chunks)
    }

