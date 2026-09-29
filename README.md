# Nivara — AI Livelihood Guidance Assistant (SIH PS 26097)
**Government of India · Ministry of Social Justice & Empowerment (MoSJE)**

An AI-powered, multilingual, **voice-first** assistant for Scheduled Caste (SC) beneficiaries under the **PM-AJAY (Pradhan Mantri Anusuchit Jaati Abhyuday Yojana)** scheme. Replaces friction-heavy text intake forms with a spoken conversation that gathers candidate background, conducts NSQF-aligned skill-gap analysis, and generates tailored 4-step livelihood roadmaps.

---

## 1. Architecture: Three Access Modes, One Shared Pipeline

| Mode | Who it's for | Entry UX |
|---|---|---|
| `app` | Smartphone users | Dominant glowing mic button on first screen. No menus or forms. Quick language picker. |
| `call` | Feature/button-phone users | Toll-free **1800-11-PMAJAY** (1800-11-762529) IVR hotline with keypad simulation. |
| `facilitator` | No-phone / low-literacy users | **"Start for someone else"** 1-tap handoff button. Zero friction, no login or facilitator ID capture required. |

All three access doors query the same backend pipeline and tag records with `entry_mode`.

---

## 2. NSQF Domain Rules & Recommendations

Replacing healthcare triage with official National Skills Qualifications Framework (NSQF Levels 1-5) and PM-AJAY components:
- **Food Processing & Agri-Value Addition** (NSQF Level 3 - FICSI): Tailored for agricultural backgrounds and restricted mobility candidates.
- **Self-Employed Tailor & Apparel Specialist** (NSQF Level 3 - AMHSSC): Cluster or village-based garment making with sewing toolkits.
- **Solar PV Installer — Suryamitra** (NSQF Level 4 - SCGJ): Technical trades aligned with PM Surya Ghar Muft Bijli Yojana.
- **Two-Wheeler & EV Service Technician** (NSQF Level 3 - ASDC): Vehicle repair & electric battery maintenance.
- **Digital Services Operator & CSC Citizen Facilitator** (NSQF Level 4 - IT-ITeS): Common Service Centre kiosks & DBT scheme facilitation.
- **General Duty Assistant — Healthcare** (NSQF Level 4 - HSSC): District hospital & clinic wage employment.

---

## 3. 4-Step Livelihood Roadmap Output

1. **Stage 1 (Skill Foundation)**: Free PM-AJAY sponsored vocational course with ₹1,500/month stipend and tool kit vouchers.
2. **Stage 2 (Accredited Training Centre)**: Hands-on practical training at District Jan Shikshan Sansthan (JSS), ITI, or PMKK Hubs.
3. **Stage 3 (National Certification)**: Practical assessment & QR-verifiable NSQF qualification certificate.
4. **Stage 4 (Local Livelihood & Credit)**: Mudra Shishu grant/loan (up to ₹50,000) for micro-enterprise or direct placement with local clusters.

---

## 4. API Endpoints (Section 5 Spec)

- `POST /session/start` — Initializes session with `{ entry_mode, language }`
- `POST /session/{id}/voice-input` — Accepts spoken transcript/audio, extracts schema fields, returns next prompt & profile completion status
- `GET /session/{id}/recommendation` — Runs NSQF skill gap matching and returns 4-step roadmap + spoken audio summary
- `GET /dashboard/summary?district=` — District officer analytics: enrolments, placements, dropouts, skill demand breakdown
- `POST /followup/{beneficiary_id}` — Updates retention status (`enrolled`, `placed`, `dropped`, `no_contact`)

---

## 5. Running Locally

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```
Open your browser at `http://127.0.0.1:8000`.

---

## 6. Voice, Retrieval & Webhook Configuration

- **Voice Input:** browser Web Speech API (Chrome recommended, internet required); Indic accuracy varies; Bhashini/Whisper planned.
- **Knowledge Retrieval:** lexical (TF-IDF) retrieval with translate-then-retrieve; embedding-based retrieval planned.
- **WhatsApp Webhook:** sandbox-ready (configured for Twilio WhatsApp sandbox with HMAC signature verification; production WhatsApp Business API planned).

### Environment Variables
- `MOCK_SPEECH` (default `true`): When set to `true`, the assistant uses keyless local/offline speech synthesis (Edge-TTS) and simulated ASR transcripts for zero-friction local development without requiring government credentials. Set to `false` when connecting to live MeitY Bhashini endpoints.
- `BHASHINI_USER_ID`: MeitY ULCA / Dhruva User ID.
- `BHASHINI_API_KEY`: MeitY ULCA / Dhruva API Key (`ulcaApiKey`).

### TTS Generation Hierarchy
1. **Live Bhashini ULCA TTS**: Active when `MOCK_SPEECH=false` and `BHASHINI_USER_ID` & `BHASHINI_API_KEY` are set in `.env`.
2. **Keyless Neural TTS (`edge-tts`)**: Default server-side engine when Bhashini credentials are not provided. Uses natural Microsoft neural voices for Indian languages (`hi-IN-SwaraNeural`, `mr-IN-AarohiNeural`, `ta-IN-PallaviNeural`, `en-IN-NeerjaNeural`, `pa-IN` fallback) with sentence-by-sentence audio chunking.
3. **Browser Web Speech API (`SpeechSynthesis`)**: Client-side fallback if server audio is blocked or unavailable, ensuring voice output functions even without internet access.

---

## 7. Demo Script Walkthrough (Section 10)

1. **Step 1 (Cold Open)**: Open `http://127.0.0.1:8000` with no login. Tap the dominant mic button or click the demo chip: *"I finished 10th, my family does farming, I want something food-related, I can't travel far"*.
2. **Step 2 (Instant Roadmap)**: System extracts profile signals (10th pass, farming family, food processing, restricted mobility) and renders the 4-step NSQF Level 3 Food Processing roadmap with spoken Indic audio.
3. **Step 3 (Facilitator Mode)**: Click *"Start for someone else (Facilitator Mode)"*. A blue badge confirms facilitator intake mode; run an intake for another beneficiary with zero friction.
4. **Step 4 (Low-Connectivity Call Line)**: Navigate to *"IVR Call Line"* tab. View the toll-free number and use the interactive feature phone simulator to dial digits (1 for Hindi, 2 for Marathi, 3 for Punjabi).
5. **Step 5 (Admin Dashboard)**: Navigate to *"District Dashboard"* tab. View district officer analytics, filter by Pune/Solapur/Amritsar, inspect the skill-demand chart, and update a candidate's follow-up status.
