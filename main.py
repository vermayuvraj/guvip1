from fastapi import FastAPI, Header, HTTPException
import base64
import numpy as np
import io
import librosa
import soundfile as sf

# -------------------- APP SETUP --------------------
app = FastAPI(title="AI Generated Voice Detection API")

API_KEY = "sk_test_123456789"
SUPPORTED_LANGUAGES = {"English", "Hindi", "Tamil", "Telugu", "Malayalam"}

# -------------------- ACOUSTIC FEATURES --------------------
def extract_acoustic_features(y, sr):
    pitch = librosa.yin(y, fmin=50, fmax=300)
    pitch = pitch[~np.isnan(pitch)]
    pitch_var = np.var(pitch) if len(pitch) > 0 else 0

    rms = librosa.feature.rms(y=y)[0]
    energy_var = np.var(rms)

    smoothness = np.mean(np.abs(np.diff(y)))

    return pitch_var, energy_var, smoothness


def acoustic_score(pitch_var, energy_var, smoothness):
    return min(1.0, 1 / (pitch_var + energy_var + smoothness + 1e-6))

# -------------------- SPECTRAL FEATURES --------------------
def extract_spectral_features(y, sr):
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_entropy = np.mean(np.std(mfcc, axis=1))

    flatness = np.mean(librosa.feature.spectral_flatness(y=y))

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_var = np.var(centroid)

    return mfcc_entropy, flatness, centroid_var


def spectral_score(mfcc_entropy, flatness, centroid_var):
    return min(1.0, 1 / (mfcc_entropy + flatness + centroid_var + 1e-6))

# -------------------- TEMPORAL FEATURES --------------------
def extract_temporal_features(y):
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    zcr_var = np.var(zcr)

    silence_ratio = np.mean(np.abs(y) < 0.005)
    frame_diff = np.mean(np.abs(np.diff(y)))

    return zcr_var, silence_ratio, frame_diff


def temporal_score(zcr_var, silence_ratio, frame_diff):
    return min(1.0, 1 / (zcr_var + silence_ratio + frame_diff + 1e-6))

# -------------------- API ENDPOINT --------------------
@app.post("/api/voice-detection")
def voice_detection(payload: dict, x_api_key: str = Header(None)):

    # API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Validate request
    required_fields = {"language", "audioFormat", "audioBase64"}
    if not required_fields.issubset(payload):
        raise HTTPException(status_code=400, detail="Missing required fields")

    language = payload["language"]
    audio_format = payload["audioFormat"]

    # Normalize Base64 (IMPORTANT)
    audio_base64 = payload["audioBase64"]
    audio_base64 = audio_base64.replace("\n", "").replace("\r", "").strip()

    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")

    if audio_format.lower() != "mp3":
        raise HTTPException(status_code=400, detail="Only mp3 format is supported")

    # Decode Base64
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 audio")

    # Robust audio loading (FIXED)
    try:
        audio_buffer = io.BytesIO(audio_bytes)
        y, sr = sf.read(audio_buffer)

        # Convert stereo to mono
        if y.ndim > 1:
            y = np.mean(y, axis=1)

    except Exception:
        raise HTTPException(status_code=400, detail="Could not process audio file")

    if len(y) < sr:
        raise HTTPException(status_code=400, detail="Audio too short")

    # Feature extraction
    pitch_var, energy_var, smoothness = extract_acoustic_features(y, sr)
    acoustic = acoustic_score(pitch_var, energy_var, smoothness)

    mfcc_entropy, flatness, centroid_var = extract_spectral_features(y, sr)
    spectral = spectral_score(mfcc_entropy, flatness, centroid_var)

    zcr_var, silence_ratio, frame_diff = extract_temporal_features(y)
    temporal = temporal_score(zcr_var, silence_ratio, frame_diff)

    # Final fusion
    final_score = (
        0.4 * acoustic +
        0.35 * spectral +
        0.25 * temporal
    )
    final_score = min(final_score, 1.0)

    classification = "AI_GENERATED" if final_score > 0.55 else "HUMAN"

    # Explanation
    reasons = []
    if acoustic > 0.6:
        reasons.append("high pitch and energy consistency")
    if spectral > 0.6:
        reasons.append("low spectral diversity")
    if temporal > 0.6:
        reasons.append("overly smooth temporal transitions")

    explanation = (
        "Synthetic speech indicators detected: " + ", ".join(reasons)
        if reasons else
        "Natural human speech variations detected"
    )

    return {
        "status": "success",
        "language": language,
        "classification": classification,
        "confidenceScore": round(float(final_score), 2),
        "explanation": explanation
    }
