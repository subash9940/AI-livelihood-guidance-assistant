"""
Local Vector Store: lexical (TF-IDF) retrieval with translate-then-retrieve; embedding-based retrieval planned for Nivara Delhi Knowledge Base.
Supports local vector indexing using TF-IDF / Subword character n-gram cosine embeddings
with instant chunking and ranking. Zero external network dependencies.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import delhi_data_loader as ddl

INDEX_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "delhi", "vector_index_cache.json")


class LocalVectorStore:
    def __init__(self, region: str = "delhi"):
        self.region = region
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None
        self.is_built = False
        self.build_index()

    def _create_chunks(self) -> List[Dict[str, Any]]:
        """Extracts and chunks all documents from Delhi knowledge base."""
        chunks = []
        
        # 1. Schemes
        schemes = ddl.load_delhi_schemes(self.region)
        for s in schemes:
            # Main scheme overview chunk
            docs = s.get("documents_required", [])
            docs_str = ", ".join(docs) if isinstance(docs, list) else str(docs or "")
            
            how_to = s.get("how_to_apply", "")
            if isinstance(how_to, list):
                apply_str = " -> ".join(how_to)
            else:
                apply_str = str(how_to or "")

            raw_benefits = s.get("benefits", {})
            if isinstance(raw_benefits, list):
                benefit_str = "; ".join(raw_benefits)
            elif isinstance(raw_benefits, dict):
                benefit_str = f"Assistance: {raw_benefits.get('financial_assistance', '')}. Stipend: {raw_benefits.get('stipend', '')}. Loan: {raw_benefits.get('loan_subsidy', '')}. Toolkit: {raw_benefits.get('toolkit_support', '')}. Details: {raw_benefits.get('details', '')}"
            else:
                benefit_str = str(raw_benefits or "")

            elig = s.get("eligibility", {})
            elig_str = f"Age: {elig.get('min_age')}-{elig.get('max_age')}, Income Limit: {elig.get('income_limit')}, Income Rule: {elig.get('income_rule_type', 'hard_cap')}, Priority Below: {elig.get('income_priority_below')}, Categories: {elig.get('category')}, Education: {elig.get('education')}, Residency: {elig.get('residency')}"

            desc = s.get("description") or s.get("notes") or ""
            active_info = f"Active: {s.get('active', True)}. Status note: {s.get('status_note', '')}." if not s.get('active', True) else "Active: True."
            full_text = f"Scheme: {s['name']} ({s['level']} level, {s['department']}). {active_info} Description: {desc}. Eligibility: {elig_str}. Benefits: {benefit_str}. Documents Required: {docs_str}. How to apply: {apply_str}. Official URL: {s['official_url']}. Helpline: {s.get('helpline')}."
            
            chunks.append({
                "chunk_id": f"scheme_{s['id']}_overview",
                "entity_id": s["id"],
                "entity_type": "scheme",
                "title": s["name"],
                "text": full_text,
                "metadata": {
                    "scheme_id": s["id"],
                    "name": s["name"],
                    "level": s["level"],
                    "department": s["department"],
                    "active": s.get("active", True),
                    "status_note": s.get("status_note"),
                    "official_url": s["official_url"],
                    "helpline": s.get("helpline"),
                    "documents_required": docs,
                    "how_to_apply": apply_str,
                    "benefits": raw_benefits,
                    "eligibility": s.get("eligibility", {}),
                    "nearest_offices": s.get("nearest_offices", [])
                }
            })

            # Offices chunk
            for off in s.get("nearest_offices", []):
                off_text = f"Nearest Office for {s['name']}: District {off['district']}, {off['name']}, Address: {off['address']}, Contact: {off['contact']}."
                chunks.append({
                    "chunk_id": f"scheme_{s['id']}_office_{off['district'].replace(' ', '_').lower()}",
                    "entity_id": s["id"],
                    "entity_type": "office",
                    "title": f"{s['name']} - Office in {off['district']}",
                    "text": off_text,
                    "metadata": {
                        "scheme_id": s["id"],
                        "scheme_name": s["name"],
                        "district": off["district"],
                        "address": off["address"],
                        "contact": off["contact"],
                        "official_url": s["official_url"]
                    }
                })

        # 2. NCS Jobs
        jobs = ddl.load_delhi_jobs(self.region)
        for j in jobs:
            skills_str = ", ".join(j.get("required_skills", []))
            dist_str = ", ".join(j.get("delhi_districts_hiring", []))
            j_text = f"Job Role: {j['job_role']}, NSQF Level {j['nsqf_level']}, Sector: {j['sector']}. Average Wage: {j['avg_wage_range']}. Required Skills: {skills_str}. Minimum Education: {j['minimum_education']}. Experience: {j['experience_required']}. Hiring in Delhi Districts: {dist_str}."
            chunks.append({
                "chunk_id": f"job_{j['id']}",
                "entity_id": j["id"],
                "entity_type": "job",
                "title": f"NCS Job: {j['job_role']} (NSQF Level {j['nsqf_level']})",
                "text": j_text,
                "metadata": {
                    "job_id": j["id"],
                    "job_role": j["job_role"],
                    "nsqf_level": j["nsqf_level"],
                    "sector": j["sector"],
                    "wage": j["avg_wage_range"],
                    "districts": j["delhi_districts_hiring"],
                    "skills": j["required_skills"],
                    "education": j["minimum_education"]
                }
            })

        # 3. Training Centres
        centres = ddl.load_delhi_training_centres(self.region)
        for c in centres:
            fac_str = ", ".join(c.get("facilities", []))
            tc_text = f"Training Centre: {c['centre_name']} ({c['type']}). Course: {c['course']}, NSQF Level {c['nsqf_level']}. Duration: {c['duration']}, Fee: {c['fee']}. District: {c['district']}, Address: {c['address']}, Contact: {c['contact']}. Facilities: {fac_str}. Accreditation: {c.get('accreditation', 'Govt Recognized')}."
            chunks.append({
                "chunk_id": f"tc_{c['id']}",
                "entity_id": c["id"],
                "entity_type": "training_centre",
                "title": f"{c['centre_name']} - {c['course']}",
                "text": tc_text,
                "metadata": {
                    "centre_id": c["id"],
                    "centre_name": c["centre_name"],
                    "type": c["type"],
                    "course": c["course"],
                    "nsqf_level": c["nsqf_level"],
                    "district": c["district"],
                    "address": c["address"],
                    "contact": c["contact"],
                    "fee": c["fee"]
                }
            })

        # 4. Policies
        policies = ddl.load_delhi_policies(self.region)
        for p in policies:
            prov_str = " | ".join(p.get("key_provisions_sc", []))
            p_text = f"Policy Document: {p['title']} ({p['authority']}, {p['year']}). Summary: {p['summary']}. Key Provisions for SC: {prov_str}. Official URL: {p['source_url']}."
            chunks.append({
                "chunk_id": f"policy_{p['id']}",
                "entity_id": p["id"],
                "entity_type": "policy",
                "title": p["title"],
                "text": p_text,
                "metadata": {
                    "policy_id": p["id"],
                    "title": p["title"],
                    "authority": p["authority"],
                    "source_url": p["source_url"]
                }
            })

        return chunks

    def build_index(self):
        """Builds TF-IDF subword/word vector index for local retrieval."""
        self.chunks = self._create_chunks()
        corpus = [c["text"] for c in self.chunks]
        
        # Word + character n-grams captures typing variations, Hindi phonetic terms, scheme names
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w+\b",
            lowercase=True
        )
        self.matrix = self.vectorizer.fit_transform(corpus)
        self.is_built = True

    def retrieve(self, query: str, k: int = 5, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant knowledge chunks for the given query.
        Returns ranked list of chunks with similarity score and metadata.
        """
        if not self.is_built or self.vectorizer is None or self.matrix is None:
            self.build_index()

        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        
        # Keyword booster for exact ID or name matches
        query_lower = query.lower()
        stopwords = {"scheme", "delhi", "yojana", "yojna", "level", "office", "want", "documents", "required", "about", "what", "which", "give", "show", "help", "from", "with", "this", "that"}
        query_words = [w for w in re.findall(r"\b\w+\b", query_lower) if len(w) > 3 and w not in stopwords]
        is_office_query = any(w in query_lower for w in ["office", "address", "phone", "contact", "karyalay", "pata", "कार्यालय", "पता"])
        boosted_scores = np.copy(sims)
        for idx, chunk in enumerate(self.chunks):
            # Boost if query contains entity title or id
            title_lower = chunk["title"].lower()
            if any(word in title_lower for word in query_words):
                boosted_scores[idx] += 0.25
            if chunk["entity_id"].lower() in query_lower:
                boosted_scores[idx] += 0.50
            if chunk["entity_type"] == "scheme" and not is_office_query:
                boosted_scores[idx] += 0.15

        # Sort indices descending
        ranked_indices = np.argsort(boosted_scores)[::-1]
        
        results = []
        for idx in ranked_indices:
            score = float(boosted_scores[idx])
            chunk = self.chunks[idx]
            if filter_type and chunk["entity_type"] != filter_type:
                continue
            if score <= 0.01 and len(results) >= 2:
                break
            results.append({
                "chunk_id": chunk["chunk_id"],
                "entity_id": chunk["entity_id"],
                "entity_type": chunk["entity_type"],
                "title": chunk["title"],
                "text": chunk["text"],
                "score": round(score, 4),
                "metadata": chunk["metadata"]
            })
            if len(results) >= k:
                break

        return results


# Global singleton instance
_vector_store: Optional[LocalVectorStore] = None

def get_vector_store(region: str = "delhi") -> LocalVectorStore:
    global _vector_store
    if _vector_store is None or _vector_store.region != region:
        _vector_store = LocalVectorStore(region=region)
    return _vector_store

def retrieve(query: str, k: int = 5, filter_type: Optional[str] = None, region: str = "delhi") -> List[Dict[str, Any]]:
    """Primary RAG retrieval entrypoint with translate-then-retrieve."""
    from rag.query_normalizer import normalize_query
    norm = normalize_query(query)
    store = get_vector_store(region=region)
    return store.retrieve(norm["english"], k=k, filter_type=filter_type)

