"""
WhatsApp Business / Twilio Webhook Service for Nivara (MoSJE / PM-AJAY).
Features:
1. Twilio WhatsApp Webhook (/webhook/whatsapp) with TwiML XML responses.
2. In-app simulator endpoint (/api/whatsapp/simulate).
3. Profile lookup by phone number.
4. 'Reply 1/2/3' menu shortcuts for low-literacy users.
5. Proactive deadline and document reminders.
6. Seamless convergence with Phase 2 RAG & Knowledge pipeline.
"""

import os
import re
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

import rag
import delhi_data_loader as ddl

load_dotenv()

# Read Twilio configuration from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")


# Standard Low-Literacy Numbered Menu Shortcuts
WHATSAPP_MENU_TEXT_EN = """*Nivara — PM-AJAY Livelihood Guide (MoSJE)* 🇮🇳
Official WhatsApp Assistance for SC Beneficiaries (Delhi NCT)

Please reply with a number:
*1* — Free PM-AJAY Schemes & Loans
*2* — Nearest Training Centres (Delhi)
*3* — Check My Eligibility & Documents
*4* — My Deadlines & Reminders
*5* — Ask Any Question (Voice or Text)
*0* — Back to Main Menu

_Or simply type or send a voice note with your trade question!_"""

WHATSAPP_MENU_TEXT_HI = """*निभारा — पीएम-अजय आजीविका एवं कौशल सेवा (MoSJE)* 🇮🇳
दिल्ली अनुसूचित जाति (SC) कल्याण आधिकारिक व्हाट्सएप हेल्पलाइन

कृपया उत्तर देने के लिए नंबर चुनें:
*1* — निःशुल्क पीएम-अजय योजनाएं व ऋण
*2* — दिल्ली में निकटतम प्रशिक्षण केंद्र
*3* — मेरी पात्रता एवं ज़रूरी दस्तावेज़
*4* — मेरी अंतिम तिथियां व रिमाइंडर
*5* — कोई भी सवाल पूछें (बोलकर या लिखकर)
*0* — मुख्य मेनू

_या सीधे अपना सवाल लिखकर अथवा वॉयस नोट भेजकर पूछें!_"""


def normalize_phone(phone_str: str) -> str:
    """Normalizes phone numbers by stripping whatsapp: prefix and non-digits."""
    if not phone_str:
        return "9810123456"
    clean = phone_str.replace("whatsapp:", "").replace("+", "").replace("-", "").replace(" ", "").strip()
    return clean[-10:] if len(clean) >= 10 else clean


def get_profile_by_phone(phone_number: str) -> Dict[str, Any]:
    """
    Looks up stored user profile by phone number from persistent memory.
    If not found, initializes a seeded Delhi beneficiary profile.
    """
    clean_phone = normalize_phone(phone_number)
    user_id = f"wa_{clean_phone}"
    bundle = rag.UserMemoryStore.get_full_memory_bundle(user_id)
    profile = bundle.get("profile", {})
    
    if not profile or not profile.get("name"):
        # Pre-seed demo profile for standard test numbers
        if clean_phone == "9810123456" or clean_phone.endswith("1234"):
            profile = {
                "name": "Rohan Kumar",
                "phone": clean_phone,
                "category": "SC",
                "age": 22,
                "gender": "male",
                "education": "10th Standard",
                "district": "South Delhi",
                "location": "South Delhi",
                "skills": ["Electrical Wiring", "Solar Installations"],
                "income_bracket": "₹1.5 Lakh - ₹2.5 Lakh",
                "annual_income": 180000,
                "goals": "Become a certified Solar PV Installer, NSQF 4"
            }
        else:
            profile = {
                "name": f"Candidate ({clean_phone[-4:]})",
                "phone": clean_phone,
                "category": "SC",
                "age": 24,
                "gender": "all",
                "education": "10th Standard",
                "district": "Central Delhi",
                "location": "Central Delhi",
                "skills": ["General Technical"],
                "income_bracket": "Under ₹1.5 Lakh",
                "annual_income": 140000,
                "goals": "PM-AJAY Vocational Certification & Livelihood"
            }
        rag.UserMemoryStore.update_profile(user_id, profile)
        rag.UserMemoryStore.record_consent(user_id, True)

    return profile


def handle_whatsapp_message(
    from_number: str,
    body: str,
    media_url: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Processes incoming WhatsApp message (text or voice transcript).
    Returns response text, citations, and menu state.
    """
    clean_phone = normalize_phone(from_number)
    user_id = f"wa_{clean_phone}"
    profile = get_profile_by_phone(clean_phone)
    name = profile.get("name", "Beneficiary")
    input_text = (body or "").strip()
    lang = language.lower() if language in ["hi", "en"] else ("hi" if any('\u0900' <= c <= '\u097F' for c in input_text) else "en")

    # 1. Menu Shortcut Navigation (Reply 1/2/3/4/5/0)
    choice = input_text.strip()
    
    if choice in ["0", "menu", "help", "start", "hi", "hello", "namaste", "नमस्ते"]:
        greeting = f"Namaste *{name}*! 🙏" if lang == "en" else f"नमस्ते *{name}* जी! 🙏"
        menu = WHATSAPP_MENU_TEXT_EN if lang == "en" else WHATSAPP_MENU_TEXT_HI
        return {
            "reply": f"{greeting}\n\n{menu}",
            "menu_active": True,
            "options": ["1", "2", "3", "4", "5"],
            "profile": profile
        }

    # Option 1: Free PM-AJAY Schemes
    if choice == "1" or "scheme" in input_text.lower() or "योजना" in input_text:
        schemes = ddl.load_delhi_schemes("delhi")[:3]
        if lang == "hi":
            lines = [f"*{name}* जी, दिल्ली में आपके लिए प्रमुख पीएम-अजय व एससी कल्याण योजनाएं:\n"]
            for idx, s in enumerate(schemes, 1):
                b = s.get("benefits", {})
                lines.append(f"*{idx}. {s['name']}*")
                b = s.get("benefits", {})
                if isinstance(b, list):
                    benefit_summary = "; ".join(b[:2])
                elif isinstance(b, dict):
                    benefit_summary = f"{b.get('financial_assistance', '100% शुल्क माफी')} | छात्रवृत्ति: {b.get('stipend', '₹1,500/माह')}"
                else:
                    benefit_summary = str(b)
                lines.append(f"• लाभ: {benefit_summary}")
                lines.append(f"• लिंक: {s.get('official_url')}\n")
            lines.append("विस्तृत विवरण जानने के लिए योजना का नाम लिखकर भेजें, या मुख्य मेनू के लिए *0* दबाएं।")
            reply = "\n".join(lines)
        else:
            lines = [f"Here are the top PM-AJAY & SC welfare schemes for you in Delhi, *{name}*:\n"]
            for idx, s in enumerate(schemes, 1):
                b = s.get("benefits", {})
                if isinstance(b, list):
                    benefit_summary = "; ".join(b[:2])
                elif isinstance(b, dict):
                    benefit_summary = f"{b.get('financial_assistance', '100% Fee waiver')} | Stipend: {b.get('stipend', '₹1,500/month')}"
                else:
                    benefit_summary = str(b)
                lines.append(f"*{idx}. {s['name']}*")
                lines.append(f"• Benefits: {benefit_summary}")
                lines.append(f"• Portal: {s.get('official_url')}\n")
            lines.append("Type the scheme name for step-by-step guidance, or reply *0* for Main Menu.")
            reply = "\n".join(lines)

        return {"reply": reply, "menu_active": True, "options": ["0", "2", "3", "4"], "profile": profile}

    # Option 2: Nearest Training Centres in Delhi
    if choice == "2" or "centre" in input_text.lower() or "केंद्र" in input_text or "iti" in input_text.lower():
        dist = profile.get("district", "Delhi")
        centres = ddl.search_training_centres(district=dist, region="delhi")
        if not centres:
            centres = ddl.load_delhi_training_centres("delhi")[:3]
        else:
            centres = centres[:3]

        if lang == "hi":
            lines = [f"*{name}* जी, दिल्ली में निकटतम मान्यता प्राप्त कौशल केंद्र:\n"]
            for idx, c in enumerate(centres, 1):
                lines.append(f"*{idx}. {c['centre_name']}* ({c['type']})")
                lines.append(f"• पाठ्यक्रम: {c['course']} (NSQF Level {c['nsqf_level']})")
                lines.append(f"• शुल्क: {c['fee']}")
                lines.append(f"• पता: {c['address']} ({c['district']})")
                lines.append(f"• संपर्क: {c['contact']}\n")
            lines.append("दाखिले की जानकारी के लिए सवाल पूछें, या मुख्य मेनू के लिए *0* भेजें।")
            reply = "\n".join(lines)
        else:
            lines = [f"Accredited PM-AJAY / ITI training centres near *{dist}*, Delhi:\n"]
            for idx, c in enumerate(centres, 1):
                lines.append(f"*{idx}. {c['centre_name']}* ({c['type']})")
                lines.append(f"• Course: {c['course']} (NSQF Level {c['nsqf_level']})")
                lines.append(f"• Fee: {c['fee']}")
                lines.append(f"• Address: {c['address']} ({c['district']})")
                lines.append(f"• Contact: {c['contact']}\n")
            lines.append("To inquire about batch dates, reply with your question or send *0* for Main Menu.")
            reply = "\n".join(lines)

        return {"reply": reply, "menu_active": True, "options": ["0", "1", "3", "4"], "profile": profile}

    # Option 3: Eligibility & Documents
    if choice == "3" or "eligible" in input_text.lower() or "पात्रता" in input_text:
        pmajay = ddl.get_scheme_by_id("delhi-pmajay-gia")
        eval_res = rag.check_eligibility(profile, pmajay) if pmajay else {"eligible": True, "match_percentage": 100, "unmet_criteria": [], "missing_documents": []}
        
        status_line = "आप पूरी तरह पात्र हैं ✓" if eval_res["eligible"] else "पात्रता शर्तें जाँचे ✗"
        if lang == "hi":
            lines = [
                f"*{name}* जी, आपके पंजीकृत प्रोफाइल के आधार पर पीएम-अजय पात्रता:",
                f"• स्थिति: *{status_line}* (मैच स्कोर: {eval_res['match_percentage']}%)",
                f"• जाति श्रेणी: {profile.get('category', 'SC')}",
                f"• योग्यता: {profile.get('education', '10th Standard')}",
                f"• निवास: {profile.get('district', 'Delhi')}\n",
                "*ज़रूरी दस्तावेज़ (Mandatory Documents):*",
                "1. दिल्ली राजस्व विभाग द्वारा जारी SC जाति प्रमाण पत्र",
                "2. आधार कार्ड (बैंक से जुड़ा हुआ)",
                "3. वार्षिक आय प्रमाण पत्र (प्राथमिकता: ₹2.5 लाख तक, कोई निश्चित सीमा नहीं)",
                "4. दिल्ली निवास प्रमाण (राशन कार्ड / वोटर कार्ड)",
                "5. 2 पासपोर्ट आकार फोटो\n",
                "*आवेदन प्रक्रिया (How to Benefit):*",
                "लाभार्थी का चयन अनुमोदित राज्य/ज़िला परियोजनाओं एवं कार्यान्वयन एजेंसियों द्वारा किया जाता है (सीधा व्यक्तिगत आवेदन नहीं)।",
                "अधिक जानकारी के लिए ज़िला समाज कल्याण कार्यालय से संपर्क करें। (मई 2023 दिशा-निर्देशों में कोई हेल्पलाइन मुद्रित नहीं है)।\n",
                "मेनू के लिए *0* भेजें"
            ]
            reply = "\n".join(lines)
        else:
            lines = [
                f"Eligibility Evaluation for *{name}* under PM-AJAY (Delhi):",
                f"• Status: *{'ELIGIBLE ✓' if eval_res['eligible'] else 'CRITERIA NOT FULLY MET ✗'}* ({eval_res['match_percentage']}% Match)",
                f"• Category: {profile.get('category', 'SC')}",
                f"• Education: {profile.get('education', '10th Standard')}",
                f"• Location: {profile.get('district', 'Delhi')}\n",
                "*Mandatory Documents Checklist:*",
                "1. Delhi SC Caste Certificate (SDM / GNCTD verified)",
                "2. Aadhaar Card (Aadhaar-seeded for DBT)",
                "3. Family Income Certificate (Priority up to ₹2.5 Lakh/yr, no fixed cutoff)",
                "4. Delhi Residence Proof (Voter ID / Electricity bill)",
                "5. 2 Passport Photographs\n",
                "*Selection & Application Process:*",
                "Benefits are delivered through approved State/District projects and implementing agencies, not a direct individual application.",
                "Beneficiaries are mobilised and selected by the State/District administration or training partner through a selection committee.",
                "Contact the District Social Welfare/SC Welfare office. (No helpline printed in official May 2023 guidelines).\n",
                "Reply *0* for Main Menu"
            ]
            reply = "\n".join(lines)

        return {"reply": reply, "menu_active": True, "options": ["0", "1", "2", "4"], "profile": profile}

    # Option 4: Deadlines & Reminders
    if choice == "4" or "reminder" in input_text.lower() or "रिमाइंडर" in input_text:
        if lang == "hi":
            reply = (
                f"*{name}* जी, आपके महत्वपूर्ण रिमाइंडर व अंतिम तिथियां:\n\n"
                "⏰ *15 तारीख*: पीएम-अजय Q4 बैच पंजीकरण अंतिम तिथि।\n"
                "📋 *दस्तावेज़*: कृपया अपना दिल्ली SC प्रमाण पत्र व बैंक पासबुक तैयार रखें।\n"
                "📍 *सत्यापन*: निकटतम JSS केंद्र पर बायोमेट्रिक सत्यापन आवश्यक है।\n\n"
                "मुख्य मेनू के लिए *0* भेजें।"
            )
        else:
            reply = (
                f"Important Deadlines & Reminders for *{name}*:\n\n"
                "⏰ *15th Next Month*: PM-AJAY Q4 batch admission closing date.\n"
                "📋 *Document*: Ensure Delhi SC Certificate & Aadhaar-seeded passbook are ready.\n"
                "📍 *Verification*: Visit your allotted Delhi ITI/JSS for biometric verification.\n\n"
                "Reply *0* for Main Menu or ask any question."
            )
        return {"reply": reply, "menu_active": True, "options": ["0", "1", "2", "3"], "profile": profile}

    # Option 5 or Natural Language Question -> Route to Phase 2 RAG Pipeline!
    rag_query = input_text
    if choice == "5":
        rag_query = "What free training courses and stipend schemes are available under PM-AJAY in Delhi?"

    rag_res = rag.ask_rag(
        query=rag_query,
        user_id=user_id,
        language=lang,
        region="delhi"
    )

    clean_answer = rag_res.get("answer", "")
    citations = rag_res.get("citations", [])
    
    citation_lines = []
    if citations:
        citation_lines.append("\n*Official Sources:*")
        for c in citations[:2]:
            citation_lines.append(f"• {c['name'].split('(')[0].strip()}: {c['url']}")

    final_reply = clean_answer + "\n" + "\n".join(citation_lines) + "\n\n_Reply *0* for Main Menu_"
    return {
        "reply": final_reply,
        "menu_active": False,
        "citations": citations,
        "profile": profile,
        "method": rag_res.get("method", "none")
    }


def generate_twiml_response(reply_text: str) -> str:
    """Generates TwiML XML compliant with Twilio WhatsApp Webhook specifications."""
    escaped = (
        reply_text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escaped}</Message>
</Response>"""
