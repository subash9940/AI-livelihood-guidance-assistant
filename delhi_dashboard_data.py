"""
delhi_dashboard_data.py — Curated Sample/Demonstration Data for GIA Dashboard (Delhi Region).
Provides Delhi-scoped metrics for beneficiaries mapped, skilling enrolments by NSQF level,
scheme uptake, 11-district coverage, pending applications queue, and administrative alerts.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

DELHI_DISTRICTS = [
    "Central Delhi",
    "East Delhi",
    "New Delhi",
    "North Delhi",
    "North East Delhi",
    "North West Delhi",
    "Shahdara",
    "South Delhi",
    "South East Delhi",
    "South West Delhi",
    "West Delhi"
]

# District-level baseline mapping for Delhi (curated demonstration data for MoSJE PM-AJAY GIA)
DISTRICT_BASELINES: Dict[str, Dict[str, Any]] = {
    "Central Delhi": {
        "mapped": 68,
        "enrolled": 48,
        "placed": 32,
        "dropouts": 3,
        "target": 80,
        "training_centres": 2,
        "priority_trade": "Assistant Electrician (NSQF 3)"
    },
    "East Delhi": {
        "mapped": 94,
        "enrolled": 62,
        "placed": 45,
        "dropouts": 4,
        "target": 100,
        "training_centres": 3,
        "priority_trade": "Food Processing Technician (NSQF 3)"
    },
    "New Delhi": {
        "mapped": 42,
        "enrolled": 31,
        "placed": 22,
        "dropouts": 2,
        "target": 50,
        "training_centres": 1,
        "priority_trade": "General Duty Assistant (NSQF 4)"
    },
    "North Delhi": {
        "mapped": 88,
        "enrolled": 58,
        "placed": 39,
        "dropouts": 4,
        "target": 95,
        "training_centres": 2,
        "priority_trade": "CNC Machinist & Operator (NSQF 4)"
    },
    "North East Delhi": {
        "mapped": 115,
        "enrolled": 78,
        "placed": 54,
        "dropouts": 6,
        "target": 120,
        "training_centres": 2,
        "priority_trade": "Self-Employed Tailor (NSQF 3)"
    },
    "North West Delhi": {
        "mapped": 132,
        "enrolled": 89,
        "placed": 66,
        "dropouts": 5,
        "target": 140,
        "training_centres": 3,
        "priority_trade": "Solar PV Installer (NSQF 4)"
    },
    "Shahdara": {
        "mapped": 86,
        "enrolled": 55,
        "placed": 41,
        "dropouts": 3,
        "target": 90,
        "training_centres": 1,
        "priority_trade": "Solar PV Installer (NSQF 4)"
    },
    "South Delhi": {
        "mapped": 104,
        "enrolled": 71,
        "placed": 49,
        "dropouts": 4,
        "target": 110,
        "training_centres": 2,
        "priority_trade": "Electric Vehicle Maintenance (NSQF 5)"
    },
    "South East Delhi": {
        "mapped": 98,
        "enrolled": 67,
        "placed": 46,
        "dropouts": 5,
        "target": 105,
        "training_centres": 2,
        "priority_trade": "Apparel & Fashion Tech (NSQF 3)"
    },
    "South West Delhi": {
        "mapped": 110,
        "enrolled": 74,
        "placed": 51,
        "dropouts": 4,
        "target": 115,
        "training_centres": 2,
        "priority_trade": "Drone Service Technician (NSQF 4)"
    },
    "West Delhi": {
        "mapped": 105,
        "enrolled": 73,
        "placed": 53,
        "dropouts": 4,
        "target": 110,
        "training_centres": 2,
        "priority_trade": "Electronics Hardware Tech (NSQF 4)"
    }
}

# Skilling Enrolments by NSQF Level across Delhi
NSQF_LEVEL_DATA = [
    {
        "level": "NSQF Level 3",
        "description": "Foundation / Semi-Skilled Vocational",
        "enrolled": 242,
        "pct": 32.3,
        "key_trades": ["Self-Employed Tailor", "Assistant Electrician", "Food Processing Tech"]
    },
    {
        "level": "NSQF Level 4",
        "description": "Skilled Craftsperson / Technician",
        "enrolled": 348,
        "pct": 46.5,
        "key_trades": ["Solar PV Installer (Suryamitra)", "General Duty Assistant", "CNC Operator"]
    },
    {
        "level": "NSQF Level 5",
        "description": "Advanced Technician / Supervisor",
        "enrolled": 118,
        "pct": 15.8,
        "key_trades": ["Electric Vehicle Maintenance", "Micro-Enterprise Manager", "DSEU Diploma Track"]
    },
    {
        "level": "NSQF Level 6",
        "description": "Master Craftsman / Specialized Lead",
        "enrolled": 40,
        "pct": 5.4,
        "key_trades": ["Advanced Industrial Automation", "Solar Micro-Grid Specialist"]
    }
]

# Scheme Uptake Data (Delhi & Central for SC Livelihoods)
SCHEME_UPTAKE_DATA = [
    {
        "id": "pm-ajay-gia-skill",
        "scheme_name": "PM-AJAY GIA Component (Skill Training & Toolkits)",
        "department": "Ministry of Social Justice & Empowerment",
        "enrolled": 268,
        "target": 300,
        "uptake_pct": 89.3,
        "funds_sanctioned_lakhs": 145.0,
        "funds_utilized_lakhs": 128.5,
        "status": "Active"
    },
    {
        "id": "dsfdc-self-emp",
        "scheme_name": "DSFDC Concessional Self-Employment Loan",
        "department": "Delhi SC/ST/OBC Finance & Dev Corp (GNCTD)",
        "enrolled": 174,
        "target": 200,
        "uptake_pct": 87.0,
        "funds_sanctioned_lakhs": 87.0,
        "funds_utilized_lakhs": 76.2,
        "status": "Active"
    },
    {
        "id": "stand-up-india",
        "scheme_name": "Stand-Up India Scheme (SC Green/Brownfield Loans)",
        "department": "Department of Financial Services / SIDBI",
        "enrolled": 82,
        "target": 100,
        "uptake_pct": 82.0,
        "funds_sanctioned_lakhs": 410.0,
        "funds_utilized_lakhs": 360.0,
        "status": "Active"
    },
    {
        "id": "pmkvy-delhi",
        "scheme_name": "PMKVY 4.0 Special Projects Delhi",
        "department": "Ministry of Skill Development & Entrepreneurship",
        "enrolled": 142,
        "target": 160,
        "uptake_pct": 88.8,
        "funds_sanctioned_lakhs": 48.0,
        "funds_utilized_lakhs": 43.5,
        "status": "Active"
    },
    {
        "id": "post-matric-sc",
        "scheme_name": "Post-Matric Scholarship for SC Students (Delhi)",
        "department": "Dept for Welfare of SC/ST/OBC/Minorities, GNCTD",
        "enrolled": 310,
        "target": 320,
        "uptake_pct": 96.9,
        "funds_sanctioned_lakhs": 93.0,
        "funds_utilized_lakhs": 91.2,
        "status": "Near Target"
    },
    {
        "id": "dseu-skill-cert",
        "scheme_name": "DSEU Short-Term Certificate Courses",
        "department": "Delhi Skill & Entrepreneurship University",
        "enrolled": 105,
        "target": 125,
        "uptake_pct": 84.0,
        "funds_sanctioned_lakhs": 31.5,
        "funds_utilized_lakhs": 27.8,
        "status": "Active"
    }
]

# Pending Beneficiary Applications Queue
PENDING_APPLICATIONS: List[Dict[str, Any]] = [
    {
        "application_id": "APP-DL-2026-081",
        "applicant_name": "Rajesh Kumar",
        "gender": "Male",
        "age": 22,
        "district": "North East Delhi",
        "scheme_name": "PM-AJAY GIA Skill Training & Toolkit",
        "trade": "Solar PV Installer (Suryamitra)",
        "nsqf": "NSQF Level 4",
        "submitted_date": "2026-09-26",
        "status": "Pending Document Verification",
        "documents_status": "Aadhaar & Caste Verified; Income Certificate Pending Physical Inspection",
        "recommended_action": "Schedule Welfare Inspector Home Visit"
    },
    {
        "application_id": "APP-DL-2026-082",
        "applicant_name": "Pooja Devi",
        "gender": "Female",
        "age": 28,
        "district": "Shahdara",
        "scheme_name": "DSFDC Concessional Loan Scheme",
        "trade": "Self-Employed Tailor & Apparel Tech",
        "nsqf": "NSQF Level 3",
        "submitted_date": "2026-09-25",
        "status": "Bank Appraisal",
        "documents_status": "All Documents Verified; Forwarded to Union Bank Dilshad Garden branch",
        "recommended_action": "Track Bank Sanction Order"
    },
    {
        "application_id": "APP-DL-2026-083",
        "applicant_name": "Amit Valmiki",
        "gender": "Male",
        "age": 20,
        "district": "Central Delhi",
        "scheme_name": "PMKVY 4.0 Special Project",
        "trade": "Assistant Electrician",
        "nsqf": "NSQF Level 3",
        "submitted_date": "2026-09-27",
        "status": "Batch Allocation Ready",
        "documents_status": "10th Marksheet, Caste Cert & Bank Passbook Verified",
        "recommended_action": "Assign to ITI Pusa Oct 6 Batch"
    },
    {
        "application_id": "APP-DL-2026-084",
        "applicant_name": "Sunita Rani",
        "gender": "Female",
        "age": 34,
        "district": "East Delhi",
        "scheme_name": "PM-AJAY GIA Capital Subsidy",
        "trade": "Food Processing & Packaging Technician",
        "nsqf": "NSQF Level 3",
        "submitted_date": "2026-09-24",
        "status": "Field Inspection",
        "documents_status": "SHG Membership, Caste, Rent Agreement Uploaded",
        "recommended_action": "Complete District Welfare Officer Inspection (Mayur Vihar)"
    },
    {
        "application_id": "APP-DL-2026-085",
        "applicant_name": "Deepak Jatav",
        "gender": "Male",
        "age": 26,
        "district": "South Delhi",
        "scheme_name": "Stand-Up India Scheme",
        "trade": "CNC Machinist & Light Fabrication",
        "nsqf": "NSQF Level 4",
        "submitted_date": "2026-09-23",
        "status": "Sanction Order Drafted",
        "documents_status": "Detailed Project Report (DPR) approved by SIDBI Delhi Desk",
        "recommended_action": "Authorize 15% PM-AJAY Margin Money Subsidy"
    },
    {
        "application_id": "APP-DL-2026-086",
        "applicant_name": "Manisha Kumari",
        "gender": "Female",
        "age": 19,
        "district": "North West Delhi",
        "scheme_name": "Post-Matric Scholarship for SC Students",
        "trade": "Diploma in Robotics & Automation",
        "nsqf": "NSQF Level 5",
        "submitted_date": "2026-09-28",
        "status": "Document Resubmission Required",
        "documents_status": "Income certificate validity expired on 31 March 2026",
        "recommended_action": "Send SMS / WhatsApp reminder to upload renewed Tehsildar cert"
    },
    {
        "application_id": "APP-DL-2026-087",
        "applicant_name": "Vikram Singh",
        "gender": "Male",
        "age": 24,
        "district": "West Delhi",
        "scheme_name": "DSEU Certificate Program",
        "trade": "Electric Vehicle Maintenance Technician",
        "nsqf": "NSQF Level 5",
        "submitted_date": "2026-09-27",
        "status": "Awaiting Seat Confirmation",
        "documents_status": "ITI Certificate Verified, Aptitude Test Passed (82%)",
        "recommended_action": "Confirm PM-AJAY Reserved Seat at DSEU Rajokri / Pusa"
    }
]

# Administrative Alerts Panel
ADMIN_ALERTS = [
    {
        "id": "ALT-DL-001",
        "severity": "urgent",
        "badge": "Capacity Deficit",
        "title": "Severe Training Capacity Deficit in Shahdara",
        "message": "42 SC candidates applied for Solar PV Installer (NSQF 4) in Shahdara district, but 0 accredited NSDC/PMKVY batch seats are currently active within a 7km radius.",
        "district": "Shahdara",
        "action_label": "Authorize New PMKVY Centre Batch",
        "timestamp": "Today, 09:30 AM"
    },
    {
        "id": "ALT-DL-002",
        "severity": "warning",
        "badge": "Verification Backlog",
        "title": "Document Verification Backlog in North East Delhi",
        "message": "32 Post-Matric SC Scholarship applications have been pending physical verification for >14 days at Seelampur Sub-Divisional Office.",
        "district": "North East Delhi",
        "action_label": "Dispatch Field Verification Team",
        "timestamp": "Yesterday, 04:15 PM"
    },
    {
        "id": "ALT-DL-003",
        "severity": "success",
        "badge": "GIA Fund Sanction",
        "title": "MoSJE Sanction Order #MoSJE-GIA-2026-DL-04 Released",
        "message": "₹48.50 Lakhs capital equipment and stipendiary grant credited to District Welfare Committee account for East Delhi JSS Livelihood Clusters.",
        "district": "East Delhi",
        "action_label": "View Disbursement Schedule",
        "timestamp": "28 Sep 2026, 11:00 AM"
    },
    {
        "id": "ALT-DL-004",
        "severity": "info",
        "badge": "New Batch Opening",
        "title": "DSEU Dwarka EV Technician Batch Enrolment Opens Oct 5",
        "message": "30 subsidized seats under PM-AJAY special quota open for admission in Electric Vehicle Maintenance & Battery Management (NSQF 5).",
        "district": "South West Delhi",
        "action_label": "Send Batch Alert to Candidates",
        "timestamp": "27 Sep 2026, 02:20 PM"
    }
]

def get_delhi_summary_metrics(district: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns curated Delhi summary metrics for GIA dashboard.
    If district is provided and not 'all', filters appropriately.
    """
    is_all = not district or district.strip().lower() in ("all", "all districts", "delhi", "all delhi")

    if is_all:
        tot_mapped = sum(b["mapped"] for b in DISTRICT_BASELINES.values())
        tot_enrolled = sum(b["enrolled"] for b in DISTRICT_BASELINES.values())
        tot_placed = sum(b["placed"] for b in DISTRICT_BASELINES.values())
        tot_dropouts = sum(b["dropouts"] for b in DISTRICT_BASELINES.values())
        tot_target = sum(b["target"] for b in DISTRICT_BASELINES.values())
        selected_district = "All Delhi (Consolidated)"
        app_list = PENDING_APPLICATIONS
        alert_list = ADMIN_ALERTS
    else:
        # Match case-insensitively
        norm = district.strip().lower()
        matched_dist = next((d for d in DELHI_DISTRICTS if d.lower() == norm or norm in d.lower()), "North East Delhi")
        selected_district = matched_dist
        b = DISTRICT_BASELINES.get(matched_dist, DISTRICT_BASELINES["North East Delhi"])
        tot_mapped = b["mapped"]
        tot_enrolled = b["enrolled"]
        tot_placed = b["placed"]
        tot_dropouts = b["dropouts"]
        tot_target = b["target"]
        app_list = [a for a in PENDING_APPLICATIONS if a["district"].lower() == matched_dist.lower()]
        if not app_list:
            app_list = PENDING_APPLICATIONS[:3]
        alert_list = [a for a in ADMIN_ALERTS if a.get("district", "").lower() == matched_dist.lower()]
        if not alert_list:
            alert_list = ADMIN_ALERTS[:2]

    # Build 11-district coverage table
    district_coverage = []
    for d_name in DELHI_DISTRICTS:
        dbase = DISTRICT_BASELINES[d_name]
        cov_pct = round((dbase["mapped"] / dbase["target"]) * 100, 1)
        placement_pct = round((dbase["placed"] / max(dbase["enrolled"], 1)) * 100, 1)
        district_coverage.append({
            "district": d_name,
            "mapped": dbase["mapped"],
            "target": dbase["target"],
            "enrolled": dbase["enrolled"],
            "placed": dbase["placed"],
            "dropouts": dbase["dropouts"],
            "coverage_pct": cov_pct,
            "placement_rate_pct": placement_pct,
            "training_centres": dbase["training_centres"],
            "priority_trade": dbase["priority_trade"]
        })

    # Sort districts by coverage pct descending
    district_coverage.sort(key=lambda x: x["coverage_pct"], reverse=True)

    return {
        "region": "delhi",
        "selected_district": selected_district,
        "total_beneficiaries_mapped": tot_mapped,
        "enrolments": tot_enrolled,
        "placements": tot_placed,
        "dropouts": tot_dropouts,
        "target_beneficiaries": tot_target,
        "overall_coverage_pct": round((tot_mapped / tot_target) * 100, 1),
        "placement_rate_pct": round((tot_placed / max(tot_enrolled, 1)) * 100, 1),
        "grant_sanctioned_cr": 6.85,
        "grant_utilized_cr": 5.76,
        "grant_utilization_pct": 84.1,
        "nsqf_enrolments": NSQF_LEVEL_DATA,
        "scheme_uptake": SCHEME_UPTAKE_DATA,
        "district_coverage": district_coverage,
        "pending_applications": app_list,
        "alerts": alert_list,
        "supported_districts": DELHI_DISTRICTS,
        "disclaimer": "Sample/Curated Demonstration Data for MoSJE PM-AJAY GIA Component (Delhi Region).",
        "is_sample_data": True
    }
