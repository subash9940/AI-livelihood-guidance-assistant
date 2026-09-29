"""
Persistent Per-User Memory Store for Nivara AI Assistant.
Maintains:
(a) Structured Profile (consented attributes, skills, education, demographics)
(b) Conversation History & Summaries
(c) Goals and Application-Progress Tracker (target trades, saved schemes, next steps)
Persisted in SQLite database (livelihood.db).
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("memory_store")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "livelihood.db")

# Sensitive profile fields requiring at-rest encryption
SENSITIVE_PROFILE_FIELDS = {
    # Caste Category
    "category", "caste_category", "caste", "social_category",
    # Income Bracket
    "income_bracket", "annual_income", "income", "family_income",
    # Phone
    "phone", "mobile", "contact", "phone_number"
}

_fernet_instance: Optional[Fernet] = None


def get_fernet() -> Fernet:
    """Returns or initializes the Fernet encryption cipher using key from .env."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = os.getenv("FERNET_SECRET_KEY") or os.getenv("FERNET_KEY")
    if not key:
        new_key = Fernet.generate_key().decode("utf-8")
        print(f"[SECURITY WARNING] FERNET_SECRET_KEY not set in .env. Auto-generated new key: {new_key[:8]}... and saving to .env")
        logger.warning("FERNET_SECRET_KEY not set in .env. Auto-generated new key on first run.")
        os.environ["FERNET_SECRET_KEY"] = new_key
        key = new_key
        # Append to .env file if it exists
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        try:
            if os.path.exists(env_path):
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\n# Auto-generated SQLite memory store encryption key\nFERNET_SECRET_KEY={new_key}\n")
        except Exception as e:
            logger.warning(f"Could not persist FERNET_SECRET_KEY to .env: {e}")

    if isinstance(key, str):
        key = key.strip().encode("utf-8")
    _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(val: Any) -> Any:
    """Encrypts a string or primitive value at rest using Fernet."""
    if val is None or val == "":
        return val
    val_str = str(val)
    # Avoid double encryption if already a Fernet token
    if val_str.startswith("gAAAAA") and len(val_str) > 50:
        return val_str
    try:
        f = get_fernet()
        return f.encrypt(val_str.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed for field value: {e}")
        return val_str


PHONE_FIELDS = {"phone", "mobile", "contact", "phone_number"}


def decrypt_value(val: Any) -> Any:
    """Decrypts a Fernet ciphertext token back to plaintext string."""
    if not isinstance(val, str) or not val.startswith("gAAAAA"):
        return val
    try:
        f = get_fernet()
        return f.decrypt(val.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return val
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return val


def encrypt_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a copy of profile with sensitive fields encrypted at rest."""
    if not isinstance(profile, dict):
        return profile
    encrypted = dict(profile)
    for field in SENSITIVE_PROFILE_FIELDS:
        if field in encrypted and encrypted[field] is not None:
            encrypted[field] = encrypt_value(encrypted[field])
    return encrypted


def decrypt_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a copy of profile with sensitive fields decrypted for application use."""
    if not isinstance(profile, dict):
        return profile
    decrypted = dict(profile)
    for field in SENSITIVE_PROFILE_FIELDS:
        if field in decrypted and decrypted[field] is not None:
            dec = decrypt_value(decrypted[field])
            if field in PHONE_FIELDS:
                decrypted[field] = str(dec)
            elif field in ["annual_income", "income"] and isinstance(dec, str) and dec.isdigit():
                decrypted[field] = int(dec)
            else:
                decrypted[field] = dec
    return decrypted


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_tables():
    """Initializes tables for persistent user memory, goals, and applications."""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_memory (
        user_id TEXT PRIMARY KEY,
        profile_json TEXT NOT NULL DEFAULT '{}',
        conversation_summary TEXT DEFAULT '',
        active_goal TEXT DEFAULT '',
        goal_target_trade TEXT DEFAULT '',
        goal_nsqf_level INTEGER DEFAULT 4,
        consent_given BOOLEAN DEFAULT 0,
        consent_timestamp TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_memory(user_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        scheme_id TEXT NOT NULL,
        scheme_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'saved', -- 'saved', 'applied', 'documents_verified', 'enrolled', 'certified'
        current_step INTEGER DEFAULT 1,
        total_steps INTEGER DEFAULT 4,
        notes TEXT DEFAULT '',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, scheme_id),
        FOREIGN KEY (user_id) REFERENCES user_memory(user_id)
    );
    """)

    conn.commit()
    conn.close()


# Ensure tables are initialized at import
init_memory_tables()


class UserMemoryStore:
    @staticmethod
    def get_or_create(user_id: str) -> Dict[str, Any]:
        """Retrieves user memory record or creates a new one."""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_memory WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            now = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO user_memory (user_id, profile_json, conversation_summary, created_at, updated_at)
            VALUES (?, '{}', '', ?, ?)
            """, (user_id, now, now))
            conn.commit()
            cursor.execute("SELECT * FROM user_memory WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

        conn.close()
        return UserMemoryStore.format_user_record(row)

    @staticmethod
    def format_user_record(row) -> Dict[str, Any]:
        if not row:
            return {}
        profile = {}
        try:
            raw_profile = json.loads(row["profile_json"] or "{}")
            profile = decrypt_profile(raw_profile)
        except Exception:
            pass

        return {
            "user_id": row["user_id"],
            "profile": profile,
            "conversation_summary": row["conversation_summary"] or "",
            "active_goal": row["active_goal"] or "Explore PM-AJAY Skilling & Employment",
            "goal_target_trade": row["goal_target_trade"] or "",
            "goal_nsqf_level": row["goal_nsqf_level"] or 4,
            "consent_given": bool(row["consent_given"]),
            "consent_timestamp": row["consent_timestamp"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    @staticmethod
    def update_profile(user_id: str, new_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Merges new profile fields into persistent user profile, encrypting sensitive fields at rest."""
        current = UserMemoryStore.get_or_create(user_id)
        profile = current.get("profile", {})
        profile.update(new_fields)
        
        # Encrypt sensitive fields (caste category, income bracket, phone) before storing at rest in SQLite
        stored_profile = encrypt_profile(profile)
        
        now = datetime.now().isoformat()
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE user_memory
        SET profile_json = ?, updated_at = ?
        WHERE user_id = ?
        """, (json.dumps(stored_profile), now, user_id))
        conn.commit()
        conn.close()
        return profile

    @staticmethod
    def record_consent(user_id: str, consented: bool = True) -> None:
        """Records informed consent for data processing."""
        now = datetime.now().isoformat()
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE user_memory
        SET consent_given = ?, consent_timestamp = ?, updated_at = ?
        WHERE user_id = ?
        """, (1 if consented else 0, now, now, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def add_conversation_turn(user_id: str, role: str, content: str) -> None:
        """Appends a turn to conversation log and updates user record timestamp."""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_conversation_history (user_id, role, content)
        VALUES (?, ?, ?)
        """, (user_id, role, content))
        cursor.execute("UPDATE user_memory SET updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_conversation_history(user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Returns ordered recent conversation messages."""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT role, content, timestamp FROM user_conversation_history
        WHERE user_id = ? ORDER BY id ASC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]

    @staticmethod
    def update_summary(user_id: str, summary_text: str) -> None:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE user_memory SET conversation_summary = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (summary_text, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def set_user_goal(user_id: str, goal: str, target_trade: Optional[str] = None, nsqf_level: Optional[int] = None) -> Dict[str, Any]:
        """Sets user's primary livelihood or skilling goal."""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE user_memory
        SET active_goal = ?, goal_target_trade = COALESCE(?, goal_target_trade),
            goal_nsqf_level = COALESCE(?, goal_nsqf_level), updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """, (goal, target_trade, nsqf_level, user_id))
        conn.commit()
        conn.close()
        return UserMemoryStore.get_or_create(user_id)

    @staticmethod
    def save_scheme_to_plan(user_id: str, scheme_id: str, scheme_name: str) -> Dict[str, Any]:
        """Saves a scheme to user's personalized roadmap/progress tracker."""
        conn = get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO user_applications (user_id, scheme_id, scheme_name, status, current_step, updated_at)
        VALUES (?, ?, ?, 'saved', 1, ?)
        ON CONFLICT(user_id, scheme_id) DO UPDATE SET updated_at = excluded.updated_at
        """, (user_id, scheme_id, scheme_name, now))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "scheme_id": scheme_id, "status": "saved"}

    @staticmethod
    def update_application_progress(user_id: str, scheme_id: str, status: str, current_step: Optional[int] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Updates progress of a tracked scheme application."""
        conn = get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
        UPDATE user_applications
        SET status = ?, current_step = COALESCE(?, current_step),
            notes = COALESCE(?, notes), updated_at = ?
        WHERE user_id = ? AND scheme_id = ?
        """, (status, current_step, notes, now, user_id, scheme_id))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "scheme_id": scheme_id, "status": status, "current_step": current_step}

    @staticmethod
    def get_applications(user_id: str) -> List[Dict[str, Any]]:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM user_applications WHERE user_id = ? ORDER BY updated_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "scheme_id": r["scheme_id"],
                "scheme_name": r["scheme_name"],
                "status": r["status"],
                "current_step": r["current_step"],
                "total_steps": r["total_steps"],
                "notes": r["notes"] or "",
                "updated_at": r["updated_at"]
            }
            for r in rows
        ]

    @staticmethod
    def get_full_memory_bundle(user_id: str) -> Dict[str, Any]:
        """Returns complete memory snapshot for RAG context and Nivara Saathi assistant."""
        user = UserMemoryStore.get_or_create(user_id)
        history = UserMemoryStore.get_conversation_history(user_id, limit=10)
        apps = UserMemoryStore.get_applications(user_id)
        
        return {
            "user_id": user_id,
            "profile": user["profile"],
            "active_goal": user["active_goal"],
            "goal_target_trade": user["goal_target_trade"],
            "goal_nsqf_level": user["goal_nsqf_level"],
            "conversation_summary": user["conversation_summary"],
            "consent_given": user["consent_given"],
            "applications": apps,
            "history": history
        }

    @staticmethod
    def delete_user_data(user_id: str) -> bool:
        """Completely purges all data for a user (Consent / Right to be forgotten)."""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_conversation_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_applications WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
