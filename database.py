"""
Database models and storage for Nivara — AI Livelihood Guidance Assistant.
Implements the exact Section 4 data model with SQLite persistence.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "livelihood.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Beneficiary Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beneficiaries (
        id TEXT PRIMARY KEY,
        name TEXT,
        language TEXT DEFAULT 'en',
        location TEXT DEFAULT 'Pune',
        state TEXT,
        mobility_constraint TEXT,
        education_level TEXT,
        family_occupation TEXT,
        current_livelihood TEXT,
        skills TEXT DEFAULT '[]',
        interests TEXT DEFAULT '[]',
        employment_preference TEXT DEFAULT 'undecided',
        entry_mode TEXT DEFAULT 'app',
        facilitator_id TEXT,
        created_at TEXT
    )
    """)

    # Ensure state column exists if table existed previously
    cursor.execute("PRAGMA table_info(beneficiaries)")
    b_cols = [c["name"] for c in cursor.fetchall()]
    if "state" not in b_cols:
        cursor.execute("ALTER TABLE beneficiaries ADD COLUMN state TEXT")

    # SkillGapResult Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skill_gap_results (
        id TEXT PRIMARY KEY,
        beneficiary_id TEXT,
        recommended_trade TEXT,
        gap_summary TEXT,
        nsqf_alignment TEXT,
        FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
    )
    """)

    # Recommendation Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id TEXT PRIMARY KEY,
        beneficiary_id TEXT,
        training_programme TEXT,
        training_centre TEXT,
        local_opportunity TEXT,
        roadmap_steps TEXT DEFAULT '[]',
        spoken_summary TEXT,
        generated_at TEXT,
        FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
    )
    """)

    # FollowUp Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS follow_ups (
        id TEXT PRIMARY KEY,
        beneficiary_id TEXT,
        status TEXT DEFAULT 'no_contact',
        last_contact_date TEXT,
        FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
    )
    """)

    # Sessions Table (to maintain conversational state before completion)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        entry_mode TEXT DEFAULT 'app',
        language TEXT DEFAULT 'en',
        beneficiary_id TEXT,
        conversation_history TEXT DEFAULT '[]',
        profile_data TEXT DEFAULT '{}',
        profile_complete INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Regional Recommendation Demand Table (Tracks demand signals per state and trade)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_demand (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        beneficiary_id TEXT,
        state TEXT,
        trade_key TEXT,
        trade_name TEXT,
        created_at TEXT
    )
    """)

    # Populate baseline demand records from existing beneficiaries if table is fresh
    cursor.execute("SELECT COUNT(*) as cnt FROM recommendation_demand")
    demand_count = cursor.fetchone()["cnt"]
    if demand_count == 0:
        cursor.execute("""
        SELECT b.id as beneficiary_id, b.location, b.state, sg.recommended_trade
        FROM beneficiaries b
        LEFT JOIN skill_gap_results sg ON b.id = sg.beneficiary_id
        """)
        existing_rows = cursor.fetchall()
        import region_schemes
        import nsqf_rules
        for row in existing_rows:
            raw_loc = row["state"] or row["location"] or "Maharashtra"
            c_state = region_schemes.get_canonical_state(raw_loc) or "Maharashtra"
            rec_trade = row["recommended_trade"] or ""
            t_key = "food_processing"
            for k, info in nsqf_rules.TRADES_CATALOG.items():
                t_cand = info.get("trade_name", "")
                if t_cand.lower() in rec_trade.lower() or rec_trade.lower() in t_cand.lower():
                    t_key = k
                    break
            t_name = nsqf_rules.TRADES_CATALOG[t_key].get("trade_name", t_key)
            now_iso = datetime.utcnow().isoformat()
            cursor.execute("""
            INSERT INTO recommendation_demand (id, session_id, beneficiary_id, state, trade_key, trade_name, created_at)
            VALUES (?, NULL, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), row["beneficiary_id"], c_state, t_key, t_name, now_iso))

    conn.commit()
    conn.close()

def save_beneficiary(data: Dict[str, Any]) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    b_id = data.get("id") or str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    state_val = data.get("state")
    if not state_val and data.get("location"):
        import region_schemes
        state_val = region_schemes.get_canonical_state(data.get("location"))

    cursor.execute("""
    INSERT OR REPLACE INTO beneficiaries (
        id, name, language, location, state, mobility_constraint, education_level,
        family_occupation, current_livelihood, skills, interests,
        employment_preference, entry_mode, facilitator_id, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        b_id,
        data.get("name"),
        data.get("language", "hi"),
        data.get("location", "Pune"),
        state_val,
        data.get("mobility_constraint"),
        data.get("education_level", "10th Standard"),
        data.get("family_occupation", "Agriculture"),
        data.get("current_livelihood", "Unemployed / Daily wage"),
        json.dumps(data.get("skills", [])),
        json.dumps(data.get("interests", [])),
        data.get("employment_preference", "undecided"),
        data.get("entry_mode", "app"),
        data.get("facilitator_id"),
        data.get("created_at", now)
    ))
    conn.commit()
    conn.close()
    return b_id

def save_skill_gap(beneficiary_id: str, recommended_trade: str, gap_summary: str, nsqf_alignment: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    sg_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO skill_gap_results (id, beneficiary_id, recommended_trade, gap_summary, nsqf_alignment)
    VALUES (?, ?, ?, ?, ?)
    """, (sg_id, beneficiary_id, recommended_trade, gap_summary, nsqf_alignment))
    conn.commit()
    conn.close()
    return sg_id

def save_recommendation(
    beneficiary_id: str,
    training_programme: str,
    training_centre: str,
    local_opportunity: str,
    roadmap_steps: List[str],
    spoken_summary: str
) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    rec_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO recommendations (
        id, beneficiary_id, training_programme, training_centre,
        local_opportunity, roadmap_steps, spoken_summary, generated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rec_id,
        beneficiary_id,
        training_programme,
        training_centre,
        local_opportunity,
        json.dumps(roadmap_steps),
        spoken_summary,
        now
    ))
    conn.commit()
    conn.close()
    return rec_id

def update_followup(beneficiary_id: str, status: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM beneficiaries WHERE id = ?", (beneficiary_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Beneficiary not found")

    cursor.execute("SELECT id FROM follow_ups WHERE beneficiary_id = ?", (beneficiary_id,))
    row = cursor.fetchone()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    if row:
        f_id = row["id"]
        cursor.execute("""
        UPDATE follow_ups SET status = ?, last_contact_date = ? WHERE id = ?
        """, (status, today, f_id))
    else:
        f_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT INTO follow_ups (id, beneficiary_id, status, last_contact_date)
        VALUES (?, ?, ?, ?)
        """, (f_id, beneficiary_id, status, today))

    conn.commit()
    conn.close()
    return f_id

def create_session(entry_mode: str = "app", language: str = "hi") -> str:
    conn = get_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO sessions (id, entry_mode, language, conversation_history, profile_data, profile_complete, created_at, updated_at)
    VALUES (?, ?, ?, '[]', '{}', 0, ?, ?)
    """, (session_id, entry_mode, language, now, now))
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "entry_mode": row["entry_mode"],
        "language": row["language"],
        "beneficiary_id": row["beneficiary_id"],
        "conversation_history": json.loads(row["conversation_history"] or "[]"),
        "profile_data": json.loads(row["profile_data"] or "{}"),
        "profile_complete": bool(row["profile_complete"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

def update_session(session_id: str, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    now = datetime.utcnow().isoformat()
    kwargs["updated_at"] = now

    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        if isinstance(v, (dict, list)):
            values.append(json.dumps(v))
        elif isinstance(v, bool):
            values.append(1 if v else 0)
        else:
            values.append(v)

    values.append(session_id)
    query = f"UPDATE sessions SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def record_recommendation_demand(
    state: str,
    trade_key: str,
    trade_name: str,
    beneficiary_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Records a completed recommendation demand signal by (state, trade).
    """
    conn = get_connection()
    cursor = conn.cursor()
    record_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO recommendation_demand (id, session_id, beneficiary_id, state, trade_key, trade_name, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (record_id, session_id, beneficiary_id, state, trade_key, trade_name, now))
    conn.commit()
    conn.close()
    return record_id

def get_demand_counts_by_state(state: Optional[str] = None) -> Dict[str, int]:
    """
    Returns aggregated demand count per trade_key for a given state,
    or across all states if state is None or 'all'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if state and state.lower() != "all":
        cursor.execute("""
        SELECT trade_key, COUNT(*) as cnt
        FROM recommendation_demand
        WHERE LOWER(state) = LOWER(?)
        GROUP BY trade_key
        """, (state,))
    else:
        cursor.execute("""
        SELECT trade_key, COUNT(*) as cnt
        FROM recommendation_demand
        GROUP BY trade_key
        """)
    rows = cursor.fetchall()
    conn.close()
    return {r["trade_key"]: r["cnt"] for r in rows}

