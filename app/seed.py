from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models import JobApplication, ResumeScan

def seed_initial_jobs(db: Session):
    if db.query(JobApplication).count() > 0:
        return

    today = date.today()
    starter_jobs = [
        JobApplication(
            company="Razorpay",
            role="Python Backend Engineer",
            location="Bengaluru (Hybrid)",
            ctc_package="14.5 LPA",
            status="Technical Interview",
            ats_score=92,
            hr_contact="ananya.hr@razorpay.com",
            job_portal="LinkedIn",
            applied_date=today - timedelta(days=9),
            notes="Round 1 FastAPI & SQLAlchemy system design cleared."
        ),
        JobApplication(
            company="Zomato",
            role="Full Stack Python Developer",
            location="Gurugram",
            ctc_package="12.0 LPA",
            status="Final Round",
            ats_score=89,
            hr_contact="talent@zomato.com",
            job_portal="Company Career Portal",
            applied_date=today - timedelta(days=14),
            notes="HM discussion scheduled for API optimization & database indexing."
        ),
        JobApplication(
            company="Infosys Finacle",
            role="Associate Python Developer",
            location="Pune / Jaipur",
            ctc_package="7.5 LPA",
            status="Offer",
            ats_score=95,
            hr_contact="recruitment@infosys.com",
            job_portal="Naukri",
            applied_date=today - timedelta(days=22),
            notes="Offer letter received! Reviewing joining timeline."
        ),
        JobApplication(
            company="Postman",
            role="API Platform Engineer (Junior)",
            location="Bengaluru",
            ctc_package="16.0 LPA",
            status="Screening",
            ats_score=86,
            hr_contact="careers@postman.com",
            job_portal="LinkedIn",
            applied_date=today - timedelta(days=4),
            notes="Recruiter shortlisted REST API & FastAPI portfolio projects."
        ),
        JobApplication(
            company="Cred",
            role="Backend SDE - Python",
            location="Bengaluru",
            ctc_package="18.0 LPA",
            status="Applied",
            ats_score=81,
            hr_contact="hiring@cred.club",
            job_portal="Wellfound",
            applied_date=today - timedelta(days=2),
            notes="Submitted FinTrack Pro & CineVerse live deployment links."
        ),
        JobApplication(
            company="TCS Digital",
            role="Python Full Stack Developer",
            location="Jaipur",
            ctc_package="7.0 LPA",
            status="Technical Interview",
            ats_score=88,
            hr_contact="hr.jaipur@tcs.com",
            job_portal="Naukri",
            applied_date=today - timedelta(days=11),
            notes="SQL queries, Flask blueprints, and OOPs round completed."
        ),
        JobApplication(
            company="Swiggy",
            role="Software Engineer I - Backend",
            location="Remote",
            ctc_package="13.5 LPA",
            status="Rejected",
            ats_score=68,
            hr_contact="careers@swiggy.in",
            job_portal="LinkedIn",
            applied_date=today - timedelta(days=19),
            notes="Need stronger Redis & Docker keywords on resume."
        ),
    ]

    db.add_all(starter_jobs)

    sample_scan = ResumeScan(
        target_role="Python Full Stack & FastAPI Developer",
        match_score=87.5,
        matched_keywords="python, fastapi, flask, sqlalchemy, sqlite, rest api, json, git, bootstrap, deployment",
        missing_keywords="docker, postgresql, pytest, redis"
    )
    db.add(sample_scan)
    db.commit()