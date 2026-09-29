# Nivara Demo Script — 3-Minute Live Presentation

**Target Time:** 3 Minutes  
**Audience:** MoSJE / SIH Evaluators & Stakeholders  
**Focus:** PM-AJAY GIA Component (Delhi Region Skilling & Livelihood Mapping)

---

## Pre-Flight Check (0:00)
1. Ensure the server is running: `python api.py` (running on `http://127.0.0.1:8000`).
2. Open browser at `http://127.0.0.1:8000`.
3. Check audio/speaker volume is turned up to hear multilingual TTS.

---

## ⏱️ Step 1: Voice Query & Intake (0:00 – 0:35)
*Goal: Demonstrate working voice-first beneficiary intake for an SC candidate.*

1. **On Screen 1 (Voice Assistant):**
   - Click **"Sunita Verma (Delhi • Tailoring)"** demo quick-scenario card (or tap the big orange mic button and speak):
     > *"I am from Delhi, finished 8th standard, family does tailoring. I know basic machine stitching and want to start my own tailoring unit."*
2. **Observe:**
   - Real-time transcription fills the live speech box.
   - Profile signals update automatically:
     - Education: `8th Standard`
     - Family Occupation: `Tailoring / Weaving`
     - Mobility: `Cannot travel far`
     - State: `Delhi`
   - Spoken AI confirmation announces: *"Generating your customized PM-AJAY NSQF livelihood roadmap."*

---

## ⏱️ Step 2: Pathway & Conversational Follow-Up (0:35 – 1:05)
*Goal: Show NSQF qualification pack alignment, readiness tier, and grounded follow-up.*

1. **Auto-navigation to "Pathways & Skills" view:**
   - Highlights: **Self-Employed Tailor (NSQF Level 3, AMH/Q1947)** under AMHSSC.
   - Skill Readiness Score: `60/100 (Skill Bridge Track)`.
   - 4-step milestone roadmap: Enrolment, JSS training, NSQF certification, and PM-AJAY capital subsidy.
2. **Interactive Conversational Panel (Phase 3):**
   - Scroll down to the **"Ask Follow-Up Question"** panel.
   - Click the suggested chip: **`"Am I eligible?"`** (or `"Documents needed"`).
3. **Observe:**
   - Deterministic eligibility engine checks age, income, caste, and Delhi residency.
   - Reply shows:
     - ✅ **Eligible** under PM-AJAY GIA Component & DSFDC Loan.
     - Inline scheme card appears with an **"Apply Steps"** dropdown and **"Save to my plan"** button.
     - Click **"Save to my plan"** — toast confirms scheme saved to beneficiary profile.

---

## ⏱️ Step 3: Nivara Saathi Personal Assistant (1:05 – 1:40)
*Goal: Showcase Siri-like personal assistant, proactive steps, and data consent.*

1. **Open Saathi:**
   - Click the floating **"Saathi"** badge at bottom-right corner.
   - Fullscreen Siri-like glass modal opens with soundwave visualizer.
2. **Onboarding & Consent:**
   - Shows active consented profile: *Sunita Verma, Age 28, Delhi, Stated Goal: Certified Tailor (NSQF 3)*.
   - Point out the **"View / Edit / Delete My Data"** (GDPR / DPDP Act compliant Right-to-be-Forgotten).
3. **Proactive Cards:**
   - **Daily Next Best Step:** *"Visit Jan Shikshan Sansthan East Delhi (Mayur Vihar) for batch verification."*
   - **Stated Goal Progress Tracker:** 40% achieved toward NSQF Level 3 certification.
   - **Deadline Reminders:** Post-Matric document verification deadline.
4. **Voice Interaction:**
   - Click the big glowing mic button and ask: *"Where is the nearest training centre in East Delhi?"*
   - Saathi answers aloud via TTS with verified JSS address, phone number, and official link.
   - Close modal.

---

## ⏱️ Step 4: WhatsApp Simulator (1:40 – 2:10)
*Goal: Demonstrate omnichannel delivery for low-literacy users without requiring Twilio credentials.*

1. **Open WhatsApp Simulator:**
   - Navigate to `http://127.0.0.1:8000/whatsapp` (or click "WhatsApp Sim" in header).
2. **Interactive Chat:**
   - Notice the authentic WhatsApp interface with active phone profile: `+91 98101 23456 (Sunita Verma, Delhi)`.
   - Click quick reply chip **`1`** (Schemes) or type `1`.
   - Bot instantly replies with structured numbered menu of Delhi SC schemes with emoji formatting.
   - Click quick reply chip **`3`** (Check Eligibility).
   - Bot runs deterministic eligibility engine and confirms eligibility with document checklist.
   - Click **"Simulate Voice Note"** button: demonstrates audio note transcription and processing.

---

## ⏱️ Step 5: 10+ Language IVR Demo (2:10 – 2:35)
*Goal: Feature phone zero-data accessibility across 10+ Indian languages with DTMF tones.*

1. **Switch to "IVR Line" Tab:**
   - View the retro feature phone (AJAY-PHONE) on the left and Live Transcript on the right.
2. **Make Call:**
   - Click the green **Call** button.
   - Listen to realistic phone ringing and analog line static via Web Audio API.
   - Screen displays: *"● CALL CONNECTED"* with running call timer (`00:01`, `00:02`).
   - Spoken greeting plays: *"Welcome to Nivara PM-AJAY Toll-Free Helpline. For Hindi press 1, English 2, Punjabi 3..."*
3. **Keypad DTMF Interaction:**
   - Press **`1`** on the phone keypad.
   - Authentic DTMF dual-tone (`697 Hz + 1209 Hz`) sounds.
   - Screen updates: *"LANG: HI"*.
   - Prompt speaks Hindi main menu options.
   - Press **`1`** (Schemes):
     - RAG backend retrieves Delhi PM-AJAY schemes.
     - Spoken explanation plays.
     - Right panel updates live transcript and generates a **Simulated SMS Slip** dispatched to the feature phone!
   - Press **`*`** to go back.
   - Click red **End Call** button.

---

## ⏱️ Step 6: GIA Coordination Dashboard (2:35 – 3:00)
*Goal: Show government officer monitoring across all 11 Delhi districts.*

1. **Open Dashboard:**
   - Click **"GIA Dashboard"** in the top navigation bar (or visit `/dashboard`).
2. **Highlight Key Deliverables:**
   - **Unified Theme:** Uses identical design system, fonts (`Plus Jakarta Sans`), colors, and Dark/Light toggle.
   - **Clear Labelling:** Prominent banner: *"DEMO / SAMPLE DATA — MoSJE PM-AJAY GIA Component (Delhi Region)"*.
   - **4 KPI Bento Cards:** Beneficiaries Mapped (1,184), Active Enrolments (748), Verified Placements (488), Grant Utilization (₹6.85 Cr, 84.1%).
   - **Enrolments by NSQF Level:** Interactive Chart.js bar chart showing NSQF Levels 3, 4, 5, 6.
   - **Scheme Uptake:** Chart showing distribution across PM-AJAY, DSFDC, Stand-Up India, PMKVY, Post-Matric, DSEU.
   - **Capacity vs Demand Gap:** Demonstrates where training seat deficits exist (e.g. Shahdara Solar PV deficit).
   - **11-District Coverage Table:** Click **"Shahdara"** or **"North East Delhi"** to filter the entire dashboard in real-time.
   - **Pending Applications Queue:** Click **"Review"** on `APP-DL-2026-081` (Rajesh Kumar), select *"Mark Documents as Verified"*, and click *"Confirm Action"*. Toast notification confirms live administrative record update!

---

## Wrap-Up (3:00)
> *"Nivara bridges the digital divide for SC beneficiaries under PM-AJAY GIA—delivering deterministic, hallucination-free guidance from smartphones to basic feature phones, while giving welfare officers real-time district skilling visibility across Delhi."*
