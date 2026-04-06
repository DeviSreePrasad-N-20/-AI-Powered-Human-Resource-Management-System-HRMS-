from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee, ManagerReview, ReviewCycle, SelfAssessment
from ..schemas import (
    ManagerReviewCreate,
    ManagerReviewOut,
    ReviewCycleCreate,
    ReviewCycleOut,
    ReviewSnapshot,
    SelfAssessmentCreate,
    SelfAssessmentOut,
)
from ..services.ai import review_summary
from ..services.reporting import build_review_pdf


router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/cycles", response_model=list[ReviewCycleOut])
def list_cycles(db: Session = Depends(get_db)) -> list[ReviewCycle]:
    return db.query(ReviewCycle).order_by(ReviewCycle.start_date.desc()).all()


@router.post("/cycles", response_model=ReviewCycleOut)
def create_cycle(payload: ReviewCycleCreate, db: Session = Depends(get_db)) -> ReviewCycle:
    cycle = ReviewCycle(**payload.model_dump())
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


@router.post("/self-assessments", response_model=SelfAssessmentOut)
def upsert_self_assessment(payload: SelfAssessmentCreate, db: Session = Depends(get_db)) -> SelfAssessment:
    entry = (
        db.query(SelfAssessment)
        .filter(SelfAssessment.cycle_id == payload.cycle_id, SelfAssessment.employee_id == payload.employee_id)
        .first()
    )
    if entry:
        for key, value in payload.model_dump().items():
            setattr(entry, key, value)
        db.commit()
        db.refresh(entry)
        return entry
    entry = SelfAssessment(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/manager-reviews", response_model=ManagerReviewOut)
def upsert_manager_review(payload: ManagerReviewCreate, db: Session = Depends(get_db)) -> ManagerReview:
    employee = db.get(Employee, payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    self_assessment = (
        db.query(SelfAssessment)
        .filter(SelfAssessment.cycle_id == payload.cycle_id, SelfAssessment.employee_id == payload.employee_id)
        .first()
    )
    summary = review_summary(
        employee_name=employee.name,
        achievements=self_assessment.achievements if self_assessment else "No self-assessment submitted.",
        challenges=self_assessment.challenges if self_assessment else "Not submitted.",
        goals=self_assessment.goals if self_assessment else "Not submitted.",
        self_rating=self_assessment.self_rating if self_assessment else 3,
        ratings={
            "quality": payload.quality,
            "delivery": payload.delivery,
            "communication": payload.communication,
            "initiative": payload.initiative,
            "teamwork": payload.teamwork,
        },
        manager_comments=payload.manager_comments,
    )
    review = (
        db.query(ManagerReview)
        .filter(ManagerReview.cycle_id == payload.cycle_id, ManagerReview.employee_id == payload.employee_id)
        .first()
    )
    data = payload.model_dump()
    data.update(
        {
            "ai_summary": summary["summary"],
            "mismatches": summary["mismatches"],
            "development_actions": summary["development_actions"],
        }
    )
    if review:
        for key, value in data.items():
            setattr(review, key, value)
        db.commit()
        db.refresh(review)
        return review
    review = ManagerReview(**data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews/{cycle_id}/{employee_id}", response_model=ReviewSnapshot)
def get_review_snapshot(cycle_id: int, employee_id: int, db: Session = Depends(get_db)) -> ReviewSnapshot:
    self_assessment = (
        db.query(SelfAssessment)
        .filter(SelfAssessment.cycle_id == cycle_id, SelfAssessment.employee_id == employee_id)
        .first()
    )
    manager_review = (
        db.query(ManagerReview)
        .filter(ManagerReview.cycle_id == cycle_id, ManagerReview.employee_id == employee_id)
        .first()
    )
    return ReviewSnapshot(employee_id=employee_id, cycle_id=cycle_id, self_assessment=self_assessment, manager_review=manager_review)


@router.get("/reviews/{cycle_id}/{employee_id}/export")
def export_review_pdf(cycle_id: int, employee_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    cycle = db.get(ReviewCycle, cycle_id)
    employee = db.get(Employee, employee_id)
    review = (
        db.query(ManagerReview)
        .filter(ManagerReview.cycle_id == cycle_id, ManagerReview.employee_id == employee_id)
        .first()
    )
    if not cycle or not employee or not review:
        raise HTTPException(status_code=404, detail="Review data not found")
    pdf_bytes = build_review_pdf(
        employee_name=employee.name,
        cycle_label=cycle.period_label,
        summary=review.ai_summary,
        manager_comments=review.manager_comments,
        development_actions=review.development_actions,
    )
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={employee.name.replace(' ', '_')}_review.pdf"},
    )
