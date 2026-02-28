import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import docx
import stripe

# ======================
# SETUP
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

DEMO_VERSION = "vFinal"
PAYMENTS_ENABLED = False  # 🔴 PAUSED

print(f"✅ DEMO MODE DEPLOYED {DEMO_VERSION}")

# ======================
# PAYMENT CONFIG (PAUSED)
# ======================
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
DOMAIN = os.environ.get("DOMAIN", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def stripe_ready():
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN)


# ======================
# DEMO CHECK ENDPOINT
# ======================
@app.get("/__demo_check")
def demo_check():
    return {
        "ok": True,
        "mode": "demo",
        "version": DEMO_VERSION,
        "payments_enabled": PAYMENTS_ENABLED
    }


# ======================
# FILE READER
# ======================
def extract_text_from_file(file_storage):
    filename = (file_storage.filename or "").lower()

    try:
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file_storage.stream)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text.strip()

        if filename.endswith(".docx"):
            document = docx.Document(file_storage.stream)
            return "\n".join([p.text for p in document.paragraphs]).strip()

    except Exception:
        return ""

    return ""


# ======================
# DEMO AI OUTPUT
# ======================
def demo_ai(job_description):
    jd = job_description.lower()
    detected = []

    for word in ["python", "sql", "machine learning", "nlp", "api", "docker", "aws", "flask", "analytics"]:
        if word in jd:
            detected.append(word)

    keywords = ", ".join(detected) if detected else "communication, teamwork, ownership"

    return f"""
[1] Resume Diagnosis
• Good technical base detected.
• Missing quantified achievements.
• Improve clarity and measurable impact.

[2] ATS Keyword Gaps
• Suggested keywords: {keywords}

[3] Improved Resume Summary
Results-driven professional delivering measurable outcomes and scalable solutions.

[4] Improved Experience Bullet Example
• Increased efficiency by 30% by automating internal reporting workflows.
• Reduced processing time by 25% through system optimization.

[5] Tailored Cover Letter
Dear Hiring Manager,
I am excited to apply for this role. My experience aligns strongly with your requirements and I am confident in my ability to deliver measurable results for your team.

Sincerely,
Ahmed Mohy

[6] Final Checklist
✔ Add numbers
✔ Use strong action verbs
✔ Match job keywords
✔ Keep ATS-friendly formatting

⚡ DEMO MODE ACTIVE — No OpenAI billing required.
""".strip()


# ======================
# MAIN ROUTE
# ======================
@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file:
            error = "Please upload a resume file."
        elif not job_description:
            error = "Please paste the job description."
        else:
            result = demo_ai(job_description)

    return render_template(
        "index.html",
        result=result,
        error=error,
        demo=True,
        demo_version=DEMO_VERSION,
        payments_enabled=PAYMENTS_ENABLED,
        stripe_ready=stripe_ready()
    )


# ======================
# STRIPE ROUTE (PAUSED)
# ======================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    return redirect(url_for("home"))
