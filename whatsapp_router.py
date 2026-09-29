import os
import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import whatsapp_service

logger = logging.getLogger("whatsapp_router")

router = APIRouter(tags=["WhatsApp Integration"])


def validate_twilio_signature(url: str, params: Dict[str, Any], signature: str, auth_token: str) -> bool:
    """
    Validates Twilio X-Twilio-Signature header using HMAC-SHA1.
    Twilio specs:
    1. Take full request URL
    2. Sort POST parameters alphabetically by key
    3. Concatenate key + value to URL (no delimiter)
    4. Compute HMAC-SHA1 with auth_token
    5. Compare base64 encoded digest with header signature
    """
    if not signature or not auth_token:
        return False

    urls_to_try = [url]
    if url.startswith("http://"):
        urls_to_try.append("https://" + url[7:])
    elif url.startswith("https://"):
        urls_to_try.append("http://" + url[8:])

    for u in urls_to_try:
        data_str = u
        for key in sorted(params.keys()):
            data_str += f"{key}{params[key]}"
        mac = hmac.new(auth_token.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha1)
        computed = base64.b64encode(mac.digest()).decode("utf-8")
        if hmac.compare_digest(computed, signature):
            return True
    return False


class WhatsAppSimulateRequest(BaseModel):
    from_number: str = "9810123456"
    body: str = "1"
    media_url: Optional[str] = None
    language: Optional[str] = "en"


@router.post("/webhook/whatsapp")
async def twilio_whatsapp_webhook(
    request: Request,
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    Body: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
):
    """
    Standard Twilio WhatsApp Sandbox Webhook endpoint (sandbox-ready).
    Receives incoming WhatsApp message form fields, validates X-Twilio-Signature,
    routes through Nivara RAG pipeline, and returns TwiML XML Response.
    """
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()

    # Check for simulator mode (header or query param)
    is_simulator = (
        request.headers.get("X-Simulator", "").lower() in ["true", "1"]
        or request.query_params.get("simulator", "").lower() in ["true", "1"]
        or request.query_params.get("is_simulator", "").lower() in ["true", "1"]
    )

    from_number = From or "whatsapp:+919810123456"
    body_text = Body or ""
    media_url = MediaUrl0

    # Also handle JSON if sent programmatically
    if not Body and not From:
        try:
            json_body = await request.json()
            from_number = json_body.get("From") or json_body.get("from_number") or from_number
            body_text = json_body.get("Body") or json_body.get("body") or ""
            media_url = json_body.get("MediaUrl0") or json_body.get("media_url")
            if json_body.get("simulator") or json_body.get("is_simulator"):
                is_simulator = True
        except Exception:
            pass

    # Signature validation when TWILIO_AUTH_TOKEN is set
    if auth_token:
        if is_simulator:
            logger.warning("Twilio signature validation skipped: running in simulator mode")
        else:
            signature = request.headers.get("X-Twilio-Signature", "")
            # Collect POST parameters
            params: Dict[str, Any] = {}
            try:
                form_data = await request.form()
                for k, v in form_data.items():
                    params[k] = str(v)
            except Exception:
                pass

            if not params:
                if From: params["From"] = From
                if To: params["To"] = To
                if Body: params["Body"] = Body
                if MediaUrl0: params["MediaUrl0"] = MediaUrl0

            full_url = str(request.url)
            forwarded_proto = request.headers.get("X-Forwarded-Proto")
            forwarded_host = request.headers.get("X-Forwarded-Host")
            if forwarded_proto and forwarded_host:
                full_url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
                if request.url.query:
                    full_url += f"?{request.url.query}"

            if not validate_twilio_signature(full_url, params, signature, auth_token):
                logger.warning(f"Rejected invalid Twilio request: signature mismatch from {from_number}")
                raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    res = whatsapp_service.handle_whatsapp_message(
        from_number=from_number,
        body=body_text,
        media_url=media_url
    )

    twiml = whatsapp_service.generate_twiml_response(res["reply"])
    return Response(content=twiml, media_type="application/xml")


@router.post("/api/whatsapp/simulate")
def simulate_whatsapp_message(req: WhatsAppSimulateRequest):
    """
    In-app simulation endpoint used by the interactive WhatsApp simulator.
    Works completely offline/without live Twilio credentials.
    """
    res = whatsapp_service.handle_whatsapp_message(
        from_number=req.from_number,
        body=req.body,
        media_url=req.media_url,
        language=req.language or "en"
    )
    return res


@router.get("/api/whatsapp/profile/{phone}")
def get_whatsapp_profile(phone: str):
    """Lookup beneficiary profile associated with phone number."""
    profile = whatsapp_service.get_profile_by_phone(phone)
    return profile


@router.get("/whatsapp")
def serve_whatsapp_simulator():
    """Serves the in-app WhatsApp chat simulator interface."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    sim_path = os.path.join(static_dir, "whatsapp_sim.html")
    if os.path.exists(sim_path):
        return FileResponse(sim_path)
    return {"message": "WhatsApp simulator template not found"}
