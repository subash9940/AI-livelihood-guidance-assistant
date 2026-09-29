# Delhi SC Livelihood & Skilling Knowledge Base — Review Checklist

> **Notice for Official Reviewers:**  
> All records in `data/delhi/schemes.json` are currently marked with `verification_status="unverified"`, `last_verified=null`, and `verified_by=null`.  
> A human reviewer from MoSJE, DSFDC, or Delhi Department of Social Welfare must cross-verify each scheme against current official gazette notifications and department records before updating `verification_status` to `"verified"`.

---

## Human Reviewer Checklist

| # | Scheme Name | Scheme ID | Income Limit | Age Limit | Helpline | Official URL | Office Address | Verified? (Y/N) | Reviewer Notes / Signoff |
|---|-------------|-----------|--------------|-----------|----------|--------------|----------------|-----------------|--------------------------|
| 1 | PM-AJAY (GIA Component) | `delhi-pmajay-gia` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 2 | DSFDC Term Loan for Self-Employment | `delhi-dsfdc-term-loan` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 3 | Dilli Swarojgar Yojna (DSFDC Micro-Credit) | `delhi-dilli-swarojgar-yojna` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 4 | Post-Matric Scholarship Scheme for SC Students | `delhi-post-matric-sc` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 5 | NSFDC Employment-Linked Skill Training (ELST) | `delhi-nsfdc-elst` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 6 | Stand-Up India Scheme for SC Entrepreneurs | `delhi-standup-india` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 7 | Pradhan Mantri Kaushal Vikas Yojana 4.0 | `delhi-pmkvy-4` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 8 | Prime Minister's Employment Generation Programme (PMEGP) | `delhi-pmegp` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 9 | DSEU Short-Term Certifications | `delhi-dseu-skill-programs` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 10 | Mukhya Mantri Vidyarthi Pratibha Yojna | `delhi-mukhya-mantri-vidyarthi-pratibha` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 11 | Delhi Khadi Kaushal Vikas & Artisan Toolkit Scheme | `delhi-dkvib-swarojgar` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 12 | PM Vishwakarma Scheme (Delhi Clusters) | `delhi-pm-vishwakarma` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 13 | Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY) | `delhi-ddugky` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 14 | Dr. B.R. Ambedkar State Award for SC/ST/OBC Students | `delhi-dr-ambedkar-state-award` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 15 | PM Surya Ghar: Muft Bijli Yojana (Suryamitra) | `delhi-pm-surya-ghar` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 16 | Delhi Healthcare Skills Mission: GDA & Nursing | `delhi-sc-nursing-gda` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 17 | Delhi ITI Craftsmen Training Scheme for SC | `delhi-iti-electrician-sc` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| 18 | Delhi SC Women SHG Livelihood Grant | `delhi-sc-women-empowerment` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |

---

## Review Procedure & Instructions

1. **Income & Age Verification:** Verify that the income ceiling (e.g. ₹2,50,000/year for PM-AJAY and Post-Matric) and age brackets (18–45 years for adult skilling) match current department notifications.
2. **Helpline Verification:** Dial each telephone number to confirm it connects to an active officer, helpdesk, or IVR system.
3. **URL Live Check:** Open each portal link in a browser to confirm active SSL certificates and relevant forms.
4. **Office Physical Location:** Confirm that the SDM / District Social Welfare Office or training centre address and pin code are accurate.
5. **Marking as Verified:** Once all items are checked, update `data/delhi/schemes.json`:
   - `verification_status`: `"verified"`
   - `last_verified`: `<YYYY-MM-DD>` (ISO date format)
   - `verified_by`: `<Officer Name & Designation>`
   - `notes`: Specific verification notes or circular number.
