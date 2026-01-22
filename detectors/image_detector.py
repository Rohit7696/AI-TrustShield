import subprocess
import cv2
import numpy as np

# ---------------- CONFIG ----------------
MOBILE_SOFTWARE_KEYWORDS = ["xiaomi", "vivo", "samsung", "oppo", "apple", "redmi", "realme"]

FAKE_SIGS = [
    ("credit", "made with google ai"),
    ("actions software agent", ""),
    ("pixels per unit x", "1000"),
    ("color space", "uncalibrated"),
]

# ---------------- METADATA ----------------
def get_metadata(image_path):
    proc = subprocess.run(
        f'exiftool "{image_path}"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return {
        line.split(": ", 1)[0].strip(): line.split(": ", 1)[1].strip()
        for line in proc.stdout.split("\n") if ": " in line
    }

# ---------------- HUFFMAN ----------------
def get_huffman_tables(image_path):
    tables = []
    with open(image_path, 'rb') as f:
        data = f.read()
    i = 0
    while i < len(data) - 1:
        if data[i] == 0xFF and data[i+1] == 0xC4:
            length = int.from_bytes(data[i+2:i+4], 'big') - 2
            tables.append(length)
            i += length + 2
        else:
            i += 1
    return tables

# ---------------- REAL METADATA (4/5 RULE) ----------------
def is_real(metadata):
    score = 0
    try:
        if float(metadata.get("Megapixels", "0")) >= 5:
            score += 1
    except:
        pass

    if metadata.get("Make"):
        score += 1

    if metadata.get("Camera Model Name"):
        score += 1

    if metadata.get("Shutter Speed") or metadata.get("Shutter Speed Value"):
        score += 1

    software = (metadata.get("Software") or "").lower()
    if software == "" or "windows" in software or any(v in software for v in MOBILE_SOFTWARE_KEYWORDS):
        score += 1

    return score >= 4

# ---------------- FAKE METADATA ----------------
def has_fake_signature(metadata):
    for k, v in metadata.items():
        kl = k.lower()
        vl = str(v).lower()

        if "http" in vl:
            return True

        for fk, fv in FAKE_SIGS:
            if kl == fk and (fv == "" or fv in vl):
                return True

        if kl == "comment":
            return True

    software = metadata.get("Software", "").lower()
    if software and "windows" not in software:
        if not any(v in software for v in MOBILE_SOFTWARE_KEYWORDS):
            return True

    return False

# ---------------- PIXEL FORENSICS ----------------
def dct_smoothness(path):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    g = cv2.resize(g, (256, 256)).astype(np.float32)
    return float(np.std(cv2.dct(g)[128:, 128:]))

def sensor_noise(path):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    g = cv2.resize(g, (256, 256))
    return float(np.std(cv2.subtract(g, cv2.GaussianBlur(g, (5, 5), 0))))

def rgb_corr(path):
    img = cv2.imread(path)
    img = cv2.resize(img, (256, 256)).astype(np.float32)
    r, g, b = cv2.split(img)
    return (
        np.corrcoef(r.flatten(), g.flatten())[0,1] +
        np.corrcoef(r.flatten(), b.flatten())[0,1] +
        np.corrcoef(g.flatten(), b.flatten())[0,1]
    ) / 3.0

# ---------------- FINAL DECISION ----------------
def detect_image_real_or_fake(image_path):
    metadata = get_metadata(image_path)
    huffman_tables = get_huffman_tables(image_path)

    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    # 1️⃣ REAL FIRST (same as your code)
    if is_real(metadata):
        return "REAL", "Camera metadata passed 4/5 authenticity checks"

    # 2️⃣ METADATA + STRUCTURE FAKE CHECKS
    meta_count = len(metadata)
    h_count = len(huffman_tables)

    condA = (meta_count > 25 and has_fake_signature(metadata))
    condB = (h_count <= 4 and h >= 256 and w >= 256)
    condC = (h_count == 8 and huffman_tables[:2] == [29, 179])

    if condA or condB or condC:
        return "FAKE", "Strong AI metadata or JPEG structure signature detected"

    # 3️⃣ PIXEL-LEVEL AI CHECK
    if h >= 256 and w >= 256:
        dct = dct_smoothness(image_path)
        noise = sensor_noise(image_path)
        corr = rgb_corr(image_path)

        if dct < 2.0 and noise < 3.0 and corr < 0.85:
            return "FAKE", "AI-like smoothness and color correlation detected"

    # 4️⃣ FALLBACK (your Manipulated → REAL collapse)
    return "REAL", "No decisive AI manipulation indicators found"
