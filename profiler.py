"""
Beneficiary Profiling Engine for Nivara — AI Livelihood Guidance Assistant.
Extracts structured schema fields from conversational natural language input (spoken or transcribed).
"""
import re
from typing import Dict, Any, Tuple, List
import llm_extractor

# Common multilingual vocabulary patterns
EDU_PATTERNS = [
    (r"\b(10th|tenth|10\s*pass)\b|(10\s*वीं|१०वी|दहावी|ਦਸਵੀਂ)", "10th Standard"),
    (r"\b(12th|twelfth|inter|intermediate)\b|(12\s*वीं|१२वी|बारावी|ਬਾਰ੍ਹਵੀਂ)", "12th Standard"),
    (r"\b(8th|eighth)\b|(8\s*वीं|८वी|आठवी|ਅੱਠਵੀਂ)", "8th Standard"),
    (r"\b(5th|fifth)\b|(5\s*वीं|५वी|पाचवी)", "Primary (5th Standard)"),
    (r"\b(graduate|degree|ba|b\.a|bcom|bsc)\b|(पदवी|ਗ੍ਰੈਜੂਏਟ)", "Graduate"),
    (r"\b(uneducated|illiterate|no\s*school)\b|(अनपढ़|अशिक्षित|निरक्षर|ਨਿਰੱਖਰ)", "Informal / No formal schooling")
]

FAMILY_OCC_PATTERNS = [
    (r"\b(farm|farming|agri|agriculture|crop|crops|field|fields)\b|(खेती|किसान|कृषक|शेती|शेतकरी|ਖੇਤੀ|ਕਿਸਾਨ)", "Agriculture & Farming"),
    (r"\b(labour|labor|daily\s*wage|mazdoor)\b|(मजदूरी|मजदूर|हमाली|मजुरी|ਮਜ਼ਦੂਰੀ)", "Daily Wage Labor"),
    (r"\b(tailor|tailoring|darji|silai|weaver|weaving)\b|(दर्जी|सिलाई|शिंपी|ਦਰਜ਼ੀ)", "Tailoring / Weaving"),
    (r"\b(artisan|potter|blacksmith|lohar|kumhar)\b|(हस्तशिल्प|कारीगर|लोहार)", "Artisan / Handicrafts"),
    (r"\b(shop|retail|dukan)\b|(किराना|दुकान|व्यापार|ਦੁਕਾਨ)", "Small Retail / Kirana"),
    (r"\b(animal|dairy|cow|buffalo|pashu)\b|(गाय|भैंस|पशुपालन|ਦੁੱਧ|ਡੇਅਰੀ)", "Dairy & Animal Husbandry")
]

INTEREST_SKILL_PATTERNS = [
    (r"\b(food|cook|cooking|processing|pickle|masala)\b|(खाद्य|खाना|अन्न|लोणचे|मसाले|ਫੂਡ|ਖਾਣਾ|ਅਚਾਰ)", "Food Processing & Preservation"),
    (r"\b(sew|sewing|tailor|tailoring|cloth|clothes|clothing|stitch|stitching|dress|apparel)\b|(सिलाई|कपड़े|शिलाई|कपडे|ਸਿਲਾਈ|ਕੱਪੜੇ)", "Tailoring & Garment Making"),
    (r"\b(solar|sun|electric|electrical|wire|wiring|bijli|panel|panels)\b|(सोलर|सौर|बिजली|वायरिंग|ਸੋਲਰ|ਬਿਜਲੀ)", "Solar PV & Electrical Installations"),
    (r"\b(mechanic|bike|bikes|motorcycle|motorcycles|car|cars|garage|repair|automotive|vehicle|vehicles|scooter|scooters|ev)\b|(गाड़ी|मोटर|दुरुस्ती|ਮਕੈਨਿਕ|ਗੱਡੀ)", "Two-Wheeler & EV Maintenance"),
    (r"\b(healthcare|health|hospital|nurse|nursing|patient\s*care|patient\s*support|patients|medical|clinic|caregiver|medicine)\b|(दवा|इलाज|रुग्ण|आरोग्य|ਸਿਹਤ|ਹਸਪਤਾਲ)", "Healthcare & Patient Support"),
    (r"\b(computer|computers|digital|digitally|data|phone|internet|online|csc)\b|(कंप्यूटर|इंटरनेट|संगणक|ਕੰਪਿਊਟਰ)", "Digital Services & CSC Operation")
]

TRADITIONAL_SKILL_PATTERNS = [
    (r"\b(farm|farming|agri|crop|crops|kheti|khet|cultivat|harvest|sow|sowing|plough)\b|(खेती|किसान|फसल|वावर|ਬਿਜਾਈ|ਵਾਢੀ)", "Traditional Farming & Crop Cultivation"),
    (r"\b(sew|sewing|stitch|stitching|darji|silai|bunai|kadai|embroid|handloom|loom)\b|(सिलाई|बुनाई|कढ़ाई|विणकाम|कशीदा)", "Traditional Tailoring & Handloom Weaving"),
    (r"\b(potter|pottery|clay|terracotta|mitti|matka|bartan|kumhar)\b|(कुम्हार|मिट्टी|भांडी|ਘੁਮਿਆਰ)", "Traditional Pottery & Clay Modeling"),
    (r"\b(blacksmith|metal|iron|loha|lohar)\b|(लोहार|लोखंड|ਲੁਹਾਰ)", "Traditional Blacksmithing & Metal Craft"),
    (r"\b(carpenter|carpentry|wood|woodwork|furniture|badhai)\b|(बढ़ई|सुतार|લાકડું|ਤਰਖਾਣ)", "Traditional Carpentry & Woodcraft"),
    (r"\b(dairy|cattle|cow|buffalo|milking|milk|pashu|livestock|goat)\b|(पशुपालन|डेयरी|दूध|गोपालन|ਪਸ਼ੂ)", "Livestock Rearing & Dairy Management"),
    (r"\b(artisan|craft|handicraft|handmade|zari|bamboo|cane)\b|(हस्तशिल्प|कारीगरी|हस्तकला|ਦਸਤਕਾਰੀ)", "Traditional Handicrafts & Artisan Work"),
    (r"\b(retail|kirana|shopkeeping|counter\s*sales|dukan)\b|(किराना|दुकान|दुकानदारी|ਵਪਾਰ)", "Traditional Retail & Shopkeeping")
]

SOFT_SKILL_PATTERNS = [
    (r"\b(good\s*with\s*people|people\s*person|friendly|social|interpersonal|loogon\s*se\s*baat|milansar)\b|(मिलनसार|लोगों\s*से\s*बात|लोकांशी\s*संभाषण|ਮਿਲਣਸਾਰ)", "Interpersonal Skills (Good with people)"),
    (r"\b(patient|patience|calm|composed|peaceful|sabar|dhairya)\b|(धैर्य|शांत|धीरज|ਸਬਰ|ਸ਼ਾਂਤ)", "Patient & Attentive"),
    (r"\b(hardworking|hard\s*working|diligent|dedicated|laborious|mehnat|mehnati|kamath)\b|(मेहनती|कष्ट|लगातार\s*काम|ਮਿਹਨਤੀ)", "Hardworking & Dedicated"),
    (r"\b(communication|speaking|talk|explaining|bolchal|baat\s*karna)\b|(बातचीत|संवाद|बोलचाल|ਸੰਚਾਰ)", "Effective Communication"),
    (r"\b(teamwork|team\s*player|collaborative|cooperative|saath\s*me\s*kaam)\b|(सहयोग|टीम\s*वर्क|एकत्र\s*काम)", "Team Player & Collaborative"),
    (r"\b(quick\s*learner|fast\s*learner|learns\s*fast|adaptable|jaldi\s*seekh)\b|(जल्दी\s*सीखना|शिकण्याची\s*तयारी|ਚੁਸਤ)", "Quick Learner & Adaptable"),
    (r"\b(punctual|punctuality|disciplined|timely|samay\s*par)\b|(समय\s*का\s*पाबंद|वेळेचे\s*पालन|ਨਿਯਮਿਤ)", "Punctual & Disciplined"),
    (r"\b(honest|integrity|trustworthy|truthful|imandar|vishwasu)\b|(ईमानदार|विश्वसनीय|ਪ੍ਰਮਾਣਿਕ)", "Honest & Trustworthy"),
    (r"\b(problem\s*solver|resourceful|practical|jugad|solution)\b|(जुगाड़|समस्या\s*समाधान|ਸਮੱਸਿਆ\s*ਹੱਲ)", "Practical Problem Solving & Resourcefulness")
]


MOBILITY_PATTERNS = [
    (r"\b(can\s*not\s*travel|cannot\s*travel|can\'t\s*travel|don\'t\s*want\s*to\s*go\s*far|stay\s*near|home\s*based|within\s*village|village\s*only|local\s*only)\b|(गाँव\s*में|गावातच|दूर\s*नहीं|जा\s*नहीं\s*सकते|लांब\s*जाऊ\s*शकत\s*नाही|ਨੇੜੇ|ਪਿੰਡ\s*ਵਿੱਚ)", "Cannot travel far (Restricted to village/cluster)"),
    (r"\b(can\s*travel|willing\s*to\s*travel|anywhere|district\s*center|town|commute)\b|(शहर\s*जा\s*सकते|शहर|तालुक्यात|तालुका|ਜਾ\s*ਸਕਦਾ)", "Willing to commute to District/Taluka center")
]

EMP_PREF_PATTERNS = [
    (r"\b(own\s*business|self\s*employ|self\s*employment|dukan|shop|khud\s*ka|business)\b|(स्वयंरोजगार|खुद\s*का\s*काम|स्वतःचा\s*व्यवसाय|दुकान|दुकानदार|ਆਪਣਾ\s*ਕੰਮ)", "self_employment"),
    (r"\b(job|naukri|salary|wage|company)\b|(नौकरी|नोकरी|पगार|ਕੰਪਨੀ|ਨੌਕਰੀ)", "wage_employment")
]

STATE_PATTERNS = [
    (r"\b(delhi|new\s*delhi)\b|(दिल्ली|ਦਿੱਲੀ)", "Delhi"),
    (r"\b(maharashtra)\b|(महाराष्ट्र|ਮਹਾਰਾਸ਼ਟਰ)", "Maharashtra"),
    (r"\b(tamil\s*nadu)\b|(तमिलनाडु|தமிழ்நாடு)", "Tamil Nadu"),
    (r"\b(karnataka)\b|(कर्नाटक|ਕਰਨਾਟਕ|ಕರ್ನಾಟಕ)", "Karnataka"),
    (r"\b(uttar\s*pradesh|u\.?p\.?)\b|(उत्तर\s*प्रदेश|ਉੱਤਰ\s*ਪ੍ਰਦੇਸ਼)", "Uttar Pradesh"),
]

LOCATION_PATTERNS = [
    (r"\b(delhi|new\s*delhi)\b|(दिल्ली|ਦਿੱਲੀ)", "Delhi"),
    (r"\b(maharashtra)\b|(महाराष्ट्र|ਮਹਾਰਾਸ਼ਟਰ)", "Maharashtra"),
    (r"\b(tamil\s*nadu)\b|(तमिलनाडु|தமிழ்நாடு)", "Tamil Nadu"),
    (r"\b(karnataka)\b|(कर्नाटक|ਕਰਨਾਟਕ|ಕರ್ನಾಟಕ)", "Karnataka"),
    (r"\b(uttar\s*pradesh|u\.?p\.?)\b|(उत्तर\s*प्रदेश|ਉੱਤਰ\s*ਪ੍ਰਦੇਸ਼)", "Uttar Pradesh"),
    (r"\b(pune)\b|(पुणे|ਪੂਨੇ)", "Pune"),
    (r"\b(solapur)\b|(सोलापूर|सोलापुर)", "Solapur"),
    (r"\b(nagpur)\b|(नागपूर|नागपुर)", "Nagpur"),
    (r"\b(amritsar)\b|(ਅੰਮ੍ਰਿਤਸਰ|अमृतसर)", "Amritsar"),
    (r"\b(ludhiana)\b|(ਲੁਧਿਆਣਾ|लुधियाना)", "Ludhiana"),
    (r"\b(varanasi|kashi)\b|(वाराणसी|बनारस)", "Varanasi"),
    (r"\b(patna)\b|(पटना)", "Patna"),
    (r"\b(kolhapur)\b|(कोल्हापूर)", "Kolhapur"),
    (r"\b(madurai)\b|(மதுரை|मदुरै)", "Madurai"),
    (r"\b(mysuru|mysore)\b|(ಮೈಸೂರು|मैसूर)", "Mysuru"),
    (r"\b(ranchi)\b|(राँची|रांची)", "Ranchi"),
    (r"\b(medinipur|midnapore)\b|(মেদিনীপুর|मेदनीपुर)", "Medinipur"),
    (r"\b(kamrup|guwahati)\b|(কামৰূপ|कामरूप)", "Kamrup"),
    (r"\b(bhopal)\b|(भोपाल)", "Bhopal"),
    (r"\b(raipur)\b|(रायपुर)", "Raipur")
]

SOFT_SKILLS_SET = {
    "Interpersonal Skills (Good with people)",
    "Patient & Attentive",
    "Hardworking & Dedicated",
    "Effective Communication",
    "Team Player & Collaborative",
    "Quick Learner & Adaptable",
    "Punctual & Disciplined",
    "Honest & Trustworthy",
    "Practical Problem Solving & Resourcefulness"
}

def is_soft_skill(skill_name: str) -> bool:
    """Checks whether a skill string represents a soft/interpersonal skill."""
    s = skill_name.strip().lower()
    for soft in SOFT_SKILLS_SET:
        if s == soft.lower() or soft.lower() in s or s in soft.lower():
            return True
    soft_keywords = {
        "communication", "patient", "patience", "hardworking", "hard working", "interpersonal",
        "good with people", "people skill", "people", "team", "teamwork", "adaptable", "punctual",
        "honest", "trustworthy", "problem solving", "leadership", "collaborative", "dedicated",
        "discipline", "disciplined", "attentive", "soft skill", "listening", "empathy", "friendly",
        "relationship", "multitask", "reliable", "dependable"
    }
    return any(k in s for k in soft_keywords)

def has_concrete_interest_or_technical_skill(profile: Dict[str, Any]) -> bool:
    """
    Checks if profile has at least one concrete trade interest OR technical skill.
    Soft skills alone return False.
    """
    if len(profile.get("interests", [])) > 0:
        return True
    for sk in profile.get("skills", []):
        if not is_soft_skill(sk):
            return True
    return False

def is_profile_complete(profile: Dict[str, Any]) -> bool:
    """
    A beneficiary profile is considered complete and eligible for recommendation
    ONLY IF it has at least one concrete interest OR technical skill.
    Soft-skill phrases alone do not satisfy completeness.
    """
    return has_concrete_interest_or_technical_skill(profile)

def extract_profile_from_text(text: str, current_profile: Dict[str, Any] = None) -> Tuple[Dict[str, Any], bool]:
    """
    Extracts structured fields from user conversation input and updates current profile.
    Returns (updated_profile, is_complete).
    """
    profile = dict(current_profile or {})

    # Optional Multi-Provider LLM Extraction (Claude / Gemini) if API key configured
    if llm_extractor.has_llm_provider():
        try:
            llm_prof = llm_extractor.extract_profile_with_llm(text)
            if llm_prof:
                for k, v in llm_prof.items():
                    if v and not profile.get(k):
                        profile[k] = v
                    elif k in ("skills", "interests") and v:
                        existing = profile.get(k, [])
                        if isinstance(existing, list) and isinstance(v, list):
                            profile[k] = list(dict.fromkeys(existing + v))
        except Exception:
            # Fallback seamlessly to deterministic rule-based cascade
            pass

    lowered = text.lower()

    # 0. Name extraction (from common conversational patterns)
    if not profile.get("name"):
        name_patterns = [
            r"(?:my\s+name\s+is|i\s+am|i'm|this\s+is|naam\s+hai|mera\s+naam|मेरा\s+नाम|माझे\s+नाव|ਮੇਰਾ\s+ਨਾਮ)\s+([A-Za-z\u0900-\u0D7F]{2,}(?:\s+[A-Za-z\u0900-\u0D7F]{2,})*)",
        ]
        for pat in name_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                name_candidate = m.group(1).strip()
                # Avoid capturing common non-name words
                skip_words = {"interested", "from", "living", "working", "looking", "studying", "here", "there"}
                first_word = name_candidate.split()[0].lower()
                if first_word not in skip_words and len(name_candidate) >= 2:
                    profile["name"] = name_candidate.title()
                break


    # 1. Education
    for pattern, val in EDU_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["education_level"] = val
            break

    # 2. Family Occupation
    for pattern, val in FAMILY_OCC_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["family_occupation"] = val
            break

    # 3. Interests & Skills (Broad definition: Technical, Vocational, Traditional, and Soft/Interpersonal)
    skills = list(profile.get("skills", []))
    interests = list(profile.get("interests", []))

    # A. Vocational / Technical patterns
    for pattern, val in INTEREST_SKILL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            if val not in interests:
                interests.append(val)
            if val not in skills:
                skills.append(val)

    # B. Traditional / Family-occupation-based skills
    for pattern, val in TRADITIONAL_SKILL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            if val not in skills:
                skills.append(val)

    # C. Soft / Interpersonal strengths (good with people, patient, hardworking, etc.)
    for pattern, val in SOFT_SKILL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            if val not in skills:
                skills.append(val)

    # D. Inherit traditional skill from family occupation if present
    fam_occ = profile.get("family_occupation")
    if fam_occ:
        fam_skill_map = {
            "Agriculture & Farming": "Traditional Farming & Agriculture Knowledge",
            "Tailoring / Weaving": "Traditional Tailoring & Handloom Weaving",
            "Artisan / Handicrafts": "Traditional Handicrafts & Artisan Craft",
            "Small Retail / Kirana": "Traditional Retail & Shopkeeping",
            "Dairy & Animal Husbandry": "Livestock Rearing & Dairy Management",
            "Daily Wage Labor": "Manual Labor & Field Execution"
        }
        mapped_skill = fam_skill_map.get(fam_occ, f"Traditional Experience in {fam_occ}")
        if mapped_skill not in skills:
            skills.append(mapped_skill)

    profile["skills"] = skills
    profile["interests"] = interests

    # 4. Mobility Constraint
    for pattern, val in MOBILITY_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["mobility_constraint"] = val
            break

    # 5. Employment Preference
    for pattern, val in EMP_PREF_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["employment_preference"] = val
            break

    # 6. Location & State
    for pattern, val in LOCATION_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["location"] = val
            break

    for pattern, val in STATE_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            profile["state"] = val
            break

    # Current Livelihood default or inferred
    if not profile.get("current_livelihood"):
        if profile.get("family_occupation"):
            profile["current_livelihood"] = f"Assisting family in {profile['family_occupation']}"
        else:
            profile["current_livelihood"] = "Informal wage worker / Seeking opportunity"

    # Default location if missing
    if not profile.get("location"):
        profile["location"] = "Your Local District"

    # Profile Completeness Logic:
    # Require at least one concrete interest OR technical skill before generating any recommendation.
    # If the user has only provided soft skills, is_complete MUST be False.
    is_complete = is_profile_complete(profile)

    return profile, is_complete

def generate_next_prompt(profile: Dict[str, Any], language: str = "en") -> str:
    """
    Generates a natural, spoken follow-up prompt based on what is missing from the profile.
    Implements a priority-ordered question cascade covering all 7 PS 26097-required data points:
      1. Name  2. Education  3. Skills/Interests  4. State/Location
      5. Family Occupation  6. Mobility  7. Employment Preference
    If the user has provided soft skills but no concrete interest or technical skill,
    returns a clarifying follow-up question asking for a concrete interest or technical skill.
    """
    has_concrete = has_concrete_interest_or_technical_skill(profile)
    has_soft = any(is_soft_skill(s) for s in profile.get("skills", []))

    # Priority 0: If the beneficiary only provided soft skills with no concrete interest or technical skill
    if has_soft and not has_concrete:
        prompts = {
            "hi": "अपनी व्यक्तिगत खूबियों (जैसे मेहनत, धैर्य, या व्यवहार) को साझा करने के लिए धन्यवाद! सही ट्रेड का सुझाव देने के लिए, क्या आप किसी व्यावहारिक हुनर, रुचि या कार्यक्षेत्र (जैसे सिलाई, बिजली/वायरिंग, वाहन मरम्मत, खाद्य प्रसंस्करण, कंप्यूटर, या खेती) के बारे में बता सकते हैं?",
            "mr": "तुमचे वैयक्तिक गुण (उदा. कष्टाळूपणा, संयम किंवा संवाद) सांगितल्याबद्दल धन्यवाद! योग्य उपजीविकेची शिफारस करण्यासाठी, तुम्हाला कोणत्या विशिष्ट कामात किंवा कौशल्यात रस आहे (उदा. सिलाई, इलेक्ट्रिकल काम, वाहन दुरुस्ती, अन्न प्रक्रिया, संगणक किंवा शेती) ते सांगू शकाल का?",
            "pa": "ਆਪਣੀਆਂ ਨਿੱਜੀ ਖੂਬੀਆਂ (ਜਿਵੇਂ ਮਿਹਨਤ, ਸਬਰ ਜਾਂ ਮਿਲਣਸਾਰ ਹੋਣਾ) ਸਾਂਝੀਆਂ ਕਰਨ ਲਈ ਧੰਨਵਾਦ! ਸਹੀ ਰੋਜ਼ਗਾਰ ਦੀ ਸਿਫ਼ਾਰਸ਼ ਕਰਨ ਲਈ, ਕੀ ਤੁਸੀਂ ਕਿਸੇ ਖਾਸ ਕੰਮ, ਹੁਨਰ ਜਾਂ ਖੇਤਰ (ਜਿਵੇਂ ਸਿਲਾਈ, ਬਿਜਲੀ ਦਾ ਕੰਮ, ਗੱਡੀਆਂ ਦੀ ਮੁਰੰਮਤ, ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ, ਕੰਪਿਊਟਰ ਜਾਂ ਖੇਤੀਬਾੜੀ) ਬਾਰੇ ਦੱਸ ਸਕਦੇ ਹੋ?",
            "en": "Thank you for sharing your personal strengths! To recommend the right trade, could you tell me about a specific practical skill, trade interest, or work area you'd like to pursue (for example: electrical wiring, tailoring, two-wheeler repair, food processing, computers, or agriculture)?"
        }
        return prompts.get(language, prompts["en"])

    # Determine what's missing — priority-ordered cascade for 7 PS-required data points
    missing_skills = not has_concrete and not has_soft
    missing_edu = not profile.get("education_level")
    missing_name = not profile.get("name")
    missing_state = not profile.get("state") and not profile.get("location")
    missing_family_occ = not profile.get("family_occupation")
    missing_mobility = not profile.get("mobility_constraint")
    missing_emp_pref = not profile.get("employment_preference")

    # Priority 1: Name + Education + Skills (initial greeting — bundle if multiple are missing)
    if missing_skills and missing_edu:
        prompts = {
            "hi": "नमस्ते! आप अपने बारे में बताएं — आपका नाम क्या है, पढ़ाई कितनी हुई है, और आपकी क्या खूबियां या हुनर हैं? यह कोई पारंपरिक काम (जैसे खेती, सिलाई), तकनीकी हुनर, या आपकी व्यक्तिगत ताकत (जैसे लोगों से अच्छा मेलजोल, धैर्य, या मेहनत) भी हो सकती है।",
            "mr": "नमस्कार! तुमच्याबद्दल सांगा — तुमचे नाव, शिक्षण किती झाले आणि तुमच्याकडे कोणती कौशल्ये किंवा गुण आहेत? हे कोणतेही कौटुंबिक काम (उदा. शेती, विणकाम), तांत्रिक काम, किंवा तुमचे व्यक्तिमत्त्व गुण (उदा. लोकांसोबत चांगले संबंध, संयम, कष्ट करण्याची तयारी) असू शकते.",
            "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ — ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ, ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ ਅਤੇ ਤੁਹਾਡਾ ਕੀ ਹੁਨਰ ਜਾਂ ਖੂਬੀ ਹੈ? ਇਹ ਕੋਈ ਪਰਿਵਾਰਕ ਕੰਮ (ਜਿਵੇਂ ਖੇਤੀ, ਸਿਲਾਈ), ਤਕਨੀਕੀ ਹੁਨਰ, ਜਾਂ ਤੁਹਾਡੀਆਂ ਨਿੱਜੀ ਖੂਬੀਆਂ (ਜਿਵੇਂ ਲੋਕਾਂ ਨਾਲ ਚੰਗਾ ਰਾਬਤਾ, ਸਬਰ ਜਾਂ ਮਿਹਨਤ) ਵੀ ਹੋ ਸਕਦਾ ਹੈ।",
            "en": "Welcome! Please tell me about yourself — what is your name, education level, and what are your strengths or skills? This could be family or traditional work (like farming or tailoring), practical technical skills, or personal strengths like being good with people, patient, or hardworking."
        }
        return prompts.get(language, prompts["en"])

    # Priority 2: Skills missing (education already captured)
    if missing_skills:
        prompts = {
            "hi": "बहुत अच्छा! क्या आप अपने कौशल या खूबियों के बारे में बता सकते हैं? यह केवल तकनीकी काम ही नहीं, बल्कि पारंपरिक पारिवारिक काम (जैसे खेती, शिल्प) या आपकी व्यक्तिगत ताकत (जैसे लोगों से अच्छा व्यवहार, धैर्य, या लगन) भी हो सकती है।",
            "mr": "छान! तुमच्याकडे कोणती कौशल्ये किंवा ताकदीचे पैलू आहेत ते सांगू शकाल का? हे केवळ तांत्रिक काम नसून पारंपरिक कौटुंबिक काम किंवा लोकांसोबत चांगले वागणे, संयम व कष्टाळूपणा यासारखे वैयक्तिक गुणही असू शकतात.",
            "pa": "ਬਹੁਤ ਵਧੀਆ! ਕੀ ਤੁਸੀਂ ਆਪਣੇ ਕਿਸੇ ਹੁਨਰ ਜਾਂ ਖੂਬੀ ਬਾਰੇ ਦੱਸ ਸਕਦੇ ਹੋ? ਇਹ ਕੋਈ ਰਵਾਇਤੀ ਜਾਂ ਪਰਿਵਾਰਕ ਕੰਮ ਹੋ ਸਕਦਾ ਹੈ ਜਾਂ ਨਿੱਜੀ ਖੂਬੀਆਂ ਜਿਵੇਂ ਲੋਕਾਂ ਨਾਲ ਮਿਲਣਸਾਰ ਹੋਣਾ, ਸਬਰ ਜਾਂ ਮਿਹਨਤੀ ਸੁਭਾਅ ਵੀ ਹੋ ਸਕਦਾ ਹੈ।",
            "en": "Great! Could you tell me about any skills or strengths you have? It doesn't have to be formal technical training — it could be traditional or family work (like farming or crafts), or personal strengths like being good with people, patient, or hardworking."
        }
        return prompts.get(language, prompts["en"])

    # Priority 3: Education missing (skills already captured)
    if missing_edu:
        prompts = {
            "hi": "बहुत अच्छा! क्या आप अपनी पढ़ाई के बारे में बता सकते हैं, जैसे 8वीं, 10वीं या 12वीं पास?",
            "mr": "छान! तुमचे शिक्षण कितवीपर्यंत झाले आहे ते सांगू शकता का (उदा. ८वी, १०वी किंवा १२वी)?",
            "pa": "ਬਹੁਤ ਵਧੀਆ! ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ, ਜਿਵੇਂ 8ਵੀਂ, 10ਵੀਂ ਜਾਂ 12ਵੀਂ?",
            "en": "Great! Could you tell me about your education level, such as 8th, 10th, or 12th standard?"
        }
        return prompts.get(language, prompts["en"])

    # Priority 4: State/Location missing
    if missing_state:
        prompts = {
            "hi": "आप किस राज्य या जिले में रहते हैं? (जैसे दिल्ली, महाराष्ट्र, तमिलनाडु, कर्नाटक, या उत्तर प्रदेश)",
            "mr": "तुम्ही कोणत्या राज्यात किंवा जिल्ह्यात राहता? (उदा. दिल्ली, महाराष्ट्र, तामिळनाडू, कर्नाटक, किंवा उत्तर प्रदेश)",
            "pa": "ਤੁਸੀਂ ਕਿਸ ਰਾਜ ਜਾਂ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਰਹਿੰਦੇ ਹੋ? (ਜਿਵੇਂ ਦਿੱਲੀ, ਮਹਾਰਾਸ਼ਟਰ, ਤਾਮਿਲਨਾਡੂ, ਕਰਨਾਟਕ, ਜਾਂ ਉੱਤਰ ਪ੍ਰਦੇਸ਼)",
            "en": "Which state or district do you live in? (For example: Delhi, Maharashtra, Tamil Nadu, Karnataka, or Uttar Pradesh)"
        }
        return prompts.get(language, prompts["en"])

    # Priority 5: Family Occupation missing
    if missing_family_occ:
        prompts = {
            "hi": "आपके परिवार का पारंपरिक पेशा क्या है? (जैसे खेती, मजदूरी, सिलाई, दुकानदारी, या पशुपालन)",
            "mr": "तुमच्या कुटुंबाचा पारंपरिक व्यवसाय कोणता आहे? (उदा. शेती, मजुरी, शिलाई, दुकानदारी, किंवा पशुपालन)",
            "pa": "ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਦਾ ਰਵਾਇਤੀ ਕੰਮ ਕੀ ਹੈ? (ਜਿਵੇਂ ਖੇਤੀ, ਮਜ਼ਦੂਰੀ, ਸਿਲਾਈ, ਦੁਕਾਨਦਾਰੀ, ਜਾਂ ਪਸ਼ੂ ਪਾਲਣ)",
            "en": "What is your family's traditional occupation? (For example: farming, daily wage labor, tailoring, shopkeeping, or dairy/animal husbandry)"
        }
        return prompts.get(language, prompts["en"])

    # Priority 6: Mobility constraint missing
    if missing_mobility:
        prompts = {
            "hi": "क्या आप प्रशिक्षण के लिए पास के शहर या तालुके तक जा सकते हैं, या आपको घर/गाँव के पास ही रहना ज़रूरी है?",
            "mr": "तुम्ही प्रशिक्षणासाठी जवळच्या शहरात किंवा तालुक्यात जाऊ शकता का, की तुम्हाला गावाजवळच राहणे आवश्यक आहे?",
            "pa": "ਕੀ ਤੁਸੀਂ ਸਿਖਲਾਈ ਲਈ ਨੇੜੇ ਦੇ ਸ਼ਹਿਰ ਜਾ ਸਕਦੇ ਹੋ, ਜਾਂ ਤੁਹਾਨੂੰ ਘਰ/ਪਿੰਡ ਦੇ ਨੇੜੇ ਹੀ ਰਹਿਣਾ ਜ਼ਰੂਰੀ ਹੈ?",
            "en": "Can you travel to a nearby town or district center for training, or do you need something close to home?"
        }
        return prompts.get(language, prompts["en"])

    # Priority 7: Employment Preference missing
    if missing_emp_pref:
        prompts = {
            "hi": "क्या आप खुद की दुकान या व्यवसाय शुरू करना चाहते हैं, या किसी कंपनी में नौकरी करना चाहते हैं?",
            "mr": "तुम्हाला स्वतःचा व्यवसाय सुरू करायचा आहे की नोकरी करायची आहे?",
            "pa": "ਕੀ ਤੁਸੀਂ ਆਪਣਾ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ ਜਾਂ ਨੌਕਰੀ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
            "en": "Would you prefer self-employment (your own small enterprise) or wage employment with a monthly salary?"
        }
        return prompts.get(language, prompts["en"])

    # All 7 fields captured — profile is rich enough for recommendation
    prompts = {
        "hi": "धन्यवाद! आपकी पूरी जानकारी मिल गई है। अब हम आपके लिए सबसे उपयुक्त पीएम-अजय कौशल योजना तैयार कर रहे हैं।",
        "mr": "धन्यवाद! तुमची सर्व माहिती मिळाली आहे. आता तुमच्यासाठी योग्य पीएम-अजय कौशल्य योजना तयार केली जात आहे.",
        "pa": "ਧੰਨਵਾਦ! ਤੁਹਾਡੀ ਪੂਰੀ ਜਾਣਕਾਰੀ ਮਿਲ ਗਈ ਹੈ। ਹੁਣ ਅਸੀਂ ਤੁਹਾਡੇ ਲਈ ਸਭ ਤੋਂ ਢੁਕਵੀਂ ਪੀਐਮ-ਅਜੇ ਸਿਖਲਾਈ ਯੋਜਨਾ ਤਿਆਰ ਕਰ ਰਹੇ ਹਾਂ।",
        "en": "Thank you! We have all the information we need. Generating your customized PM-AJAY livelihood roadmap now."
    }
    return prompts.get(language, prompts["en"])

