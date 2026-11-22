from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from app.database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(120), nullable=False)
    role = Column(String(150), nullable=False)
    location = Column(String(100), default="Remote / Bengaluru")
    ctc_package = Column(String(60), default="8 - 12 LPA")
    status = Column(String(50), default="Applied")
    ats_score = Column(Integer, default=80)
    hr_contact = Column(String(120), default="")
    job_portal = Column(String(60), default="LinkedIn")
    applied_date = Column(Date, default=date.today)
    notes = Column(Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "location": self.location,
            "ctc_package": self.ctc_package,
            "status": self.status,
            "ats_score": self.ats_score,
            "hr_contact": self.hr_contact,
            "job_portal": self.job_portal,
            "applied_date": self.applied_date.strftime("%Y-%m-%d") if self.applied_date else "",
            "notes": self.notes
        }


class ResumeScan(Base):
    __tablename__ = "resume_scans"

    id = Column(Integer, primary_key=True, index=True)
    target_role = Column(String(120), nullable=False)
    match_score = Column(Float, nullable=False)
    matched_keywords = Column(Text, default="")
    missing_keywords = Column(Text, default="")
    scanned_at = Column(DateTime, default=datetime.utcnow)