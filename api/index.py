import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import docx
import stripe

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

DEMO_VERSION = "vStable"
PAYMENTS_ENABLED = False  # Payments paused

print(f"✅ DEMO MODE DEPLOYED {DEMO_VERSION}")

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
DOMAIN = os.environ.get("DOMAIN", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


@app.get("/__demo_check")
def demo_check():
    return {
        "ok": True,
        "mode": "demo",
        "version": DEMO_VERSION,
        "payments_enabled": PAYMENTS_ENABLED
    }


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


def demo_ai(job_description):
    return f"""
[1] Resume Diagnosis
• Strong professional base.
• Add quantified achievements.
• Improve measurable impact.

[2] ATS Suggestions
• Align resume keywords with job description.

[3] Improved Summary
Results-driven professional focused on measurable performance and scalable solutions.

[4] Experience Improvement
• Increased efficiency by 30% through automation.
• Reduced workflow delays by 25%.

[5] Cover Letter
Dear Hiring Manager,
I am excited to apply for this role. My experience aligns strongly with your requirements and I am confident in delivering measurable results.

Sincerely,
Ahmed Mohy

⚡ DEMO MODE ACTIVE — No OpenAI billing required.
"""


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
        demo_version=DEMO_VERSION
    )


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    # Payment paused
    return redirect(url_for("home"))
