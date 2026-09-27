"""
Local Opportunities Data for Nivara — AI Livelihood Guidance Assistant.
Provides synthetic/illustrative region-specific employment and enterprise opportunities
keyed by (state, trade_key). These are clearly marked as illustrative data pending
integration with live labor market APIs (e.g., NCS Portal, UDYAM).

PS 26097 Requirement: "Region-specific employment or enterprise opportunities
in and around the beneficiary."
"""
from typing import Dict, List, Any, Optional

# Illustrative local opportunities data — synthetic, not from a live registry
# Each entry: title, employer_type, distance, source_note
LOCAL_OPPORTUNITIES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "Delhi": {
        "food_processing": [
            {"title": "Spice packaging unit assistant", "employer_type": "PMEGP Micro-Enterprise", "distance": "Within 5 km", "wage_range": "₹8,000–12,000/month"},
            {"title": "Community kitchen / midday meal helper", "employer_type": "NGO / Annapurna Scheme", "distance": "Within 10 km", "wage_range": "₹7,000–9,000/month"},
            {"title": "Sweet shop production assistant", "employer_type": "Local SME", "distance": "Within 8 km", "wage_range": "₹9,000–11,000/month"}
        ],
        "apparel_tailoring": [
            {"title": "Garment stitching operator (export unit)", "employer_type": "Apparel Export House, Okhla", "distance": "Within 12 km", "wage_range": "₹10,000–14,000/month"},
            {"title": "School uniform contract tailor", "employer_type": "Municipal Corporation tender", "distance": "Within 5 km", "wage_range": "₹8,000–12,000/month"}
        ],
        "solar_technician": [
            {"title": "Rooftop solar installer — PM Surya Ghar", "employer_type": "DISCOM empaneled vendor", "distance": "Within 15 km", "wage_range": "₹12,000–18,000/month"},
            {"title": "Solar panel cleaning & maintenance crew", "employer_type": "Facility management company", "distance": "Within 10 km", "wage_range": "₹10,000–13,000/month"}
        ],
        "automotive_ev": [
            {"title": "Two-wheeler service center mechanic", "employer_type": "Authorized dealership (Hero/Honda)", "distance": "Within 8 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "EV battery swap station attendant", "employer_type": "Private EV startup", "distance": "Within 15 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "healthcare_assistant": [
            {"title": "Ward assistant — Govt. hospital", "employer_type": "Delhi State Health Mission", "distance": "Within 10 km", "wage_range": "₹12,000–16,000/month"},
            {"title": "Home-care attendant for elderly", "employer_type": "Private healthcare agency", "distance": "Within 5 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "digital_csc": [
            {"title": "CSC VLE (Village Level Entrepreneur)", "employer_type": "CSC e-Governance Services India", "distance": "Within 3 km", "wage_range": "₹12,000–20,000/month (commission-based)"},
            {"title": "Data entry operator — e-District portal", "employer_type": "District Collector office", "distance": "Within 10 km", "wage_range": "₹10,000–13,000/month"}
        ]
    },
    "Maharashtra": {
        "food_processing": [
            {"title": "Pickle & papad production unit worker", "employer_type": "Women's SHG (Mahila Bachat Gat)", "distance": "Within 5 km", "wage_range": "₹7,000–10,000/month"},
            {"title": "Dairy processing plant helper", "employer_type": "District Milk Cooperative", "distance": "Within 15 km", "wage_range": "₹9,000–12,000/month"},
            {"title": "Organic food packaging assistant", "employer_type": "FPO (Farmer Producer Organization)", "distance": "Within 10 km", "wage_range": "₹8,000–11,000/month"}
        ],
        "apparel_tailoring": [
            {"title": "Paithani saree border weaver assistant", "employer_type": "Handloom Cooperative, Yeola", "distance": "Within 20 km", "wage_range": "₹9,000–13,000/month"},
            {"title": "Readymade garment stitching operator", "employer_type": "Apparel unit, MIDC", "distance": "Within 12 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "solar_technician": [
            {"title": "Agricultural solar pump installer", "employer_type": "MEDA empaneled contractor", "distance": "Within 20 km", "wage_range": "₹13,000–18,000/month"},
            {"title": "Solar street light maintenance technician", "employer_type": "Gram Panchayat / ZP contractor", "distance": "Within 10 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "automotive_ev": [
            {"title": "Two-wheeler service technician", "employer_type": "Bajaj/TVS authorized workshop", "distance": "Within 10 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "Auto-rickshaw / 3-wheeler mechanic", "employer_type": "Independent garage cluster", "distance": "Within 8 km", "wage_range": "₹10,000–13,000/month"}
        ],
        "healthcare_assistant": [
            {"title": "ANM / GDA at Primary Health Center", "employer_type": "NHM Maharashtra", "distance": "Within 15 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "Nursing home patient care attendant", "employer_type": "Private nursing home", "distance": "Within 10 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "digital_csc": [
            {"title": "MahaOnline / Aaple Sarkar kiosk operator", "employer_type": "CSC / MahaOnline franchise", "distance": "Within 5 km", "wage_range": "₹10,000–18,000/month (commission-based)"},
            {"title": "Bank Mitra / micro-ATM agent", "employer_type": "Nationalized bank BC model", "distance": "Within 3 km", "wage_range": "₹8,000–15,000/month (transaction-based)"}
        ]
    },
    "Tamil Nadu": {
        "food_processing": [
            {"title": "Rice mill & flour processing helper", "employer_type": "KVIC-registered micro unit", "distance": "Within 10 km", "wage_range": "₹8,000–11,000/month"},
            {"title": "Coconut oil / copra processing worker", "employer_type": "Local cooperative society", "distance": "Within 8 km", "wage_range": "₹7,000–10,000/month"}
        ],
        "apparel_tailoring": [
            {"title": "Garment export unit operator", "employer_type": "Tirupur Knitwear cluster", "distance": "Within 20 km", "wage_range": "₹10,000–15,000/month"},
            {"title": "Blouse / petticoat stitching (home-based)", "employer_type": "SHG / local boutique", "distance": "Within 5 km", "wage_range": "₹6,000–10,000/month"}
        ],
        "solar_technician": [
            {"title": "Solar water heater installer", "employer_type": "TEDA empaneled company", "distance": "Within 15 km", "wage_range": "₹12,000–16,000/month"},
            {"title": "Solar micro-grid maintenance technician", "employer_type": "Rural electrification project", "distance": "Within 20 km", "wage_range": "₹11,000–15,000/month"}
        ],
        "automotive_ev": [
            {"title": "Two-wheeler mechanic (TVS/Yamaha)", "employer_type": "Authorized service center", "distance": "Within 10 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "E-rickshaw / EV fleet maintenance", "employer_type": "Smart city mobility project", "distance": "Within 15 km", "wage_range": "₹12,000–16,000/month"}
        ],
        "healthcare_assistant": [
            {"title": "GDA at Govt. district hospital", "employer_type": "TN Health Department", "distance": "Within 12 km", "wage_range": "₹12,000–16,000/month"},
            {"title": "ASHA worker / health sub-center aide", "employer_type": "NHM Tamil Nadu", "distance": "Within 5 km", "wage_range": "₹8,000–12,000/month"}
        ],
        "digital_csc": [
            {"title": "e-Sevai center operator", "employer_type": "TN e-Governance Agency", "distance": "Within 5 km", "wage_range": "₹10,000–16,000/month (commission-based)"},
            {"title": "Data entry / digitization assistant", "employer_type": "District collectorate", "distance": "Within 10 km", "wage_range": "₹9,000–12,000/month"}
        ]
    },
    "Karnataka": {
        "food_processing": [
            {"title": "Millet-based snack production helper", "employer_type": "FPO / Ragi processing SHG", "distance": "Within 10 km", "wage_range": "₹7,000–10,000/month"},
            {"title": "Spice sorting & grading plant worker", "employer_type": "KVIC unit, Hassan", "distance": "Within 15 km", "wage_range": "₹8,000–11,000/month"}
        ],
        "apparel_tailoring": [
            {"title": "Silk saree finishing assistant", "employer_type": "Mysuru Silk Cooperative", "distance": "Within 10 km", "wage_range": "₹9,000–13,000/month"},
            {"title": "School uniform / workwear stitching", "employer_type": "Govt. contract (BBMP / ZP)", "distance": "Within 8 km", "wage_range": "₹8,000–12,000/month"}
        ],
        "solar_technician": [
            {"title": "Rooftop solar PV installer", "employer_type": "KREDL empaneled company", "distance": "Within 15 km", "wage_range": "₹13,000–17,000/month"},
            {"title": "Solar pump technician for farms", "employer_type": "State Agriculture Dept. scheme", "distance": "Within 20 km", "wage_range": "₹11,000–15,000/month"}
        ],
        "automotive_ev": [
            {"title": "Two-wheeler service technician", "employer_type": "Hero / Honda dealership", "distance": "Within 10 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "EV charging station operator", "employer_type": "BESCOM / private EV infra company", "distance": "Within 12 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "healthcare_assistant": [
            {"title": "Patient care attendant — Taluk hospital", "employer_type": "Karnataka Health Dept.", "distance": "Within 10 km", "wage_range": "₹11,000–15,000/month"},
            {"title": "Elderly home-care assistant", "employer_type": "Private nursing & care agency", "distance": "Within 8 km", "wage_range": "₹10,000–13,000/month"}
        ],
        "digital_csc": [
            {"title": "Nada Kacheri / Bhoomi kiosk operator", "employer_type": "CSC / Karnataka e-Governance", "distance": "Within 5 km", "wage_range": "₹10,000–16,000/month (commission-based)"},
            {"title": "Digital literacy trainer (PMGDISHA)", "employer_type": "CSC Academy", "distance": "Within 8 km", "wage_range": "₹8,000–12,000/month"}
        ]
    },
    "Uttar Pradesh": {
        "food_processing": [
            {"title": "Atta / dal milling unit helper", "employer_type": "PMEGP micro-enterprise", "distance": "Within 5 km", "wage_range": "₹6,000–9,000/month"},
            {"title": "Mango pulp / amla processing worker", "employer_type": "FPO / District horticulture unit", "distance": "Within 12 km", "wage_range": "₹7,000–10,000/month"},
            {"title": "Dairy collection center operator", "employer_type": "UPCDF (Parag) cooperative", "distance": "Within 8 km", "wage_range": "₹8,000–11,000/month"}
        ],
        "apparel_tailoring": [
            {"title": "Chikankari embroidery artisan", "employer_type": "Lucknow Chikan Cluster", "distance": "Within 10 km", "wage_range": "₹7,000–12,000/month (piece-rate)"},
            {"title": "Carpet weaving assistant", "employer_type": "Bhadohi Carpet Export Cluster", "distance": "Within 15 km", "wage_range": "₹8,000–12,000/month"}
        ],
        "solar_technician": [
            {"title": "Solar pump installer (Kusum Yojana)", "employer_type": "UPNEDA empaneled contractor", "distance": "Within 20 km", "wage_range": "₹12,000–16,000/month"},
            {"title": "Street light solar panel maintenance", "employer_type": "Nagar Palika / smart city project", "distance": "Within 10 km", "wage_range": "₹10,000–13,000/month"}
        ],
        "automotive_ev": [
            {"title": "Two-wheeler mechanic", "employer_type": "Hero / Bajaj workshop", "distance": "Within 8 km", "wage_range": "₹9,000–13,000/month"},
            {"title": "E-rickshaw repair & battery technician", "employer_type": "E-rickshaw assembly cluster", "distance": "Within 10 km", "wage_range": "₹10,000–14,000/month"}
        ],
        "healthcare_assistant": [
            {"title": "Ward assistant — CHC / PHC", "employer_type": "NHM Uttar Pradesh", "distance": "Within 12 km", "wage_range": "₹10,000–14,000/month"},
            {"title": "ASHA facilitator / health volunteer", "employer_type": "State Health Mission", "distance": "Within 5 km", "wage_range": "₹6,000–10,000/month"}
        ],
        "digital_csc": [
            {"title": "CSC Jan Seva Kendra operator", "employer_type": "CSC e-Governance Services", "distance": "Within 3 km", "wage_range": "₹10,000–18,000/month (commission-based)"},
            {"title": "e-Mitra / Lokvani kiosk assistant", "employer_type": "District administration", "distance": "Within 8 km", "wage_range": "₹8,000–12,000/month"}
        ]
    }
}

# Data provenance metadata
DATA_PROVENANCE = {
    "is_verified": False,
    "last_checked": "2026-09-27",
    "source_note": "Illustrative opportunities compiled from publicly available job portals, scheme guidelines, and NCS data patterns. Not sourced from a live labor market registry. Verify with local employment exchange or NCS Portal (ncs.gov.in).",
    "disclaimer": "Illustrative — verify with local employment exchange"
}


def get_local_opportunities(state: Optional[str], trade_key: Optional[str]) -> List[Dict[str, Any]]:
    """
    Returns illustrative local employment/enterprise opportunities for a given state and trade.
    Returns empty list if state or trade not found (no guessing).
    Each opportunity includes a provenance disclaimer.
    """
    if not state or not trade_key:
        return []

    state_data = LOCAL_OPPORTUNITIES.get(state)
    if not state_data:
        return []

    opportunities = state_data.get(trade_key, [])

    # Attach provenance metadata to each opportunity
    result = []
    for opp in opportunities:
        entry = dict(opp)
        entry["is_verified"] = DATA_PROVENANCE["is_verified"]
        entry["last_checked"] = DATA_PROVENANCE["last_checked"]
        entry["source_note"] = DATA_PROVENANCE["source_note"]
        entry["disclaimer"] = DATA_PROVENANCE["disclaimer"]
        result.append(entry)

    return result
