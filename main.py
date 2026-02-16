import base64
import hashlib
import re
import time
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

# =====================================================
# Configuration
# =====================================================

API_KEY = "sk_test_123456789"

app = FastAPI(title="LionKing AI Security API")

# In-memory session store for Honeypot
sessions: Dict[str, dict] = {}

# =====================================================
# Utility Functions
# =====================================================

def validate_api_key(x_api_key: str):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def calculate_latency(start_time: float) -> int:
    return int((time.time() - start_time) * 1000)


# =====================================================
# ================= PS1: Voice Detection =============
# =====================================================

class VoiceRequest(BaseModel):
    language: str
    audio_format: str
    audio_base64: str


def extract_audio_features(decoded_bytes: bytes) -> Dict:
    size = len(decoded_bytes)
    entropy = len(set(decoded_bytes)) / 256
    return {"size": size, "entropy": entropy}


def classify_voice(features: Dict) -> Dict:
    size = features["size"]
    entropy = features["entropy"]

    score = 0

    # Heuristic improvements for better human detection
    if entropy < 0.2:
        score += 0.5
    if size < 20000:
        score += 0.3
    if entropy < 0.1:
        score += 0.2

    confidence = min(round(score, 2), 0.95)

    if score >= 0.5:
        classification = "AI_GENERATED"
        explanation = "Synthetic patterns and uniformity detected"
    else:
        classification = "HUMAN"
        explanation = "Natural variation and signal complexity detected"

    return {
        "classification": classification,
        "confidenceScore": confidence,
        "explanation": explanation
    }


@app.post("/api/voice-detection")
def voice_detection(payload: VoiceRequest, x_api_key: str = Header(...)):
    validate_api_key(x_api_key)
    start_time = time.time()

    try:
        decoded = base64.b64decode(payload.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio")

    features = extract_audio_features(decoded)
    result = classify_voice(features)

    latency = calculate_latency(start_time)

    return {
        "status": "success",
        "language": payload.language,
        "classification": result["classification"],
        "confidenceScore": result["confidenceScore"],
        "latencyMs": latency,
        "explanation": result["explanation"]
    }


# =====================================================
# ================= PS2: Agentic Honeypot =============
# =====================================================

class HoneyRequest(BaseModel):
    sessionId: Optional[str] = None
    message: Optional[str] = ""
    conversationHistory: Optional[List[Dict]] = []


def extract_intelligence(text: str) -> Dict:
    phone_regex = r"\+?\d[\d\- ]{8,}"
    upi_regex = r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+"
    url_regex = r"https?://[^\s]+"
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    bank_regex = r"\b\d{9,18}\b"

    return {
        "phoneNumbers": re.findall(phone_regex, text),
        "upiIds": re.findall(upi_regex, text),
        "urls": re.findall(url_regex, text),
        "emails": re.findall(email_regex, text),
        "bankAccounts": re.findall(bank_regex, text)
    }


def detect_scam(text: str) -> bool:
    scam_keywords = [
        "urgent", "otp", "verify", "blocked",
        "reward", "click", "transfer",
        "bank", "upi", "compromised"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in scam_keywords)


@app.post("/api/ai")
def honeypot_api(payload: HoneyRequest, request: Request, x_api_key: str = Header(...)):
    validate_api_key(x_api_key)

    start_time = time.time()

    session_id = payload.sessionId or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = {
            "startTime": time.time(),
            "messages": [],
            "intel": {},
            "scamDetected": False
        }

    session = sessions[session_id]

    message = payload.message or ""
    session["messages"].append(message)

    # Extract intelligence
    intel = extract_intelligence(message)
    for key in intel:
        session["intel"].setdefault(key, [])
        session["intel"][key].extend(intel[key])

    # Scam detection
    if detect_scam(message):
        session["scamDetected"] = True

    reply = "Thank you for the information. Could you clarify further?"

    total_messages = len(session["messages"])
    duration = int(time.time() - session["startTime"])

    latency = calculate_latency(start_time)

    return {
        "status": "success",
        "sessionId": session_id,
        "reply": reply,
        "scamDetected": session["scamDetected"],
        "totalMessagesExchanged": total_messages,
        "engagementDurationSeconds": duration,
        "extractedIntelligence": session["intel"],
        "agentNotes": "Conversation monitored for fraud patterns.",
        "latencyMs": latency
    }


@app.get("/")
def root():
    return {"status": "running"}
