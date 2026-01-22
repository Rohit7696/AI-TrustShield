import librosa
import numpy as np

def detect_audio_real_or_fake(audio_path):
    y, sr = librosa.load(audio_path, sr=22050)

    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0]
    rolloff_var = np.var(rolloff)

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_std = np.std(centroid)

    reasons = []

    if rolloff_var > 4_000_000:
        reasons.append("Digital frequency artifacts detected")

    if centroid_std > 1250:
        reasons.append("Unnatural vocal brightness patterns")

    if reasons:
        return "FAKE", ", ".join(reasons)
    else:
        return "REAL", "Natural spectral voice patterns detected"
