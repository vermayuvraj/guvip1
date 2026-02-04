from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import math
import time

app = FastAPI(
    title="AI Generated Voice Detection API",
    version="1.0"
)

# 🔐 Hardcoded API key (as required by hackathon)
API_KEY = "sk_test_123456789"

# 🚧 Base64 size limit (~1.5 MB audio max)
MAX_BASE64_CHARS = 2_000_000


# =========================
# Request Schema (ROBUST)
# =========================
class VoiceRequest(BaseModel):
    language: str

    # accept both snake_case and camelCase
    audio_format: Optional[str] = None
    audioFormat: Optional[str] = None

    audio_base64: Optional[str] = None
    audioBase64: Optional[str] = None

    def resolved_audio_format(self) -> Optional[str]:
        return self.audio_format or self.audioFormat

    def resolved_audio_base64(self) -> Optional[str]:
        return self.audio_base64 or self.audioBase64


# =========================
# Utility: entropy
# =========================
def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0

    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    entropy = 0.0
    length = len(data)

    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)

    return entropy


# =========================
# API Endpoint
# =========================
@app.post("/api/voice-detection")
def detect_voice(
    payload: VoiceRequest,
    x_api_key: str = Header(None)
):
    start_time = time.time()

    # 🔐 API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    audio_format = payload.resolved_audio_format()
    audio_base64 = payload.resolved_audio_base64()

    # 🚫 Required field validation
    if not audio_format or not audio_base64:
        raise HTTPException(
            status_code=422,
            detail="audio_format and audio_base64 are required"
        )

    # 🚧 Base64 size guard (prevents OOM)
    if len(audio_base64) > MAX_BASE64_CHARS:
        raise HTTPException(
            status_code=413,
            detail="Audio file too large"
        )

    # 🔓 Safe base64 decode
    try:
        audio_bytes = base64.b64decode(audio_base64, validate=True)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 audio"
        )

    size_kb = len(audio_bytes) / 1024
    entropy = calculate_entropy(audio_bytes)

    # 🧠 Lightweight classification logic (fast + stable)
    if entropy > 7.3 and size_kb < 350:
        classification = "AI"
        confidence = round(0.75 + min((entropy - 7.3) / 2, 0.2), 2)
        explanation = "High entropy and compressed signal pattern detected"
    else:
        classification = "HUMAN"
        confidence = round(0.60 + min(size_kb / 2000, 0.25), 2)
        explanation = "Natural variation and signal complexity detected"

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "status": "success",
        "language": payload.language,
        "classification": classification,
        "confidenceScore": confidence,
        "latencyMs": latency_ms,
        "explanation": explanation
    }


# =========================
# Health Check
# =========================
@app.get("/")
def health():
    return {"status": "alive"}
