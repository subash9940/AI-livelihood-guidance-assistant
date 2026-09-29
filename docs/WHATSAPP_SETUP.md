# Nivara — WhatsApp Business & Twilio Integration Setup

This guide documents the WhatsApp integration for Nivara under PM-AJAY (MoSJE), enabling SC beneficiaries and low-literacy users to interact with the assistant via WhatsApp.

---

## 1. Zero-Credential In-App Simulator (Demo Ready)

For live demonstrations and local testing without requiring active Twilio accounts, Nivara provides an authentic **in-app WhatsApp chat simulator**:

1. Start the server:
   ```bash
   python -m uvicorn api:app --port 8000
   ```
2. Open your browser at:
   ```
   http://127.0.0.1:8000/whatsapp
   ```
3. Use the simulator:
   - **Beneficiary Switcher**: Switch phone numbers (`+91 98101 23456` for Rohan Kumar or `+91 98765 43210` for Pooja Rani) to test profile lookup.
   - **Quick Tap Menu**: Tap `1` for Schemes, `2` for Centres, `3` for Eligibility, `4` for Reminders, `0` for Main Menu.
   - **Voice Note Input**: Tap the green mic button to dictate questions or send simulated voice notes.

---

## 2. Connecting to Live Twilio WhatsApp Sandbox

To route live WhatsApp messages from actual smartphones into Nivara:

### Step 1: Twilio Console Setup
1. Create a free account at [Twilio Console](https://console.twilio.com).
2. Navigate to **Messaging > Try it out > Send a WhatsApp message**.
3. Activate the WhatsApp Sandbox by sending the join code (e.g., `join <sandbox-keyword>`) to `+1 415 523 8886`.

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and configure your credentials:
```env
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Step 3: Expose Local Webhook (ngrok or Cloud Run)
In development, expose port 8000 using ngrok:
```bash
ngrok http 8000
```
Copy your forwarding HTTPS URL (e.g. `https://xyz.ngrok-free.app`).

### Step 4: Set Twilio Webhook URL
1. In Twilio Sandbox Settings, set **WHEN A MESSAGE COMES IN**:
   ```
   https://xyz.ngrok-free.app/webhook/whatsapp
   ```
2. Set HTTP method to `HTTP POST`.
3. Save configuration.

---

## 3. Webhook Features & Flow

| Feature | How It Works |
|---|---|
| **Profile Lookup** | Looks up beneficiary records by phone number (`From` field). Personalized greetings and context. |
| **Numbered Shortcuts** | Low-literacy users can reply with single digits (`1`, `2`, `3`, `4`, `0`). |
| **Grounded RAG Pipeline** | Natural language queries are grounded strictly in the Delhi Knowledge Base with citations. |
| **Deterministic Eligibility** | Evaluates age, caste, and income limits using official JSON rules. |
| **TwiML XML** | Responds with standard `<Response><Message>...</Message></Response>`. |
