from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    name: str
    designation: str
    department: str
    joining_date: date
    manager_id: int | None = None
    contact: str
    email: str
    skills: list[str] = Field(default_factory=list)
    termination_date: date | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    status: str = "active"


class EmployeeDocumentOut(ORMModel):
    id: int
    title: str
    file_name: str
    file_path: str
    content_type: str
    uploaded_at: datetime


class EmployeeOut(ORMModel):
    id: int
    name: str
    designation: str
    department: str
    joining_date: date
    manager_id: int | None
    contact: str
    email: str
    skills: list[str]
    status: str
    bio: str
    flags: list[str]
    termination_date: date | None
    created_at: datetime
    documents: list[EmployeeDocumentOut] = Field(default_factory=list)


class OrgChartNode(BaseModel):
    id: int
    name: str
    designation: str
    department: str
    reports: list["OrgChartNode"] = Field(default_factory=list)


class JobPostingCreate(BaseModel):
    role: str
    job_description: str
    required_skills: list[str]
    experience_level: str


class JobPostingOut(ORMModel):
    id: int
    role: str
    job_description: str
    required_skills: list[str]
    experience_level: str
    status: str
    created_at: datetime


class CandidateStageUpdate(BaseModel):
    stage: str


class CandidateOut(ORMModel):
    id: int
    job_posting_id: int
    name: str
    email: str
    skills: list[str]
    stage: str
    resume_filename: str
    match_percent: float
    match_reasoning: str
    strengths: list[str]
    gaps: list[str]
    interview_questions: list[str]
    created_at: datetime


class CandidateComparison(BaseModel):
    candidate_id: int
    candidate_name: str
    current_stage: str
    match_percent: float
    strengths: list[str]
    gaps: list[str]
    recommendation: str


class LeaveBalanceOut(ORMModel):
    employee_id: int
    sick: float
    casual: float
    earned: float
    wfh: float


class LeaveRequestCreate(BaseModel):
    employee_id: int
    manager_id: int | None = None
    leave_type: str
    start_date: date
    end_date: date
    reason: str


class LeaveDecision(BaseModel):
    status: str
    manager_comment: str = ""


class LeaveRequestOut(ORMModel):
    id: int
    employee_id: int
    manager_id: int | None
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    manager_comment: str
    ai_flags: list[str]
    capacity_risk: str
    created_at: datetime


class AttendanceCreate(BaseModel):
    employee_id: int
    record_date: date
    status: str
    notes: str = ""


class AttendanceOut(ORMModel):
    id: int
    employee_id: int
    record_date: date
    status: str
    notes: str


class AttendanceSummary(BaseModel):
    employee_id: int
    month: str
    totals: dict[str, int]


class ReviewCycleCreate(BaseModel):
    period_label: str
    start_date: date
    end_date: date
    employee_ids: list[int]


class ReviewCycleOut(ORMModel):
    id: int
    period_label: str
    start_date: date
    end_date: date
    employee_ids: list[int]
    created_at: datetime


class SelfAssessmentCreate(BaseModel):
    cycle_id: int
    employee_id: int
    achievements: str
    challenges: str
    goals: str
    self_rating: int


class SelfAssessmentOut(ORMModel):
    id: int
    cycle_id: int
    employee_id: int
    achievements: str
    challenges: str
    goals: str
    self_rating: int
    created_at: datetime


class ManagerReviewCreate(BaseModel):
    cycle_id: int
    employee_id: int
    manager_id: int
    quality: int
    delivery: int
    communication: int
    initiative: int
    teamwork: int
    manager_comments: str


class ManagerReviewOut(ORMModel):
    id: int
    cycle_id: int
    employee_id: int
    manager_id: int
    quality: int
    delivery: int
    communication: int
    initiative: int
    teamwork: int
    manager_comments: str
    ai_summary: str
    mismatches: list[str]
    development_actions: list[str]
    created_at: datetime


class ReviewSnapshot(BaseModel):
    employee_id: int
    cycle_id: int
    self_assessment: SelfAssessmentOut | None
    manager_review: ManagerReviewOut | None


class OnboardingRoleCreate(BaseModel):
    role_name: str
    checklist_template: list[dict[str, Any]]


class OnboardingRoleOut(ORMModel):
    id: int
    role_name: str
    checklist_template: list[dict[str, Any]]


class OnboardingTaskUpdate(BaseModel):
    status: str


class OnboardingTaskOut(ORMModel):
    id: int
    employee_id: int
    role_id: int | None
    title: str
    due_date: date | None
    assignee: str
    status: str
    created_at: datetime


class OnboardingQuestionCreate(BaseModel):
    employee_id: int | None = None
    question: str


class OnboardingQuestionOut(ORMModel):
    id: int
    employee_id: int | None
    question: str
    answer: str
    matched_doc_title: str
    created_at: datetime


class PolicyDocumentOut(ORMModel):
    id: int
    title: str
    file_name: str
    file_path: str
    uploaded_at: datetime


class DashboardStats(BaseModel):
    headcount: int
    open_positions: int
    approved_leave_today: int
    pending_reviews: int
    onboarding_questions: int


class HrAnalytics(BaseModel):
    headcount_by_department: dict[str, int]
    attrition_rate: float
    average_tenure_by_department: dict[str, float]
    open_vs_filled_positions: dict[str, int]
    leave_utilisation_rate: float
    ai_summary: str


class MonthlySummary(BaseModel):
    summary: str
    highlights: list[str]
    risks: list[str]
    recommended_actions: list[str]
