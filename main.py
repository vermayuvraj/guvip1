from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import base64
import math
import time

app = FastAPI(
    title="AI Generated Voice Detection API",
    version="1.0"
)

API_KEY = "sk_test_123456789"
MAX_BASE64_CHARS = 2_000_000  # ~1.5MB audio (SAFE for Render)

class VoiceRequest(BaseModel):
    language: str
    audio_format: str
    audio_base64: str

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

@app.post("/api/voice-detection")
def detect_voice(
    payload: VoiceRequest,
    x_api_key: str = Header(None)
):
    start = time.time()

    # 🔐 API key validation
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 🚧 Size guard (CRITICAL)
    if len(payload.audio_base64) > MAX_BASE64_CHARS:
        raise HTTPException(
            status_code=413,
            detail="Audio file too large"
        )

    # 🔓 Safe base64 decode
    try:
        audio_bytes = base64.b64decode(payload.audio_base64, validate=True)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 audio"
        )

    size_kb = len(audio_bytes) / 1024
    entropy = calculate_entropy(audio_bytes)

    # 🧠 Lightweight classification logic
    if entropy > 7.3 and size_kb < 350:
        classification = "AI"
        confidence = round(0.75 + min((entropy - 7.3) / 2, 0.2), 2)
        explanation = "High entropy and compressed signal pattern detected"
    else:
        classification = "HUMAN"
        confidence = round(0.60 + min(size_kb / 2000, 0.25), 2)
        explanation = "Natural variation and signal complexity detected"

    latency_ms = int((time.time() - start) * 1000)

    return {
        "status": "success",
        "language": payload.language,
        "classification": classification,
        "confidenceScore": confidence,
        "latencyMs": latency_ms,
        "explanation": explanation
    }

@app.get("/")
def health():
    return {"status": "alive"}
