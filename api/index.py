import os
from pathlib import Path
from flask import Flask, render_template, request
from openai import OpenAI
import PyPDF2
import docx

BASE_DIR = Path(__file__).resolve().parent.parent  # project root
TEMPLATES_DIR = BASE_DIR / "templates"
PUBLIC_DIR = BASE_DIR / "public"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(PUBLIC_DIR),
    static_url_path="/public",
)

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

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a resume file (PDF/DOCX)."
            return render_template("index.html", result=result, error=error)

        if not job_description:
            error = "Please paste the job description."
            return render_template("index.html", result=result, error=error)

        resume_text = extract_text_from_file(resume_file)
        if not resume_text:
            error = "Could not read text from the file. Try another PDF/DOCX."
            return render_template("index.html", result=result, error=error)

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            error = "Missing OPENAI_API_KEY. Add it in Vercel Environment Variables."
            return render_template("index.html", result=result, error=error)

        client = OpenAI(api_key=api_key)

        prompt = f"""
You are a professional resume coach and ATS optimization expert.

Return in this EXACT format:

[1] Quick Resume Diagnosis (bullet points)
[2] Top 10 Improvements (bullets)
[3] Rewritten Resume Summary (3 versions)
[4] Keyword Match Plan (important keywords to add)
[5] Tailored Cover Letter (for this job)
[6] LinkedIn Headline Suggestions (5 options)

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are concise, practical, and ATS-focused."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            result = response.choices[0].message.content
        except Exception as e:
            error = f"AI request failed: {str(e)}"

    return render_template("index.html", result=result, error=error)
