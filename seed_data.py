"""
Seed data generator for Nivara — AI Livelihood Guidance Assistant.
Populates realistic initial beneficiaries, follow-up records, and district stats.
"""
import uuid
import json
from datetime import datetime, timedelta
import random
from database import get_connection, init_db

DISTRICTS = [
    "Pune", "Solapur", "Nagpur",      # West
    "Amritsar", "Varanasi",           # North
    "Madurai", "Mysuru",              # South
    "Ranchi", "Medinipur",            # East
    "Kamrup",                         # North-East
    "Bhopal", "Raipur"                # Central
]

SEED_PROFILES = [
    {
        "name": "Ramesh Jadhav",
        "language": "mr",
        "location": "Pune",
        "mobility_constraint": "Restricted to village/cluster",
        "education_level": "10th Standard",
        "family_occupation": "Agriculture & Farming",
        "current_livelihood": "Seasonal agricultural labor",
        "skills": ["Food Processing & Preservation"],
        "interests": ["Food Processing & Preservation"],
        "employment_preference": "self_employment",
        "entry_mode": "app",
        "trade": "Food Processing & Agri-Value Addition Technician",
        "status": "enrolled",
        "nsqf": "NSQF Level 3 (FICSI/Q0102)",
        "programme": "PM-AJAY Free Skill Training & Certification",
        "centre": "Jan Shikshan Sansthan (JSS Pune Hub)",
        "opportunity": "Micro-Enterprise spice and grain packaging unit with Mudra loan"
    },
    {
        "name": "Sunita Kamble",
        "language": "mr",
        "location": "Solapur",
        "mobility_constraint": "Cannot travel far",
        "education_level": "8th Standard",
        "family_occupation": "Weaving & Handloom",
        "current_livelihood": "Home-based traditional handloom helper",
        "skills": ["Tailoring & Garment Making"],
        "interests": ["Tailoring & Garment Making"],
        "employment_preference": "self_employment",
        "entry_mode": "facilitator",
        "trade": "Self-Employed Tailor & Apparel Specialist",
        "status": "placed",
        "nsqf": "NSQF Level 3 (AMH/Q1947)",
        "programme": "PM-AJAY Special Tailoring Initiative",
        "centre": "RSETI Solapur Skill Lab",
        "opportunity": "Village Tailoring Enterprise with PM-AJAY capital subsidy"
    },
    {
        "name": "Gurpreet Singh",
        "language": "pa",
        "location": "Amritsar",
        "mobility_constraint": "Willing to commute to District center",
        "education_level": "12th Standard",
        "family_occupation": "Agriculture & Farming",
        "current_livelihood": "Unemployed youth",
        "skills": ["Solar PV & Electrical Installations"],
        "interests": ["Solar PV & Electrical Installations"],
        "employment_preference": "wage_employment",
        "entry_mode": "app",
        "trade": "Solar PV Installer (Suryamitra)",
        "status": "placed",
        "nsqf": "NSQF Level 4 (SGJ/Q0101)",
        "programme": "PM-AJAY Suryamitra Green Energy Skill Initiative",
        "centre": "Govt ITI Amritsar Solar Wing",
        "opportunity": "Rooftop solar installation contractor for PM Surya Ghar"
    },
    {
        "name": "Kavita Shinde",
        "language": "mr",
        "location": "Pune",
        "mobility_constraint": "Willing to commute to District center",
        "education_level": "10th Standard",
        "family_occupation": "Daily Wage Labor",
        "current_livelihood": "Domestic house help",
        "skills": ["Healthcare & Patient Support"],
        "interests": ["Healthcare & Patient Support"],
        "employment_preference": "wage_employment",
        "entry_mode": "call",
        "trade": "General Duty Assistant (Healthcare Support)",
        "status": "enrolled",
        "nsqf": "NSQF Level 4 (HSS/Q5101)",
        "programme": "PM-AJAY Healthcare Livelihood Track",
        "centre": "District Hospital Skill Lab Pune",
        "opportunity": "Community Health Center General Duty Assistant"
    },
    {
        "name": "Priya Murugan",
        "language": "ta",
        "location": "Madurai",
        "mobility_constraint": "Cannot travel far",
        "education_level": "8th Standard",
        "family_occupation": "Weaving & Handloom",
        "current_livelihood": "Handloom assistant",
        "skills": ["Tailoring & Garment Making"],
        "interests": ["Tailoring & Garment Making"],
        "employment_preference": "self_employment",
        "entry_mode": "app",
        "trade": "Self-Employed Tailor & Apparel Specialist",
        "status": "placed",
        "nsqf": "NSQF Level 3 (AMH/Q1947)",
        "programme": "PM-AJAY Special Tailoring Initiative",
        "centre": "Jan Shikshan Sansthan Madurai",
        "opportunity": "Boutique self-employment unit with Mudra loan"
    },
    {
        "name": "Siddharth Soren",
        "language": "hi",
        "location": "Ranchi",
        "mobility_constraint": "Willing to commute to District center",
        "education_level": "12th Standard",
        "family_occupation": "Daily Wage Labor",
        "current_livelihood": "Electrical apprentice",
        "skills": ["Solar PV & Electrical Installations"],
        "interests": ["Solar PV & Electrical Installations"],
        "employment_preference": "wage_employment",
        "entry_mode": "app",
        "trade": "Solar PV Installer (Suryamitra)",
        "status": "enrolled",
        "nsqf": "NSQF Level 4 (SGJ/Q0101)",
        "programme": "PM-AJAY Suryamitra Green Energy Skill Initiative",
        "centre": "Govt ITI Ranchi",
        "opportunity": "Solar rooftop installation vendor with DISCOM"
    },
    {
        "name": "Monali Das",
        "language": "en",
        "location": "Kamrup",
        "mobility_constraint": "Local village cluster only",
        "education_level": "10th Standard",
        "family_occupation": "Small Retail / Kirana",
        "current_livelihood": "Store assistant",
        "skills": ["Digital Services & CSC Operation"],
        "interests": ["Digital Services & CSC Operation"],
        "employment_preference": "self_employment",
        "entry_mode": "facilitator",
        "trade": "Digital Services Operator & CSC Citizen Facilitator",
        "status": "placed",
        "nsqf": "NSQF Level 4 (SSC/Q2212)",
        "programme": "PM-AJAY Rural Digital Track",
        "centre": "District NIELIT Kamrup",
        "opportunity": "Common Service Center (CSC) VLE Kendra"
    },
    {
        "name": "Deepak Verma",
        "language": "hi",
        "location": "Bhopal",
        "mobility_constraint": "Willing to commute",
        "education_level": "10th Standard",
        "family_occupation": "Mechanic Helper",
        "current_livelihood": "Garage assistant",
        "skills": ["Two-Wheeler & EV Maintenance"],
        "interests": ["Two-Wheeler & EV Maintenance"],
        "employment_preference": "self_employment",
        "entry_mode": "app",
        "trade": "Two-Wheeler & EV Service Technician",
        "status": "enrolled",
        "nsqf": "NSQF Level 3 (ASC/Q1411)",
        "programme": "PM-AJAY Electric Mobility Track",
        "centre": "District Skill Center Bhopal",
        "opportunity": "Two-wheeler EV battery swapping and repair kiosk"
    },
    {
        "name": "Ananya Roy",
        "language": "en",
        "location": "Medinipur",
        "mobility_constraint": "Cannot travel far",
        "education_level": "10th Standard",
        "family_occupation": "Agriculture & Farming",
        "current_livelihood": "Farm household assistant",
        "skills": ["Food Processing & Preservation"],
        "interests": ["Food Processing & Preservation"],
        "employment_preference": "self_employment",
        "entry_mode": "facilitator",
        "trade": "Food Processing & Agri-Value Addition Technician",
        "status": "enrolled",
        "nsqf": "NSQF Level 3 (FICSI/Q0102)",
        "programme": "PM-AJAY Free Skill Training",
        "centre": "JSS Medinipur",
        "opportunity": "Local fruit and grain packaging SHG cluster"
    },
    {
        "name": "Vikas Gaikwad",
        "language": "mr",
        "location": "Nagpur",
        "mobility_constraint": "District travel possible",
        "education_level": "10th Standard",
        "family_occupation": "Mechanic Helper",
        "current_livelihood": "Garage daily assistant",
        "skills": ["Two-Wheeler & EV Maintenance"],
        "interests": ["Two-Wheeler & EV Maintenance"],
        "employment_preference": "self_employment",
        "entry_mode": "facilitator",
        "trade": "Two-Wheeler & EV Service Technician",
        "status": "enrolled",
        "nsqf": "NSQF Level 3 (ASC/Q1411)",
        "programme": "PM-AJAY Electric Mobility Track",
        "centre": "District Skill Center Nagpur",
        "opportunity": "Independent Two-Wheeler EV service unit"
    },
    {
        "name": "Manjit Kaur",
        "language": "pa",
        "location": "Amritsar",
        "mobility_constraint": "Cannot travel far",
        "education_level": "10th Standard",
        "family_occupation": "Agriculture & Farming",
        "current_livelihood": "Homemaker",
        "skills": ["Food Processing & Preservation"],
        "interests": ["Food Processing & Preservation"],
        "employment_preference": "self_employment",
        "entry_mode": "call",
        "trade": "Food Processing & Agri-Value Addition Technician",
        "status": "dropped",
        "nsqf": "NSQF Level 3 (FICSI/Q0102)",
        "programme": "PM-AJAY Free Skill Training & Certification",
        "centre": "JSS Amritsar Rural Hub",
        "opportunity": "Self-help group pickle making unit"
    },
    {
        "name": "Anil Maurya",
        "language": "hi",
        "location": "Varanasi",
        "mobility_constraint": "Within village cluster",
        "education_level": "12th Standard",
        "family_occupation": "Small Retail / Kirana",
        "current_livelihood": "Kirana counter helper",
        "skills": ["Digital Services & CSC Operation"],
        "interests": ["Digital Services & CSC Operation"],
        "employment_preference": "self_employment",
        "entry_mode": "app",
        "trade": "Digital Services Operator & CSC Citizen Facilitator",
        "status": "placed",
        "nsqf": "NSQF Level 4 (SSC/Q2212)",
        "programme": "PM-AJAY Rural Digital Track",
        "centre": "NIELIT Center Varanasi",
        "opportunity": "Common Service Center (CSC) kiosk at Block Panchayat"
    },
    {
        "name": "Pradip Ingle",
        "language": "mr",
        "location": "Solapur",
        "mobility_constraint": "Cannot travel far",
        "education_level": "8th Standard",
        "family_occupation": "Agriculture & Farming",
        "current_livelihood": "Farm labour",
        "skills": ["Food Processing & Preservation"],
        "interests": ["Food Processing & Preservation"],
        "employment_preference": "self_employment",
        "entry_mode": "facilitator",
        "trade": "Food Processing & Agri-Value Addition Technician",
        "status": "no_contact",
        "nsqf": "NSQF Level 3 (FICSI/Q0102)",
        "programme": "PM-AJAY Free Skill Training",
        "centre": "JSS Solapur",
        "opportunity": "Village grain milling and spice unit"
    }
]

def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as count FROM beneficiaries")
    row = cursor.fetchone()
    if row and row["count"] > 0:
        conn.close()
        print("Database already has records, skipping seed.")
        return

    now = datetime.utcnow()
    for idx, item in enumerate(SEED_PROFILES):
        b_id = str(uuid.uuid4())
        created_time = (now - timedelta(days=random.randint(2, 45))).isoformat()

        cursor.execute("""
        INSERT INTO beneficiaries (
            id, name, language, location, mobility_constraint, education_level,
            family_occupation, current_livelihood, skills, interests,
            employment_preference, entry_mode, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id,
            item["name"],
            item["language"],
            item["location"],
            item["mobility_constraint"],
            item["education_level"],
            item["family_occupation"],
            item["current_livelihood"],
            json.dumps(item["skills"]),
            json.dumps(item["interests"]),
            item["employment_preference"],
            item["entry_mode"],
            created_time
        ))

        # Skill gap result
        sg_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT INTO skill_gap_results (id, beneficiary_id, recommended_trade, gap_summary, nsqf_alignment)
        VALUES (?, ?, ?, ?, ?)
        """, (
            sg_id,
            b_id,
            item["trade"],
            "Aligned with candidate family background and localized livelihood opportunities under PM-AJAY.",
            item["nsqf"]
        ))

        # Recommendation
        rec_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT INTO recommendations (
            id, beneficiary_id, training_programme, training_centre,
            local_opportunity, roadmap_steps, spoken_summary, generated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec_id,
            b_id,
            item["programme"],
            item["centre"],
            item["opportunity"],
            json.dumps([
                f"Enroll in {item['programme']}",
                f"Hands-on NSQF training at {item['centre']}",
                f"National Skill Council Examination & Certification",
                f"Direct credit or placement linkage: {item['opportunity']}"
            ]),
            f"Recommended {item['trade']} at {item['centre']}.",
            created_time
        ))

        # Follow up
        fu_id = str(uuid.uuid4())
        contact_date = (now - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO follow_ups (id, beneficiary_id, status, last_contact_date)
        VALUES (?, ?, ?, ?)
        """, (fu_id, b_id, item["status"], contact_date))

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic PM-AJAY beneficiary data!")

if __name__ == "__main__":
    seed_database()
