from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, JobPosting
from ..schemas import CandidateComparison, CandidateOut, CandidateStageUpdate, JobPostingCreate, JobPostingOut
from ..services.ai import score_resume
from ..services.files import extract_text_from_path, save_upload


router = APIRouter(prefix="/recruitment", tags=["recruitment"])


@router.get("/jobs", response_model=list[JobPostingOut])
def list_jobs(db: Session = Depends(get_db)) -> list[JobPosting]:
    return db.query(JobPosting).order_by(JobPosting.created_at.desc()).all()


@router.post("/jobs", response_model=JobPostingOut)
def create_job(payload: JobPostingCreate, db: Session = Depends(get_db)) -> JobPosting:
    job = JobPosting(**payload.model_dump(), status="open")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
def list_candidates(job_id: int, db: Session = Depends(get_db)) -> list[Candidate]:
    return db.query(Candidate).filter(Candidate.job_posting_id == job_id).order_by(Candidate.match_percent.desc()).all()


@router.post("/jobs/{job_id}/candidates", response_model=CandidateOut)
def add_candidate(
    job_id: int,
    name: str = Form(...),
    email: str = Form(""),
    skills: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Candidate:
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    file_path, stored_name = save_upload(file, "resumes")
    resume_text = extract_text_from_path(file_path)
    skill_list = [item.strip() for item in skills.split(",") if item.strip()]
    ai_result = score_resume(job.job_description, job.required_skills, resume_text, skill_list)
    candidate = Candidate(
        job_posting_id=job_id,
        name=name,
        email=email,
        skills=skill_list,
        stage="Applied",
        resume_filename=stored_name,
        resume_path=file_path,
        resume_text=resume_text,
        **ai_result,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.patch("/candidates/{candidate_id}/stage", response_model=CandidateOut)
def update_candidate_stage(candidate_id: int, payload: CandidateStageUpdate, db: Session = Depends(get_db)) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.stage = payload.stage
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/compare", response_model=list[CandidateComparison])
def compare_candidates(candidate_ids: str, db: Session = Depends(get_db)) -> list[CandidateComparison]:
    ids = [int(candidate_id) for candidate_id in candidate_ids.split(",") if candidate_id.strip().isdigit()]
    candidates = db.query(Candidate).filter(Candidate.id.in_(ids)).order_by(Candidate.match_percent.desc()).all()
    if not candidates:
        return []
    top_score = candidates[0].match_percent
    comparisons: list[CandidateComparison] = []
    for candidate in candidates:
        delta = top_score - candidate.match_percent
        recommendation = "Top recommended shortlist" if delta <= 5 else "Good fit, but below top profile"
        comparisons.append(
            CandidateComparison(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                current_stage=candidate.stage,
                match_percent=candidate.match_percent,
                strengths=candidate.strengths,
                gaps=candidate.gaps,
                recommendation=recommendation,
            )
        )
    return comparisons
