from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def json_list() -> Mapped[list[str]]:
    return mapped_column(JSON, default=list)


def json_dict_list() -> Mapped[list[dict[str, Any]]]:
    return mapped_column(JSON, default=list)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    designation: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(120), index=True)
    joining_date: Mapped[date] = mapped_column(Date)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    contact: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    skills: Mapped[list[str]] = json_list()
    status: Mapped[str] = mapped_column(String(40), default="active")
    bio: Mapped[str] = mapped_column(Text, default="")
    flags: Mapped[list[str]] = json_list()
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    manager: Mapped["Employee | None"] = relationship(remote_side=[id], backref="direct_reports")
    documents: Mapped[list["EmployeeDocument"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    leave_balance: Mapped["LeaveBalance | None"] = relationship(back_populates="employee", uselist=False, cascade="all, delete-orphan")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    title: Mapped[str] = mapped_column(String(160))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(80))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped[Employee] = relationship(back_populates="documents")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(120), index=True)
    job_description: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[list[str]] = json_list()
    experience_level: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(40), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="job_posting", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), default="")
    skills: Mapped[list[str]] = json_list()
    stage: Mapped[str] = mapped_column(String(40), default="Applied")
    resume_filename: Mapped[str] = mapped_column(String(255))
    resume_path: Mapped[str] = mapped_column(String(500))
    resume_text: Mapped[str] = mapped_column(Text, default="")
    match_percent: Mapped[float] = mapped_column(Float, default=0)
    match_reasoning: Mapped[str] = mapped_column(Text, default="")
    strengths: Mapped[list[str]] = json_list()
    gaps: Mapped[list[str]] = json_list()
    interview_questions: Mapped[list[str]] = json_list()
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job_posting: Mapped[JobPosting] = relationship(back_populates="candidates")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), primary_key=True)
    sick: Mapped[float] = mapped_column(Float, default=8)
    casual: Mapped[float] = mapped_column(Float, default=8)
    earned: Mapped[float] = mapped_column(Float, default=15)
    wfh: Mapped[float] = mapped_column(Float, default=30)

    employee: Mapped[Employee] = relationship(back_populates="leave_balance")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    leave_type: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Pending")
    manager_comment: Mapped[str] = mapped_column(Text, default="")
    ai_flags: Mapped[list[str]] = json_list()
    capacity_risk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("employee_id", "record_date", name="uq_employee_attendance_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    record_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str] = mapped_column(Text, default="")


class ReviewCycle(Base):
    __tablename__ = "review_cycles"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_label: Mapped[str] = mapped_column(String(80), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    employee_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SelfAssessment(Base):
    __tablename__ = "self_assessments"
    __table_args__ = (UniqueConstraint("cycle_id", "employee_id", name="uq_self_assessment_cycle_employee"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("review_cycles.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    achievements: Mapped[str] = mapped_column(Text)
    challenges: Mapped[str] = mapped_column(Text)
    goals: Mapped[str] = mapped_column(Text)
    self_rating: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ManagerReview(Base):
    __tablename__ = "manager_reviews"
    __table_args__ = (UniqueConstraint("cycle_id", "employee_id", name="uq_manager_review_cycle_employee"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("review_cycles.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    manager_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    quality: Mapped[int] = mapped_column(Integer)
    delivery: Mapped[int] = mapped_column(Integer)
    communication: Mapped[int] = mapped_column(Integer)
    initiative: Mapped[int] = mapped_column(Integer)
    teamwork: Mapped[int] = mapped_column(Integer)
    manager_comments: Mapped[str] = mapped_column(Text)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    mismatches: Mapped[list[str]] = json_list()
    development_actions: Mapped[list[str]] = json_list()
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OnboardingRole(Base):
    __tablename__ = "onboarding_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(String(120), unique=True)
    checklist_template: Mapped[list[dict[str, Any]]] = json_dict_list()


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("onboarding_roles.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assignee: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    matched_doc_title: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
