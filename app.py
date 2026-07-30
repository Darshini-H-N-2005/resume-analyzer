import os
import re
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_from_directory, flash
)
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2

# ReportLab (Clean PDF)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors


# ==============================
# ENV + GEMINI
# ==============================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

genai.configure(api_key=GEMINI_API_KEY)


# ==============================
# FLASK
# ==============================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
GENERATED_DIR = os.path.join(DATA_DIR, "generated")

os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# ==============================
# HELPERS
# ==============================
def call_gemini(prompt):
    model = genai.GenerativeModel("gemini-2.5-flash")
    return model.generate_content(prompt).text.strip()


# ==============================
# CLEAN PROFESSIONAL PDF (NO OVERFLOW)
# ==============================
def build_clean_pdf(resume_text, output_path):
    styles = getSampleStyleSheet()

    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 14
    normal.alignment = TA_LEFT

    heading = styles["Heading2"]
    heading.fontName = "Helvetica-Bold"
    heading.fontSize = 12
    heading.textColor = colors.black
    heading.spaceAfter = 6
    heading.spaceBefore = 12

    name_style = styles["Heading1"]
    name_style.fontName = "Helvetica-Bold"
    name_style.fontSize = 18
    name_style.spaceAfter = 12

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []

    lines = resume_text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 6))
            continue

        if i == 0:
            elements.append(Paragraph(line, name_style))
            continue

        if line.lower() in [
            "summary:",
            "skills:",
            "experience:",
            "projects:",
            "education:",
            "achievements:"
        ]:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(line.upper(), heading))
            continue

        safe_line = (
            line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        elements.append(Paragraph(safe_line, normal))

    doc.build(elements)


# ==============================
# AUTH
# ==============================
def current_user():
    return session.get("user_email")


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ==============================
# ROUTES
# ==============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("login"))

        session["user_email"] = email
        session["is_admin"] = (email.lower() == "admin@admin.com")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")


# ==============================
# ✅ REAL ATS ANALYSIS (BULLETPROOF)
# ==============================
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    resume_file = request.files.get("resume")
    role = request.form.get("role", "").strip() or "General"

    if not resume_file:
        flash("Please upload a resume file.", "error")
        return redirect(url_for("dashboard"))

    reader = PyPDF2.PdfReader(resume_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        flash("Could not read resume content.", "error")
        return redirect(url_for("dashboard"))

    prompt = f"""
You are an ATS resume analyzer.

Analyze this resume for the role: {role}

Return ONLY valid JSON. No markdown. No explanation.

{{
  "ats_score": 0-100,
  "matched_skills": ["..."],
  "missing_skills": ["..."],
  "summary": "...",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendations": ["..."]
}}

Resume:
{text}
"""

    raw = call_gemini(prompt)

    data = None
    try:
        data = json.loads(raw)
    except:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                data = None

    if not data:
        data = {
            "ats_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "AI failed to return structured output.",
            "strengths": [],
            "weaknesses": [],
            "recommendations": ["Try uploading a clearer PDF."]
        }

    return render_template(
        "result.html",
        analysis=data,
        role=role
    )


# ==============================
# ✅ AI RESUME BUILDER + CLEAN PDF
# ==============================
@app.route("/build", methods=["GET", "POST"])
@login_required
def build_resume():
    pdf_filename = None
    resume_text = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        summary = request.form.get("summary", "").strip()
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "").strip()
        projects = request.form.get("projects", "").strip()
        skills = request.form.get("skills", "").strip()
        achievements = request.form.get("achievements", "").strip()

        if not name or not email or not summary:
            flash("Name, Email and Summary are required.", "error")
            return redirect(url_for("build_resume"))

        prompt = f"""
You are a professional resume writer.

Rewrite this into a clean ATS-friendly resume.
NO markdown. NO emojis. NO stars.
Use hyphen (-) bullet points only.
Do NOT add fake data.

Format exactly:

{name}
Email: {email} | Phone: {phone} | Location: {location}

Summary:
...

Skills:
- ...

Experience:
- ...

Projects:
- ...

Education:
- ...

Achievements:
- ...

User Data:

Summary:
{summary}

Skills:
{skills}

Experience:
{experience}

Projects:
{projects}

Education:
{education}

Achievements:
{achievements}
"""

        resume_text = call_gemini(prompt)

        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
        pdf_filename = f"{safe_name}_resume.pdf"
        pdf_path = os.path.join(GENERATED_DIR, pdf_filename)

        build_clean_pdf(resume_text, pdf_path)

        if not os.path.exists(pdf_path):
            flash("PDF generation failed.", "error")
            pdf_filename = None

    return render_template(
        "build_resume.html",
        resume_md=resume_text,
        pdf_filename=pdf_filename
    )


# ==============================
# DOWNLOAD
# ==============================
@app.route("/download/<path:filename>")
@login_required
def download_file(filename):
    return send_from_directory(GENERATED_DIR, filename, as_attachment=True)


# ==============================
# ADMIN
# ==============================
@app.route("/admin")
@login_required
def admin():
    if not session.get("is_admin"):
        flash("Admin only.", "error")
        return redirect(url_for("dashboard"))

    return render_template("admin.html", analyses={})


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
