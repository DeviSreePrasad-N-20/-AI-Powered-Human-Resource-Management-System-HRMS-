from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee, OnboardingQuestion, OnboardingRole, OnboardingTask, PolicyDocument
from ..schemas import (
    OnboardingQuestionCreate,
    OnboardingQuestionOut,
    OnboardingRoleCreate,
    OnboardingRoleOut,
    OnboardingTaskOut,
    OnboardingTaskUpdate,
    PolicyDocumentOut,
)
from ..services.ai import answer_from_documents
from ..services.files import extract_text_from_path, save_upload


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/roles", response_model=list[OnboardingRoleOut])
def list_roles(db: Session = Depends(get_db)) -> list[OnboardingRole]:
    return db.query(OnboardingRole).order_by(OnboardingRole.role_name).all()


@router.post("/roles", response_model=OnboardingRoleOut)
def create_role(payload: OnboardingRoleCreate, db: Session = Depends(get_db)) -> OnboardingRole:
    role = OnboardingRole(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.post("/roles/{role_id}/assign/{employee_id}", response_model=list[OnboardingTaskOut])
def assign_role_checklist(role_id: int, employee_id: int, db: Session = Depends(get_db)) -> list[OnboardingTask]:
    employee = db.get(Employee, employee_id)
    role = db.get(OnboardingRole, role_id)
    if not employee or not role:
        raise HTTPException(status_code=404, detail="Employee or role not found")

    db.query(OnboardingTask).filter(OnboardingTask.employee_id == employee_id, OnboardingTask.role_id == role_id).delete()
    tasks: list[OnboardingTask] = []
    for item in role.checklist_template:
        due_offset = int(item.get("due_offset_days", 0))
        tasks.append(
            OnboardingTask(
                employee_id=employee_id,
                role_id=role_id,
                title=str(item.get("title", "Checklist item")),
                due_date=employee.joining_date + timedelta(days=due_offset),
                assignee=str(item.get("assignee", "HR")),
                status="Pending",
            )
        )
    db.add_all(tasks)
    db.commit()
    return db.query(OnboardingTask).filter(OnboardingTask.employee_id == employee_id, OnboardingTask.role_id == role_id).all()


@router.get("/tasks/{employee_id}", response_model=list[OnboardingTaskOut])
def list_tasks(employee_id: int, db: Session = Depends(get_db)) -> list[OnboardingTask]:
    return db.query(OnboardingTask).filter(OnboardingTask.employee_id == employee_id).order_by(OnboardingTask.due_date).all()


@router.patch("/tasks/{task_id}", response_model=OnboardingTaskOut)
def update_task(task_id: int, payload: OnboardingTaskUpdate, db: Session = Depends(get_db)) -> OnboardingTask:
    task = db.get(OnboardingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = payload.status
    db.commit()
    db.refresh(task)
    return task


@router.get("/documents", response_model=list[PolicyDocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[PolicyDocument]:
    return db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()


@router.post("/documents", response_model=PolicyDocumentOut)
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> PolicyDocument:
    file_path, stored_name = save_upload(file, "policies")
    extracted_text = extract_text_from_path(file_path)
    document = PolicyDocument(title=title, file_name=stored_name, file_path=file_path, extracted_text=extracted_text)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/ask", response_model=OnboardingQuestionOut)
def ask_question(payload: OnboardingQuestionCreate, db: Session = Depends(get_db)) -> OnboardingQuestion:
    docs = [
        {"title": document.title, "text": document.extracted_text}
        for document in db.query(PolicyDocument).all()
        if document.extracted_text
    ]
    answer = answer_from_documents(payload.question, docs, None)
    log = OnboardingQuestion(
        employee_id=payload.employee_id,
        question=payload.question,
        answer=answer["answer"],
        matched_doc_title=answer["matched_doc_title"],
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/questions", response_model=list[OnboardingQuestionOut])
def list_questions(db: Session = Depends(get_db)) -> list[OnboardingQuestion]:
    return db.query(OnboardingQuestion).order_by(OnboardingQuestion.created_at.desc()).all()


@router.get("/question-analytics", response_model=list[dict])
def question_analytics(db: Session = Depends(get_db)) -> list[dict[str, int | str]]:
    rows = (
        db.query(OnboardingQuestion.question, func.count(OnboardingQuestion.id))
        .group_by(OnboardingQuestion.question)
        .order_by(func.count(OnboardingQuestion.id).desc())
        .limit(10)
        .all()
    )
    return [{"question": question, "count": count} for question, count in rows]
