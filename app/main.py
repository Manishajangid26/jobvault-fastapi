import re
import csv
import io
from datetime import datetime, date
from collections import Counter
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, SessionLocal
from app.models import JobApplication, ResumeScan
from app.seed import seed_initial_jobs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JobVault AI — Career Pipeline & ATS Resume API",
    description="Enterprise Job Application Tracker, ATS Resume Keyword Matcher & Analytics REST API built with FastAPI.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

with SessionLocal() as db:
    seed_initial_jobs(db)

STATUS_OPTIONS = ["Applied", "Screening", "Technical Interview", "Final Round", "Offer", "Rejected"]

STOPWORDS = {
    "and", "the", "for", "with", "you", "will", "are", "have", "from", "this", "that",
    "your", "our", "work", "team", "role", "job", "years", "experience", "skills",
    "strong", "good", "knowledge", "ability", "using", "build", "develop", "working",
    "must", "plus", "preferred", "required", "responsibilities", "requirements", "etc"
}


def analyze_resume_ats(resume_text: str, jd_text: str):
    resume_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", resume_text.lower()))
    jd_tokens = [
        w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", jd_text.lower())
        if w not in STOPWORDS and len(w) > 2
    ]

    if not jd_tokens:
        return 0.0, [], []

    freq = Counter(jd_tokens)
    important_jd_keywords = [word for word, _ in freq.most_common(24)]

    matched = sorted([kw for kw in important_jd_keywords if kw in resume_words])
    missing = sorted([kw for kw in important_jd_keywords if kw not in resume_words])

    score = round((len(matched) / len(important_jd_keywords)) * 100, 1) if important_jd_keywords else 0.0
    return score, matched, missing


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(JobApplication).order_by(JobApplication.applied_date.desc()).all()

    total_apps = len(jobs)
    interviews = sum(1 for j in jobs if j.status in ["Screening", "Technical Interview", "Final Round", "Offer"])
    offers = sum(1 for j in jobs if j.status == "Offer")
    avg_ats = round(sum(j.ats_score for j in jobs) / total_apps, 1) if total_apps else 0
    interview_rate = round((interviews / total_apps) * 100, 1) if total_apps else 0

    status_counts = {s: 0 for s in STATUS_OPTIONS}
    for j in jobs:
        if j.status in status_counts:
            status_counts[j.status] += 1

    recent_jobs = jobs[:5]
    recent_scans = db.query(ResumeScan).order_by(ResumeScan.scanned_at.desc()).limit(3).all()

    return templates.TemplateResponse(request, "dashboard.html", {
        "active_page": "dashboard",
        "total_apps": total_apps,
        "interviews": interviews,
        "offers": offers,
        "avg_ats": avg_ats,
        "interview_rate": interview_rate,
        "chart_labels": list(status_counts.keys()),
        "chart_values": list(status_counts.values()),
        "recent_jobs": recent_jobs,
        "recent_scans": recent_scans
    })


@app.get("/applications", response_class=HTMLResponse)
def applications_page(request: Request, status: str = "", q: str = "", db: Session = Depends(get_db)):
    query = db.query(JobApplication)
    if status and status in STATUS_OPTIONS:
        query = query.filter(JobApplication.status == status)
    if q.strip():
        query = query.filter(
            (JobApplication.company.ilike(f"%{q.strip()}%")) |
            (JobApplication.role.ilike(f"%{q.strip()}%"))
        )

    jobs = query.order_by(JobApplication.applied_date.desc(), JobApplication.id.desc()).all()

    return templates.TemplateResponse(request, "applications.html", {
        "active_page": "applications",
        "jobs": jobs,
        "status_options": STATUS_OPTIONS,
        "filter_status": status,
        "search_q": q,
        "today": date.today().strftime("%Y-%m-%d")
    })


@app.post("/applications/add")
def add_application(
    company: str = Form(...),
    role: str = Form(...),
    location: str = Form("Remote"),
    ctc_package: str = Form("8 - 12 LPA"),
    status: str = Form("Applied"),
    ats_score: int = Form(85),
    hr_contact: str = Form(""),
    job_portal: str = Form("LinkedIn"),
    applied_date: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    parsed_date = datetime.strptime(applied_date, "%Y-%m-%d").date() if applied_date else date.today()
    new_job = JobApplication(
        company=company.strip(),
        role=role.strip(),
        location=location.strip(),
        ctc_package=ctc_package.strip(),
        status=status,
        ats_score=max(0, min(100, ats_score)),
        hr_contact=hr_contact.strip(),
        job_portal=job_portal,
        applied_date=parsed_date,
        notes=notes.strip()
    )
    db.add(new_job)
    db.commit()
    return RedirectResponse(url="/applications", status_code=303)


@app.post("/applications/{job_id}/status")
def update_status(job_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if job and status in STATUS_OPTIONS:
        job.status = status
        db.commit()
    return RedirectResponse(url="/applications", status_code=303)


@app.post("/applications/{job_id}/delete")
def delete_application(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if job:
        db.delete(job)
        db.commit()
    return RedirectResponse(url="/applications", status_code=303)


@app.get("/matcher", response_class=HTMLResponse)
def matcher_page(request: Request, db: Session = Depends(get_db)):
    scans = db.query(ResumeScan).order_by(ResumeScan.scanned_at.desc()).limit(6).all()
    return templates.TemplateResponse(request, "matcher.html", {
        "active_page": "matcher",
        "result": None,
        "scans": scans
    })


@app.post("/matcher", response_class=HTMLResponse)
def run_matcher(
    request: Request,
    target_role: str = Form(...),
    resume_text: str = Form(...),
    jd_text: str = Form(...),
    db: Session = Depends(get_db)
):
    score, matched, missing = analyze_resume_ats(resume_text, jd_text)

    scan_record = ResumeScan(
        target_role=target_role.strip(),
        match_score=score,
        matched_keywords=", ".join(matched),
        missing_keywords=", ".join(missing)
    )
    db.add(scan_record)
    db.commit()

    scans = db.query(ResumeScan).order_by(ResumeScan.scanned_at.desc()).limit(6).all()
    result = {
        "target_role": target_role,
        "score": score,
        "matched": matched,
        "missing": missing
    }

    return templates.TemplateResponse(request, "matcher.html", {
        "active_page": "matcher",
        "result": result,
        "scans": scans,
        "resume_text": resume_text,
        "jd_text": jd_text
    })


@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    jobs = db.query(JobApplication).order_by(JobApplication.applied_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Company", "Role", "Location", "CTC", "Status", "ATS Score", "Portal", "Applied Date", "Notes"])
    for j in jobs:
        writer.writerow([j.id, j.company, j.role, j.location, j.ctc_package, j.status, j.ats_score, j.job_portal, j.applied_date, j.notes])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobvault_applications.csv"}
    )


@app.get("/api/jobs", tags=["REST API"])
def api_get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobApplication).all()
    return {
        "total": len(jobs),
        "applications": [j.to_dict() for j in jobs]
    }


@app.get("/api/analytics", tags=["REST API"])
def api_analytics(db: Session = Depends(get_db)):
    jobs = db.query(JobApplication).all()
    status_breakdown = Counter(j.status for j in jobs)
    return {
        "total_applications": len(jobs),
        "average_ats_score": round(sum(j.ats_score for j in jobs) / len(jobs), 1) if jobs else 0,
        "status_breakdown": dict(status_breakdown)
    }