# Nivara — AI Livelihood Guidance Assistant (PS 26097)
## Project Progress & Architecture Summary

**Last Updated:** September 27, 2026  
**Status:** All Core Milestones & Test Suites Passing (12/12)

---

### 1. Executive Overview

Nivara is an AI-powered, multilingual, voice-first livelihood guidance assistant engineered for PM-AJAY (Pradhan Mantri Anusuchit Jaati Abhyuday Yojana) beneficiaries. It bridges informal rural/semi-urban skills with formal National Skills Qualifications Framework (NSQF) qualification packs, regional government schemes, and localized employment opportunities.

---

### 2. Implemented Features & Core Capabilities

#### A. Voice-First Multilingual Conversational Intake
- **Languages Supported:** Hindi, Marathi, Punjabi, Tamil, and Indian English.
- **Web Speech ASR & SpeechSynthesis:** Native browser speech recognition with real-time transcript streaming, audio feedback, and fallback scenario chips.
- **IVR Feature Phone Simulator:** Touch-tone DTMF keypad simulation for non-smartphone / feature phone users.

#### B. Conversational Profiler & Intelligence Cascading
- **Broad Skill Ingestion:** Recognizes technical, vocational, traditional/family-occupation, and soft/interpersonal skills without arbitrary gatekeeping.
- **Natural Name & Signal Extraction:** Captures beneficiary identity, education level, mobility constraints, and wage vs. self-employment preferences.
- **Completeness Gating & Graceful Fallbacks:** Validates that at least one concrete skill or interest is present before recommendation. Returns structured clarification queries (`missing_piece: region | skill | clarity of intent`) instead of hallucinating or guessing.

#### C. NSQF-Aligned Recommendation Engine
- **NSQF Qualification Packs (QP):** Complete national occupational standards with Qualification Pack codes (e.g., `FIC/Q0102`, `CON/Q0602`, `SGJ/Q0101`), NSQF certification levels (Levels 3–4), and Sector Skill Council (SSC) endorsements.
- **Explainable Skill Readiness Scoring:** Dual numeric readiness score (0–100) and distinct qualitative classification tiers:
  - `Direct Pathway Ready` (Score >= 70)
  - `Skill Bridge Track` (Score 40–69)
  - `Exploratory Track — Review Options` (Score < 40)
- **Targeted Diagnostic Gap Breakdown:** Highlights specific competency deficits alongside recommended learning institutions (Jan Shikshan Sansthan - JSS, PMKK, RSETI).

#### D. Regional Schemes & Data Provenance Transparency
- **Regional Schemes Directory:** Curated schemes for Delhi, Maharashtra, Tamil Nadu, Karnataka, and Uttar Pradesh (e.g., Mahila Samridhi Yojana, Stand-Up Mitra, CM Rural Livelihood Grants).
- **Data Provenance Badging:** Every regional scheme and local opportunity entry carries explicit provenance tags (`Community-compiled — verify with local office` / `Illustrative data — pending live registry integration`) to clearly distinguish live verified data from compiled illustrative references.

#### E. Localized Employment & Enterprise Opportunities
- **Nearby Cluster Openings:** Realistic local wage employment and micro-enterprise options mapped by state and trade with distance indicators and estimated wage/grant brackets.
- **Linkage Channels:** Connects beneficiaries directly to District Employment Exchanges and PMKK Placement Cells.

#### F. GIA Coordination & District Facilitator Dashboard
- **Aggregate Demand vs. Training Capacity Gap Analysis:** Tracks completed recommendations against regional training infrastructure to identify deficit and surplus sectors.
- **Dedicated Web Dashboard (`/dashboard`):** Interactive Chart.js analytics, KPI cards, beneficiary queue tracking, and CSV report export for district coordinators and scheme administrators.
- **Demo Beneficiary Selector:** 1-click profiles (Textiles/Delhi, Agri/UP, Auto/Tamil Nadu, Solar/Maharashtra) running through the exact full production pipeline.

---

### 3. Architecture & File Structure

```
livelihood-assistant/
├── api.py                    # FastAPI service & endpoint routing
├── profiler.py               # Conversational extraction, gating, & session profiling
├── nsqf_rules.py             # NSQF qualification rules, readiness scoring & gap analysis
├── region_schemes.py         # Regional state schemes & canonical lookup
├── local_opportunities.py    # Localized employment & enterprise opportunities dataset
├── training_capacity.py      # State-wise training center capacity dataset & gap logic
├── database.py               # SQLite session storage, demand tracking & queue queries
├── test_api.py               # Comprehensive pytest test suite (12 suites)
├── progress.md               # Current development & feature status log
└── static/
    ├── index.html            # Main mobile-responsive beneficiary web interface
    ├── dashboard.html        # GIA coordination & district admin analytics dashboard
    ├── app.js                # Frontend controller (Voice ASR/TTS, state, rendering)
    └── styles.css            # Tailored styling & design system tokens
```

---

### 4. Verification & Testing

All 12 automated test suites in `test_api.py` are passing:
- `test_full_pipeline`: Session start, voice input, recommendation cascade.
- `test_regional_schemes_static_data_and_lookup`: State normalization & scheme schemas.
- `test_session_recommendation_with_state`: State-aware regional matching.
- `test_recommendation_incomplete_profile_returns_409`: Gating on empty profiles.
- `test_followup_nonexistent_beneficiary_returns_404`: Error boundary verification.
- `test_readiness_score_calculation`: Formula & tier label checks.
- `test_demo_beneficiary_pipeline_profiles`: Verification of all 4 demo profiles.
- `test_nsqf_qualification_pack_details`: QP codes, SSC names, and NSQF levels.
- `test_regional_demand_capacity_gap`: Capacity vs. demand delta calculations.
- `test_broad_skill_profile_validation_and_tiers`: Soft skill & vocational validation.
- `test_graceful_fallbacks_and_completeness_gating`: Missing piece handling.
- `test_local_opportunities_and_dashboard`: Local opportunities and `/dashboard` serving.

---

### 5. Next Steps & Future Enhancements

1. **Live Registry Integration:** Connect with National Career Service (NCS) API and Skill India Digital Hub for real-time training batch seat availability.
2. **Offline Mode & PWA:** Service worker caching for low-connectivity rural deployment.
3. **Automated WhatsApp / SMS Bot Dispatch:** Direct integration with SMS gateways for dispatching printable roadmaps.
