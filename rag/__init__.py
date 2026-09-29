"""
Nivara RAG & Memory Layer Package.
"""
from rag.vector_store import retrieve, get_vector_store
from rag.eligibility_engine import check_eligibility, evaluate_all_schemes_for_profile
from rag.memory_store import UserMemoryStore, get_fernet, encrypt_profile, decrypt_profile, encrypt_value, decrypt_value
from rag.answer_pipeline import ask_rag
from rag.query_normalizer import normalize_query, get_localized_scheme_name

__all__ = [
    "retrieve",
    "get_vector_store",
    "check_eligibility",
    "evaluate_all_schemes_for_profile",
    "UserMemoryStore",
    "get_fernet",
    "encrypt_profile",
    "decrypt_profile",
    "encrypt_value",
    "decrypt_value",
    "ask_rag",
    "normalize_query",
    "get_localized_scheme_name",
]

