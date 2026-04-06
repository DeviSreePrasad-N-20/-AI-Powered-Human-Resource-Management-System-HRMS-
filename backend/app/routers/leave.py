from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AttendanceRecord, Employee, LeaveBalance, LeaveRequest
from ..schemas import AttendanceCreate, AttendanceOut, AttendanceSummary, LeaveBalanceOut, LeaveDecision, LeaveRequestCreate, LeaveRequestOut
from ..services.ai import flag_leave_patterns, predict_capacity_risk


router = APIRouter(prefix="/leave", tags=["leave"])


def _date_range(start_date: date, end_date: date) -> list[date]:
    current = start_date
    days: list[date] = []
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def _leave_units(payload: LeaveRequestCreate) -> float:
    return float(len(_date_range(payload.start_date, payload.end_date)))


@router.get("/balances", response_model=list[LeaveBalanceOut])
def list_balances(db: Session = Depends(get_db)) -> list[LeaveBalance]:
    return db.query(LeaveBalance).order_by(LeaveBalance.employee_id).all()


@router.get("/requests", response_model=list[LeaveRequestOut])
def list_leave_requests(db: Session = Depends(get_db)) -> list[LeaveRequest]:
    return db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()


@router.post("/requests", response_model=LeaveRequestOut)
def create_leave_request(payload: LeaveRequestCreate, db: Session = Depends(get_db)) -> LeaveRequest:
    employee = db.get(Employee, payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    past_leaves = db.query(LeaveRequest).filter(LeaveRequest.employee_id == payload.employee_id, LeaveRequest.status == "Approved").all()
    leave_dates = [day for leave in past_leaves for day in _date_range(leave.start_date, leave.end_date)]

    overlapping = (
        db.query(LeaveRequest, Employee)
        .join(Employee, Employee.id == LeaveRequest.employee_id)
        .filter(
            Employee.department == employee.department,
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
        .all()
    )
    overlapping_people = [emp.name for _, emp in overlapping if emp.id != employee.id]
    total_people = db.query(Employee).filter(Employee.department == employee.department, Employee.status == "active").count()

    leave = LeaveRequest(
        **payload.model_dump(),
        status="Pending",
        ai_flags=flag_leave_patterns(leave_dates + [payload.start_date]),
        capacity_risk=predict_capacity_risk(employee.department, overlapping_people, total_people),
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.patch("/requests/{leave_id}", response_model=LeaveRequestOut)
def decide_leave(leave_id: int, payload: LeaveDecision, db: Session = Depends(get_db)) -> LeaveRequest:
    leave = db.get(LeaveRequest, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    previous_status = leave.status
    leave.status = payload.status
    leave.manager_comment = payload.manager_comment

    if previous_status != "Approved" and payload.status == "Approved":
        balance = db.get(LeaveBalance, leave.employee_id)
        if balance:
            days = len(_date_range(leave.start_date, leave.end_date))
            attr = leave.leave_type.lower()
            if hasattr(balance, attr):
                setattr(balance, attr, max(0.0, getattr(balance, attr) - days))

    db.commit()
    db.refresh(leave)
    return leave


@router.get("/calendar", response_model=dict)
def leave_calendar(month: str, db: Session = Depends(get_db)) -> dict[str, list[dict[str, str]]]:
    target_month = month.strip()
    rows = db.query(LeaveRequest, Employee).join(Employee, Employee.id == LeaveRequest.employee_id).filter(LeaveRequest.status == "Approved").all()
    calendar: dict[str, list[dict[str, str]]] = {}
    for leave, employee in rows:
        for leave_day in _date_range(leave.start_date, leave.end_date):
            day_key = leave_day.isoformat()
            if not day_key.startswith(target_month):
                continue
            calendar.setdefault(day_key, []).append({"employee": employee.name, "type": leave.leave_type, "department": employee.department})
    return calendar


@router.post("/attendance", response_model=AttendanceOut)
def mark_attendance(payload: AttendanceCreate, db: Session = Depends(get_db)) -> AttendanceRecord:
    existing = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.employee_id == payload.employee_id, AttendanceRecord.record_date == payload.record_date)
        .first()
    )
    if existing:
        existing.status = payload.status
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing
    record = AttendanceRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/attendance", response_model=list[AttendanceOut])
def list_attendance(db: Session = Depends(get_db)) -> list[AttendanceRecord]:
    return db.query(AttendanceRecord).order_by(AttendanceRecord.record_date.desc()).all()


@router.get("/attendance/summary", response_model=AttendanceSummary)
def attendance_summary(employee_id: int, month: str, db: Session = Depends(get_db)) -> AttendanceSummary:
    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.employee_id == employee_id)
        .all()
    )
    filtered = [record for record in records if record.record_date.isoformat().startswith(month)]
    totals = Counter(record.status for record in filtered)
    return AttendanceSummary(employee_id=employee_id, month=month, totals=dict(totals))


@router.get("/insights", response_model=dict)
def leave_insights(db: Session = Depends(get_db)) -> dict[str, list[str] | str]:
    approved = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").all()
    leave_dates = [day for leave in approved for day in _date_range(leave.start_date, leave.end_date)]
    flags = flag_leave_patterns(leave_dates)
    busiest_days = Counter(day.isoformat() for day in leave_dates).most_common(3)
    capacity = [f"{day}: {count} people out" for day, count in busiest_days]
    return {
        "flags": flags,
        "capacity_risk_overview": capacity or ["No capacity hotspots detected."],
    }
