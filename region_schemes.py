"""
Static Regional Schemes Directory for Nivara.
Provides state-specific livelihood, skill training, and credit linkage schemes.
Keyed by state name with exact benefit, eligibility, and application details.
"""
from typing import Dict, List, Any, Optional

REGIONAL_SCHEMES: Dict[str, List[Dict[str, Any]]] = {
    "Delhi": [
        {
            "name": "Dilli Swarojgar Yojna",
            "provider": "DSFDC",
            "benefit": "Loan up to ₹5 lakh at 6% interest for self-employment ventures (shops, tailoring, dairy, small manufacturing)",
            "eligibility": "Delhi residents, age 18-50, family income under ₹2 lakh/year",
            "how_to_apply": "Apply via DSFDC district office",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        },
        {
            "name": "Delhi Khadi Kaushal Vikas Yojna",
            "provider": "DKVIB",
            "benefit": "Free skill training with stipend for artisans and school/college dropouts",
            "eligibility": "Delhi residents",
            "how_to_apply": "Apply via DKVIB",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        }
    ],
    "Maharashtra": [
        {
            "name": "CMEGP",
            "provider": "Directorate of Industries, Maharashtra",
            "benefit": "Subsidy (up to 35% for SC/ST/special category) + bank loan for new micro-enterprises up to ₹50 lakh",
            "eligibility": "Age 18-45, min 7th pass",
            "how_to_apply": "Apply online via Maharashtra CMEGP portal",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        },
        {
            "name": "Annasaheb Patil Mahamandal Self-Employment Loan",
            "provider": "Annasaheb Patil Arthik Magas Vikas Mahamandal",
            "benefit": "Self-employment loan for educated unemployed youth",
            "eligibility": "Maharashtra resident, economically backward",
            "how_to_apply": "Apply via udyog.mahaswayam.gov.in",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        }
    ],
    "Tamil Nadu": [
        {
            "name": "Vetri Thozhil Munaivor Thittam",
            "provider": "TAHDCO",
            "benefit": "Capital subsidy for first-generation SC/ST entrepreneurs, based on project cost",
            "eligibility": "Age 18-55, family income under ₹3 lakh/year",
            "how_to_apply": "Apply via TAHDCO district office",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        },
        {
            "name": "TAHDCO Skill Development Training",
            "provider": "TAHDCO",
            "benefit": "NSQF-aligned vocational training with placement support, followed by self-employment loan eligibility",
            "eligibility": "SC/ST, family income under ₹3 lakh/year",
            "how_to_apply": "Apply via newscheme.tahdco.com",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        }
    ],
    "Karnataka": [
        {
            "name": "Self Employment Programme",
            "provider": "Dr. B.R. Ambedkar Development Corporation",
            "benefit": "50% subsidy (max ₹35,000) + bank loan for petty shops, tailoring, dairy",
            "eligibility": "SC applicants, Karnataka resident",
            "how_to_apply": "Apply via corporation district office",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        },
        {
            "name": "Amrith Kaushalya",
            "provider": "Govt of Karnataka",
            "benefit": "Free skill training for SC/ST youth",
            "eligibility": "SC/ST, Karnataka resident",
            "how_to_apply": "Apply via Dept of Skill Development, Karnataka",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        }
    ],
    "Uttar Pradesh": [
        {
            "name": "Vishwakarma Shram Samman Yojana",
            "provider": "Directorate of Industries & Enterprise Promotion, UP",
            "benefit": "Free skill training + toolkit up to ₹15,000 + loan up to ₹10 lakh",
            "eligibility": "UP resident, traditional artisan/craftsperson",
            "how_to_apply": "Apply via UP Industries Dept",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        },
        {
            "name": "UPSCFDC Self-Employment Schemes (under PM SC Abhyudaya Yojana)",
            "provider": "UPSCFDC",
            "benefit": "Cluster-based self-employment grants, no income ceiling, priority for income under ₹2.5 lakh/year",
            "eligibility": "SC, UP resident",
            "how_to_apply": "Apply via UPSCFDC district office",
            "is_verified": False,
            "last_checked": "2026-09-27",
            "source_note": "Compiled from official state corporation portals, manually verified as of 2026-09-27"
        }
    ]
}

# Normalization mapping for case-insensitive lookup
_NORMALIZED_SCHEMES = {k.strip().lower(): v for k, v in REGIONAL_SCHEMES.items()}

# Mapping for known district/city references within those states
_DISTRICT_TO_STATE = {
    "pune": "maharashtra",
    "solapur": "maharashtra",
    "nagpur": "maharashtra",
    "kolhapur": "maharashtra",
    "mumbai": "maharashtra",
    "thane": "maharashtra",
    "nashik": "maharashtra",
    "aurangabad": "maharashtra",
    "delhi": "delhi",
    "new delhi": "delhi",
    "madurai": "tamil nadu",
    "chennai": "tamil nadu",
    "coimbatore": "tamil nadu",
    "mysuru": "karnataka",
    "mysore": "karnataka",
    "bengaluru": "karnataka",
    "bangalore": "karnataka",
    "varanasi": "uttar pradesh",
    "kashi": "uttar pradesh",
    "lucknow": "uttar pradesh",
    "kanpur": "uttar pradesh",
    "up": "uttar pradesh",
    "u.p.": "uttar pradesh",
}

def get_regional_schemes(state_or_location: Optional[str]) -> List[Dict[str, Any]]:
    """
    Looks up regional schemes for a given state or location name.
    If the state is not in the dictionary, returns an empty list (not an error, not a guess).
    """
    if not state_or_location or not isinstance(state_or_location, str):
        return []

    cleaned = state_or_location.strip().lower()
    if not cleaned:
        return []

    found = []
    # 1. Direct case-insensitive match against registered states
    if cleaned in _NORMALIZED_SCHEMES:
        found = _NORMALIZED_SCHEMES[cleaned]

    # 2. Check if a registered state name is contained within the string (e.g. "Pune, Maharashtra")
    if not found:
        for state_key, schemes in _NORMALIZED_SCHEMES.items():
            if state_key in cleaned:
                found = schemes
                break

    # 3. Known district to state mapping
    if not found and cleaned in _DISTRICT_TO_STATE:
        mapped_state = _DISTRICT_TO_STATE[cleaned]
        if mapped_state in _NORMALIZED_SCHEMES:
            found = _NORMALIZED_SCHEMES[mapped_state]

    res = []
    for s in found:
        item = dict(s)
        item["verification_status"] = "unverified"
        item["last_verified"] = None
        item["verified_by"] = None
        item["source_url"] = item.get("source_url") or "https://socialjustice.gov.in"
        item["notes"] = "Sample data - verify on official site"
        res.append(item)
    return res

def get_schemes_for_profile(profile: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts the existing state or location field from the beneficiary profile
    and looks up the regional schemes.
    If not in the dictionary, returns an empty list (not an error, not a guess).
    """
    if not profile or not isinstance(profile, dict):
        return []

    # Check existing state or location field
    location_val = profile.get("state") or profile.get("location")
    return get_regional_schemes(location_val)

def get_canonical_state(state_or_location: Optional[str]) -> Optional[str]:
    """
    Normalizes a given state or location string into one of the 5 supported canonical state names:
    'Delhi', 'Maharashtra', 'Tamil Nadu', 'Karnataka', 'Uttar Pradesh'.
    Returns None if no supported state is recognized.
    """
    if not state_or_location or not isinstance(state_or_location, str):
        return None

    cleaned = state_or_location.strip().lower()
    if not cleaned:
        return None

    for state_name in REGIONAL_SCHEMES.keys():
        if state_name.lower() == cleaned:
            return state_name

    for state_name in REGIONAL_SCHEMES.keys():
        if state_name.lower() in cleaned:
            return state_name

    if cleaned in _DISTRICT_TO_STATE:
        mapped_state = _DISTRICT_TO_STATE[cleaned]
        for state_name in REGIONAL_SCHEMES.keys():
            if state_name.lower() == mapped_state:
                return state_name

    return None

