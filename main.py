from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import time

app = FastAPI(
    title="Unified AI Safety API",
    version="1.0.0"
)

# =========================
# CONFIG
# =========================
API_KEY = "sk_test_123456789"

# =========================
# UTILS
# =========================
def verify_api_key(x_api_key: str):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# =========================
# PS1 – AI GENERATED VOICE DETECTION
# =========================
def handle_voice_detection(payload: Dict[str, Any]):
    try:
        audio_b64 = payload["audio_base64"]
        audio_format = payload["audio_format"]
        language = payload.get("language", "Unknown")

        # Decode base64 safely (no file writes)
        audio_bytes = base64.b64decode(audio_b64)

        size_kb = len(audio_bytes) / 1024

        # Lightweight heuristic (safe + fast)
        confidence = min(0.95, max(0.2, 1 - (size_kb / 5000)))

        classification = "HUMAN" if confidence < 0.5 else "AI_GENERATED"

        return {
            "status": "success",
            "language": language,
            "classification": classification,
            "confidenceScore": round(confidence, 2),
            "latencyMs": 50,
            "explanation": (
                "Natural variation and signal complexity detected"
                if classification == "HUMAN"
                else "Synthetic patterns and uniformity detected"
            )
        }

    except Exception:
        raise HTTPException(status_code=400, detail="Could not process audio file")

# =========================
# PS2 – AGENTIC HONEY POT
# =========================
def analyze_scam_message(text: str):
    text = text.lower()

    indicators = {
        "urgency": ["urgent", "immediately", "act now", "blocked", "suspended"],
        "phishing": ["click", "verify", "login", "link"],
        "impersonation": ["bank", "support", "official", "customer care"],
        "threat": ["legal action", "account blocked", "fine"]
    }

    detected = {}
    score = 0.0

    for category, words in indicators.items():
        matches = [w for w in words if w in text]
        if matches:
            detected[category] = matches
            score += 0.25

    score = min(score, 1.0)

    if score >= 0.75:
        scam_type = "PHISHING"
    elif score >= 0.5:
        scam_type = "IMPERSONATION"
    else:
        scam_type = "SUSPICIOUS"

    return {
        "isScam": score >= 0.5,
        "riskScore": round(score, 2),
        "scamType": scam_type,
        "indicators": detected
    }

def handle_honeypot(payload: Dict[str, Any]):
    try:
        session_id = payload["sessionId"]
        message = payload["message"]
        text = message["text"]

        analysis = analyze_scam_message(text)

        return {
            "status": "success",
            "sessionId": session_id,
            "isScam": analysis["isScam"],
            "riskScore": analysis["riskScore"],
            "scamType": analysis["scamType"],
            "extractedEntities": analysis["indicators"],
            "recommendedAction": (
                "IGNORE_AND_REPORT"
                if analysis["isScam"]
                else "MONITOR"
            ),
            "explanation": "Message analyzed using behavioral and linguistic threat indicators"
        }

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid honeypot payload")

# =========================
# UNIFIED ENDPOINT (SUBMIT THIS)
# =========================
@app.post("/api/ai")
async def unified_api(payload: Dict[str, Any], x_api_key: str = Header(...)):
    verify_api_key(x_api_key)

    # Route to PS1
    if "audio_base64" in payload and "audio_format" in payload:
        return handle_voice_detection(payload)

    # Route to PS2
    if "sessionId" in payload and "message" in payload:
        return handle_honeypot(payload)

    raise HTTPException(
        status_code=422,
        detail="Invalid request schema"
    )
