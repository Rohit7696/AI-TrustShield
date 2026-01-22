import json, subprocess, shutil

def extract_metadata(video_path):
    if not shutil.which("exiftool"):
        raise FileNotFoundError("Exiftool not found")

    proc = subprocess.run(
        ["exiftool", "-j", video_path],
        capture_output=True,
        text=True
    )
    return json.loads(proc.stdout)[0] if proc.returncode == 0 else {}


def detect_video_real_or_fake(video_path):
    meta = extract_metadata(video_path)

    reasons = []

    # 1. Encoder / Software check
    encoder = str(
        meta.get("Encoder") or
        meta.get("Software") or
        meta.get("CompressorName") or ""
    ).lower()

    if any(x in encoder for x in ["ffmpeg", "lavf", "libav", "handbrake", "opencv"]):
        reasons.append("AI-generated encoder signature detected")

    # 2. Audio sample rate check
    audio_rate = meta.get("AudioSampleRate", 0)
    if audio_rate and audio_rate <= 16000:
        reasons.append("Low-fidelity audio typical of AI generation")

    # 3. Frame rate check
    fps = meta.get("VideoFrameRate", 0)
    if fps in [24, 25, 30]:
        reasons.append("Fixed frame rate common in AI videos")

    # 4. Hardware metadata presence (strong real signal)
    has_hardware = any(meta.get(k) for k in ["Make", "Model", "LensModel"])
    if has_hardware:
        return "REAL", "Physical camera hardware metadata detected"

    # Final decision
    if reasons:
        return "FAKE", reasons[0]
    else:
        return "REAL", "No AI-generation metadata patterns detected"
