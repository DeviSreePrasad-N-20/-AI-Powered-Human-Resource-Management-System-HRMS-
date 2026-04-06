from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, Employee, JobPosting, LeaveBalance, LeaveRequest, ManagerReview, OnboardingQuestion, ReviewCycle
from ..schemas import DashboardStats, HrAnalytics, MonthlySummary
from ..services.ai import build_monthly_summary, flag_leave_patterns


router = APIRouter(tags=["analytics"])


def _date_range(start_date: date, end_date: date) -> list[date]:
    current = start_date
    days: list[date] = []
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    today = date.today()
    approved_leave_today = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.status == "Approved", LeaveRequest.start_date <= today, LeaveRequest.end_date >= today)
        .count()
    )
    cycles = db.query(ReviewCycle).all()
    manager_reviews = db.query(ManagerReview).all()
    completed_pairs = {(review.cycle_id, review.employee_id) for review in manager_reviews}
    pending_reviews = sum(1 for cycle in cycles for employee_id in cycle.employee_ids if (cycle.id, employee_id) not in completed_pairs)
    return DashboardStats(
        headcount=db.query(Employee).filter(Employee.status == "active").count(),
        open_positions=db.query(JobPosting).filter(JobPosting.status == "open").count(),
        approved_leave_today=approved_leave_today,
        pending_reviews=pending_reviews,
        onboarding_questions=db.query(OnboardingQuestion).count(),
    )


@router.get("/analytics/hr", response_model=HrAnalytics)
def hr_analytics(db: Session = Depends(get_db)) -> HrAnalytics:
    employees = db.query(Employee).all()
    headcount_by_department = dict(Counter(employee.department for employee in employees if employee.status == "active"))

    attrited = [employee for employee in employees if employee.termination_date]
    attrition_rate = (len(attrited) / max(len(employees), 1)) * 100

    today = date.today()
    tenure_map: dict[str, list[float]] = defaultdict(list)
    for employee in employees:
        end_date = employee.termination_date or today
        tenure_years = max((end_date - employee.joining_date).days / 365, 0)
        tenure_map[employee.department].append(round(tenure_years, 2))
    average_tenure_by_department = {
        department: round(sum(values) / len(values), 2) for department, values in tenure_map.items()
    }

    open_positions = db.query(JobPosting).filter(JobPosting.status == "open").count()
    filled_positions = db.query(Candidate).filter(Candidate.stage == "Hired").count()

    approved_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").all()
    leave_days = sum(len(_date_range(leave.start_date, leave.end_date)) for leave in approved_leaves if leave.leave_type.lower() != "wfh")
    balances = db.query(LeaveBalance).all()
    remaining_allowance = sum(balance.sick + balance.casual + balance.earned for balance in balances)
    leave_utilisation_rate = (leave_days / max(leave_days + remaining_allowance, 1)) * 100
    leave_dates = [day for leave in approved_leaves for day in _date_range(leave.start_date, leave.end_date)]
    monthly_summary = build_monthly_summary(
        headcount_by_department=headcount_by_department,
        attrition_rate=attrition_rate,
        open_positions=open_positions,
        leave_utilisation_rate=leave_utilisation_rate,
        leave_flags=flag_leave_patterns(leave_dates),
    )

    return HrAnalytics(
        headcount_by_department=headcount_by_department,
        attrition_rate=round(attrition_rate, 2),
        average_tenure_by_department=average_tenure_by_department,
        open_vs_filled_positions={"open": open_positions, "filled": filled_positions},
        leave_utilisation_rate=round(leave_utilisation_rate, 2),
        ai_summary=monthly_summary["summary"],
    )


@router.get("/analytics/monthly-summary", response_model=MonthlySummary)
def monthly_summary(db: Session = Depends(get_db)) -> MonthlySummary:
    employees = db.query(Employee).all()
    headcount_by_department = dict(Counter(employee.department for employee in employees if employee.status == "active"))
    open_positions = db.query(JobPosting).filter(JobPosting.status == "open").count()
    approved_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").all()
    leave_dates = [day for leave in approved_leaves for day in _date_range(leave.start_date, leave.end_date)]
    leave_days = sum(len(_date_range(leave.start_date, leave.end_date)) for leave in approved_leaves)
    balances = db.query(LeaveBalance).all()
    remaining_allowance = sum(balance.sick + balance.casual + balance.earned for balance in balances)
    leave_utilisation_rate = (leave_days / max(leave_days + remaining_allowance, 1)) * 100
    attrited = len([employee for employee in employees if employee.termination_date])
    attrition_rate = (attrited / max(len(employees), 1)) * 100
    summary = build_monthly_summary(
        headcount_by_department=headcount_by_department,
        attrition_rate=attrition_rate,
        open_positions=open_positions,
        leave_utilisation_rate=leave_utilisation_rate,
        leave_flags=flag_leave_patterns(leave_dates),
    )
    return MonthlySummary(**summary)
