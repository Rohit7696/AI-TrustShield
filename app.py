from flask import Flask, render_template, request
import os

from detectors.audio_detector import detect_audio_real_or_fake
from detectors.video_detector import detect_video_real_or_fake
from detectors.image_detector import detect_image_real_or_fake

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/detect/<dtype>", methods=["GET", "POST"])
def detect(dtype):
    if request.method == "POST":
        file = request.files["file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        if dtype == "audio":
            result, reason = detect_audio_real_or_fake(path)
        elif dtype == "video":
            result, reason = detect_video_real_or_fake(path)
        elif dtype == "image":
            result, reason = detect_image_real_or_fake(path)
        else:
            result, reason = "N/A", "Text detection not implemented"

        return render_template("result.html",
                               dtype=dtype,
                               result=result,
                               reason=reason)

    return render_template("detect.html", dtype=dtype)

if __name__ == "__main__":
    app.run(debug=True)
