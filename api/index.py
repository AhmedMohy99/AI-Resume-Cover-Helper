import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
import PyPDF2
import docx
import stripe

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

FREE_TEST_MODE = os.environ.get("FREE_TEST_MODE", "true").lower() == "true"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "").strip()
DOMAIN = os.environ.get("DOMAIN", "").strip()

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


def stripe_ready():
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and DOMAIN)


def has_paid_access(req):
    if FREE_TEST_MODE:
        return True

    paid = req.args.get("paid", "")
    session_id = req.args.get("session_id", "")

    if not (paid == "1" and session_id and stripe_ready()):
        return False

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except Exception:
        return False


def friendly_openai_error(e: Exception) -> str:
    msg = str(e).lower()

    # These messages cover 95% of issues on Vercel
    if "invalid api key" in msg or "invalid_api_key" in msg:
        return "Invalid API key. Please update OPENAI_API_KEY in Vercel."
    if "insufficient_quota" in msg or "quota" in msg:
        return "Quota/Billing issue. Please enable billing on your OpenAI account."
    if "rate limit" in msg:
        return "Too many requests. Please try again in a minute."
    if "model" in msg and "not found" in msg:
        return "Model not available. Change model name in the backend."
    return "AI request failed. Please check your API key and billing, then try again."


@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""
    paid_access = has_paid_access(request)

    if request.method == "POST":
        if not paid_access:
            error = "Payment required to unlock AI generation. (Free test mode is OFF)"
            return render_template(
                "index.html",
                result=result,
                error=error,
                paid_access=paid_access,
                free_test=FREE_TEST_MODE,
                stripe_ready=stripe_ready(),
            )

        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a resume file (PDF/DOCX)."
            return render_template("index.html", result="", error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE, stripe_ready=stripe_ready())

        if not job_description:
            error = "Please paste the job description."
            return render_template("index.html", result="", error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE, stripe_ready=stripe_ready())

        resume_text = extract_text_from_file(resume_file)
        if not resume_text:
            error = "Could not read text from the file. Try another PDF/DOCX."
            return render_template("index.html", result="", error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE, stripe_ready=stripe_ready())

        if not OPENAI_API_KEY:
            error = "Missing OPENAI_API_KEY. Add it in Vercel Environment Variables."
            return render_template("index.html", result="", error=error,
                                   paid_access=paid_access, free_test=FREE_TEST_MODE, stripe_ready=stripe_ready())

        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
You are an expert Resume Writer and ATS optimizer.

GENERAL RULES:
- Use strong action verbs, quantified impact, and concise bullet points.
- Fix grammar, clarity, and structure.
- Optimize for ATS by adding relevant keywords naturally.
- Do NOT exaggerate. Keep professional tone.
- Focus on achievements, not tasks.

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
                    {"role": "user", "content": prompt},
                ],
                temperature=0.35,
            )
            result = response.choices[0].message.content

            # If somehow the model returns duplicated lines, we can clean it a bit:
            lines = result.splitlines()
            cleaned = []
            last = None
            for line in lines:
                if line.strip() and line.strip() == (last or "").strip():
                    continue
                cleaned.append(line)
                last = line
            result = "\n".join(cleaned)

        except Exception as e:
            # Log the real error for you (visible in Vercel logs)
            print("OPENAI_ERROR:", repr(e))
            error = friendly_openai_error(e)
            result = ""  # IMPORTANT: avoid printing error many times inside result box

    return render_template(
        "index.html",
        result=result,
        error=error,
        paid_access=paid_access,
        free_test=FREE_TEST_MODE,
        stripe_ready=stripe_ready(),
    )


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    if not stripe_ready():
        return redirect(url_for("home"))

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{DOMAIN}/?paid=1&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN}/?canceled=1",
        )
        return redirect(session.url, code=303)
    except Exception as e:
        print("STRIPE_ERROR:", repr(e))
        return redirect(url_for("home"))
