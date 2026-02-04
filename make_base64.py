import base64

INPUT_FILE = "sample_voice.mp3"
OUTPUT_FILE = "audio_base64.txt"

with open(INPUT_FILE, "rb") as f:
    encoded = base64.b64encode(f.read()).decode()

with open(OUTPUT_FILE, "w") as f:
    f.write(encoded)

print("✅ Base64 saved to audio_base64.txt")


