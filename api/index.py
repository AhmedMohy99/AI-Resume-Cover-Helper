import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
import PyPDF2
import docx
import stripe

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
PUBLIC_DIR = BASE_DIR / "public"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(PUBLIC_DIR),
    static_url_path="/public",
)

# ====== ENV FLAGS ======
FREE_TEST_MODE = os.environ.get("FREE_TEST_MODE", "true").lower() == "true"
DOMAIN = os.environ.get("DOMAIN", "").strip()  # e.g. https://your-project.vercel.app

# Stripe (Visa/Master) - optional
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "").strip()  # Create in Stripe dashboard
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

def extract_text_from_file(file_storage):
    filename = (file_storage.filename or "").lower()

    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file_storage.stream)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text.strip()

    if filename.endswith(".docx"):
        document = docx.Document(file_storage.stream)
        return "\n".join([p.text for p in document.paragraphs]).strip()

    return ""

def is_paid(request):
    """
    Payment gating logic:
    - If FREE_TEST_MODE is true, allow free testing.
    - If Stripe is configured, allow access if paid=1 and session verifies as paid.
    """
    if FREE_TEST_MODE:
        return True

    paid = request.args.get("paid", "")
    session_id = request.args.get("session_id", "")

    if not (paid == "1" and session_id and STRIPE_SECRET_KEY):
        return False

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except Exception:
        return False

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    paid_access = is_paid(request)

    if request.method == "POST":
        # Block if not paid and not free-test
        if not paid_access:
            error = "Please complete payment to unlock AI generation."
            return render_template(
                "index.html",
                result=result,
                error=error,
                paid_access=paid_access,
                free_test=FREE_TEST_MODE,
                stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN),
            )

        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a resume file (PDF/DOCX)."
            return render_template("index.html", result=result, error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE,
                                   stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN))

        if not job_description:
            error = "Please paste the job description."
            return render_template("index.html", result=result, error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE,
                                   stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN))

        resume_text = extract_text_from_file(resume_file)
        if not resume_text:
            error = "Could not read text from the file. Try another PDF/DOCX."
            return render_template("index.html", result=result, error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE,
                                   stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN))

        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            error = "Missing OPENAI_API_KEY. Add it in Vercel Environment Variables."
            return render_template("index.html", result=result, error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE,
                                   stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN))

        client = OpenAI(api_key=api_key)

        # ====== "General CV/Resume Instructions" prompt ======
        prompt = f"""
You are an expert Resume Writer + ATS (Applicant Tracking System) optimizer.

GENERAL RULES:
- Use strong action verbs, quantifiable impact, and concise bullets.
- Fix grammar, clarity, and formatting.
- Optimize for ATS: include relevant keywords naturally.
- Avoid exaggeration. Be professional.
- Focus on achievements not tasks.
- Keep cover letter tailored, confident, and specific to the job.

OUTPUT FORMAT (exact headings):
[1] Resume Diagnosis (bullet points)
[2] ATS Keyword Gaps (bullets)
[3] Improved Resume Summary (3 versions)
[4] Improved Experience Bullets (rewrite weak bullets)
[5] Tailored Cover Letter
[6] Final Checklist (short)

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are practical, ATS-focused, and write clean professional English."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.35
            )
            result = response.choices[0].message.content
        except Exception:
            # Hide internal details from users
            error = "AI request failed. Please check your API key and billing, then try again."

    return render_template(
        "index.html",
        result=result,
        error=error,
        paid_access=paid_access,
        free_test=FREE_TEST_MODE,
        stripe_ready=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN),
    )

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    if not (STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN):
        return redirect(url_for("home"))

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{DOMAIN}/?paid=1&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN}/?canceled=1",
        )
        return redirect(session.url, code=303)
    except Exception:
        return redirect(url_for("home"))

"""
Vodafone Cash / local Egypt payments:
Use Paymob (supports cards + mobile wallets like Vodafone Cash). :contentReference[oaicite:1]{index=1}
Implementation needs merchant credentials + integration IDs from Paymob dashboard.
When you're ready, tell me you have Paymob account and I'll add it safely.
"""
