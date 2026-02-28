import os
from pathlib import Path
from flask import Flask, render_template, request
import PyPDF2
import docx

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

# Force Demo Mode
DEMO_VERSION = "v2"
print(f"✅ DEMO MODE DEPLOYED {DEMO_VERSION}")


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


def demo_ai(resume_text: str, job_description: str) -> str:
    # Super simple keyword tease (looks smart)
    jd = job_description.lower()
    keywords = []
    for k in ["python", "sql", "machine learning", "nlp", "api", "docker", "aws", "flask", "fastapi", "analytics"]:
        if k in jd:
            keywords.append(k)

    kw_line = ", ".join(keywords[:8]) if keywords else "communication, ownership, teamwork, problem-solving"

    return f"""
[1] Resume Diagnosis
• Strong baseline profile detected, but impact metrics are missing.
• Formatting can be made more ATS-friendly (consistent titles + dates).
• Summary should be more specific to the target role.

[2] ATS Keyword Gaps
• Suggested keywords to include: {kw_line}
• Add tools/skills in a dedicated “Skills” section.

[3] Improved Resume Summary (3 Versions)
Version A:
Results-driven professional with a focus on measurable outcomes, process improvement, and execution excellence.

Version B:
Analytical and detail-oriented contributor with proven ability to deliver scalable solutions and optimize performance.

Version C:
Impact-focused specialist combining technical execution and stakeholder alignment to drive business value.

[4] Improved Experience Bullets (Examples)
• Increased workflow efficiency by 25% by automating repetitive reporting tasks.
• Reduced turnaround time by 30% through process redesign and KPI monitoring.
• Collaborated cross-functionally to deliver projects on schedule and within scope.

[5] Tailored Cover Letter (Demo)
Dear Hiring Manager,
I’m excited to apply for this role. My background aligns with your needs, especially in delivering measurable results,
improving systems, and working across teams. I’m confident I can contribute immediate value and would welcome the
opportunity to discuss how I can support your goals.

Sincerely,
Ahmed Mohy

[6] Final Checklist
✔ Add numbers (%, $, time saved)
✔ Match keywords from the JD naturally
✔ Keep bullet points concise (1–2 lines)
✔ Ensure ATS-safe formatting (no tables/images)

⚡ DEMO MODE ACTIVE — Simulated output (no OpenAI billing required).
""".strip()


@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a resume file (PDF/DOCX)."
        elif not job_description:
            error = "Please paste the job description."
        else:
            resume_text = extract_text_from_file(resume_file)
            if not resume_text:
                resume_text = "(No readable text detected in file — demo output generated anyway.)"
            result = demo_ai(resume_text, job_description)

    return render_template(
        "index.html",
        result=result,
        error=error,
        paid_access=True,
        free_test=True,
        stripe_ready=False,
        demo=True,
        demo_version=DEMO_VERSION,
        
    @app.get("/__demo_check")
def demo_check():
    return {"ok": True, "mode": "demo", "version": "v2"}
    )
