"""
Beneficiary Profiling Engine for Nivara — AI Livelihood Guidance Assistant.
Extracts structured schema fields from conversational natural language input (spoken or transcribed).
"""
import re
from typing import Dict, Any, Tuple, List

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
    (r"\b(healthcare|health|hospital|nurse|nursing|patient|patients|medical|clinic|care|caregiver|medicine)\b|(दवा|इलाज|रुग्ण|आरोग्य|ਸਿਹਤ|ਹਸਪਤਾਲ)", "Healthcare & Patient Support"),
    (r"\b(computer|computers|digital|digitally|data|phone|internet|online|csc)\b|(कंप्यूटर|इंटरनेट|संगणक|ਕੰਪਿਊਟਰ)", "Digital Services & CSC Operation")
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

def extract_profile_from_text(text: str, current_profile: Dict[str, Any] = None) -> Tuple[Dict[str, Any], bool]:
    """
    Extracts structured fields from user conversation input and updates current profile.
    Returns (updated_profile, is_complete).
    """
    profile = dict(current_profile or {})
    lowered = text.lower()

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

    # 3. Interests & Skills
    skills = list(profile.get("skills", []))
    interests = list(profile.get("interests", []))
    for pattern, val in INTEREST_SKILL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            if val not in interests:
                interests.append(val)
            if val not in skills:
                skills.append(val)
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
    # A profile is complete when we have enough signals to recommend:
    # At least education OR family occupation, AND at least one interest/skill or mobility signal
    has_edu = bool(profile.get("education_level"))
    has_fam = bool(profile.get("family_occupation"))
    has_interest = len(profile.get("interests", [])) > 0
    has_mobility = bool(profile.get("mobility_constraint"))

    is_complete = (has_interest and (has_edu or has_fam or has_mobility)) or ((has_edu or has_fam) and has_mobility) or (has_edu and has_fam)

    return profile, is_complete

def generate_next_prompt(profile: Dict[str, Any], language: str = "en") -> str:
    """
    Generates a natural, spoken follow-up prompt based on what is missing from the profile.
    """
    missing_edu = not profile.get("education_level")
    missing_interest = len(profile.get("interests", [])) == 0
    missing_mobility = not profile.get("mobility_constraint")

    if language == "hi":
        if missing_interest and missing_edu:
            return "नमस्ते! आप अपने बारे में बताएं — आपकी पढ़ाई कितनी हुई है, और आप किस तरह का काम सीखना या करना चाहते हैं?"
        elif missing_edu:
            return "बहुत अच्छा! क्या आप अपनी पढ़ाई के बारे में बता सकते हैं, जैसे 8वीं, 10वीं या 12वीं पास?"
        elif missing_mobility:
            return "क्या आप काम या ट्रेनिंग के लिए गाँव से बाहर जा सकते हैं, या गाँव के पास ही काम करना चाहते हैं?"
        else:
            return "क्या आप खुद की दुकान या व्यवसाय शुरू करना चाहते हैं, या किसी कंपनी में नौकरी करना चाहते हैं?"

    elif language == "mr":
        if missing_interest and missing_edu:
            return "नमस्कार! तुमच्याबद्दल सांगा — तुमचे शिक्षण किती झाले आहे आणि तुम्हाला कोणत्या प्रकारचे काम शिकायला आवडेल?"
        elif missing_edu:
            return "छान! तुमचे शिक्षण कितवीपर्यंत झाले आहे ते सांगू शकता का (उदा. ८वी, १०वी किंवा १२वी)?"
        elif missing_mobility:
            return "तुम्ही प्रशिक्षणासाठी बाहेर तालुक्यात जाऊ शकता का, की गावाजवळच काम हवे आहे?"
        else:
            return "तुम्हाला स्वतःचा व्यवसाय सुरू करायचा आहे की नोकरी करायची आहे?"

    elif language == "pa":
        if missing_interest and missing_edu:
            return "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ — ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ ਅਤੇ ਤੁਸੀਂ ਕਿਸ ਤਰ੍ਹਾਂ ਦਾ ਕੰਮ ਸਿੱਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?"
        elif missing_edu:
            return "ਬਹੁਤ ਵਧੀਆ! ਤੁਹਾਡੀ ਪੜ੍ਹਾਈ ਕਿੰਨੀ ਹੈ, ਜਿਵੇਂ 8ਵੀਂ, 10ਵੀਂ ਜਾਂ 12ਵੀਂ?"
        elif missing_mobility:
            return "ਕੀ ਤੁਸੀਂ ਸਿਖਲਾਈ ਲਈ ਬਾਹਰ ਜਾ ਸਕਦੇ ਹੋ ਜਾਂ ਪਿੰਡ ਵਿੱਚ ਹੀ ਕੰਮ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ?"
        else:
            return "ਕੀ ਤੁਸੀਂ ਆਪਣਾ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ ਜਾਂ ਨੌਕਰੀ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ?"

    else:
        if missing_interest and missing_edu:
            return "Welcome! Please tell me about yourself — what is your education level, and what kind of work or skills interest you?"
        elif missing_edu:
            return "Great! Could you tell me about your education level, such as 8th, 10th, or 12th standard?"
        elif missing_mobility:
            return "Can you travel to the district training center, or do you need opportunities close to your village?"
        else:
            return "Would you prefer self-employment (your own small enterprise) or wage employment with a monthly salary?"
