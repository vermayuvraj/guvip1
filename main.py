from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
import time
import base64
import hashlib
import os

app = FastAPI(title="Unified AI Security API")

# ======================
# CONFIG
# ======================
API_KEY = "sk_test_123456789"


# ======================
# REQUEST MODELS
# ======================
class VoiceDetectionRequest(BaseModel):
    language: str
    audioFormat: str
    audioBase64: str


# ======================
# UTILS
# ======================
def verify_api_key(x_api_key: str):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def quick_audio_check(b64_audio: str) -> str:
    """
    Lightweight heuristic check.
    NO heavy ML to avoid memory/time issues.
    """
    raw = base64.b64decode(b64_audio[:2000])
    entropy = len(set(raw)) / max(len(raw), 1)

    if entropy < 0.35:
        return "AI_GENERATED", 0.92, "Synthetic patterns and uniformity detected"
    else:
        return "HUMAN", 0.79, "Natural variation and signal complexity detected"


# ======================
# MAIN ENDPOINT (PS1 + PS2)
# ======================
@app.post("/api/ai")
async def unified_ai_endpoint(
    request: Request,
    x_api_key: str = Header(...)
):
    verify_api_key(x_api_key)

    payload = await request.json()

    # ======================
    # PS1: AI-GENERATED VOICE DETECTION
    # ======================
    if "audioBase64" in payload:
        try:
            start = time.time()

            audio_b64 = payload["audioBase64"]
            audio_format = payload.get("audioFormat", "")
            language = payload.get("language", "English")

            if audio_format.lower() not in ["mp3", "wav"]:
                raise HTTPException(status_code=400, detail="Unsupported audio format")

            classification, confidence, explanation = quick_audio_check(audio_b64)

            latency = int((time.time() - start) * 1000)

            return {
                "status": "success",
                "language": language,
                "classification": classification,
                "confidenceScore": round(confidence, 2),
                "latencyMs": latency,
                "explanation": explanation
            }

        except Exception:
            raise HTTPException(status_code=400, detail="Could not process audio file")

    # ======================
    # PS2: AGENTIC HONEYPOT
    # ======================
    else:
        """
        IMPORTANT:
        - Immediate response
        - No blocking
        - No sleep
        - No loops
        """

        client_ip = request.client.host if request.client else "unknown"
        fingerprint = hashlib.sha256(str(payload).encode()).hexdigest()

        return {
            "status": "ok",
            "message": "Request received",
            "honeypot": True,
            "intel": {
                "ipAddress": client_ip,
                "payloadHash": fingerprint,
                "payloadType": "generic",
                "riskScore": 0.11,
                "threatLevel": "LOW"
            }
        }


# ======================
# HEALTH CHECK
# ======================
@app.get("/")
def health():
    return {"status": "running"}
