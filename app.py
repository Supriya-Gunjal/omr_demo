import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# ✅ Corrected import (because gemini_client.py is inside helpers/)
from helpers.gemini_client import extract_answers_from_omr
from utils.omr_scoring import compute_score


app = Flask(__name__)
app.secret_key = "supersecret"  # change in production

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if files are uploaded
        if "answer_key_omr" not in request.files or "omr_image" not in request.files:
            flash("Both OMR sheets are required", "error")
            return redirect(url_for("index"))

        key_file = request.files["answer_key_omr"]
        student_file = request.files["omr_image"]
        num_questions = int(request.form["num_questions"])

        if key_file.filename == "" or student_file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("index"))

        # Save files in upload folder
        key_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(key_file.filename))
        student_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(student_file.filename))

        key_file.save(key_path)
        student_file.save(student_path)

        try:
            # Extract answers using Gemini
            key_answers = extract_answers_from_omr(key_path, num_questions)
            student_answers = extract_answers_from_omr(student_path, num_questions)

            # Compute results
            summary, breakdown = compute_score(student_answers, key_answers, num_questions)

            # ✅ Correct template name (you only have result.html, not results.html)
            return render_template("result.html", summary=summary, breakdown=breakdown)

        except Exception as e:
            flash(f"Error processing OMR: {str(e)}", "error")
            return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
