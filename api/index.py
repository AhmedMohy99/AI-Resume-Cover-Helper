import os
from pathlib import Path
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

FREE_TEST_MODE = True  # Always enabled in demo


def extract_text_from_file(file_storage):
    filename = (file_storage.filename or "").lower()

    try:
        if filename.endswith(".pdf"):
            import PyPDF2
            reader = PyPDF2.PdfReader(file_storage.stream)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text.strip()

        if filename.endswith(".docx"):
            import docx
            document = docx.Document(file_storage.stream)
            return "\n".join([p.text for p in document.paragraphs]).strip()
    except Exception:
        return ""

    return ""


def generate_demo_ai_response(resume_text, job_description):
    return f"""
[1] Resume Diagnosis
• Strong technical foundation detected.
• Resume lacks quantified achievements.
• Summary section can be more impact-driven.
• ATS keyword alignment could be improved.

[2] ATS Keyword Gaps
• Data Analysis
• Cross-functional Collaboration
• Agile Methodology
• KPI Optimization
• Strategic Planning

[3] Improved Resume Summary (3 Versions)

Version A:
Results-driven professional with demonstrated experience delivering measurable impact through data-driven strategies.

Version B:
Detail-oriented and performance-focused specialist skilled in driving operational efficiency and business growth.

Version C:
Innovative contributor combining analytical thinking with execution excellence to deliver scalable solutions.

[4] Improved Experience Bullets
• Increased operational efficiency by 28% through process automation.
• Reduced processing time by 35% via workflow optimization.
• Led cross-functional initiatives improving KPI performance.

[5] Tailored Cover Letter

Dear Hiring Manager,

I am excited to apply for this opportunity. With a strong background in delivering measurable results and optimizing performance, I am confident I can contribute meaningfully to your organization. My experience aligns well with your requirements, particularly in strategic execution and data-driven decision-making.

I look forward to discussing how I can add value to your team.

Sincerely,
Your Name

[6] Final Checklist
✔ Add quantified achievements
✔ Align keywords with job description
✔ Keep formatting ATS-friendly
✔ Use action verbs consistently

⚡ DEMO MODE ACTIVE — This is simulated AI output.
"""
    

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not resume_file or resume_file.filename == "":
            error = "Please upload a resume file."
        elif not job_description:
            error = "Please paste the job description."
        else:
            resume_text = extract_text_from_file(resume_file)
            result = generate_demo_ai_response(resume_text, job_description)

    return render_template(
        "index.html",
        result=result,
        error=error,
        paid_access=True,
        free_test=True,
        stripe_ready=False,
    )
