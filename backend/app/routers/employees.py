from __future__ import annotations

import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee, EmployeeDocument
from ..schemas import EmployeeOut, EmployeeUpdate, OrgChartNode
from ..services.ai import detect_profile_flags, generate_employee_bio
from ..services.files import save_upload


router = APIRouter(prefix="/employees", tags=["employees"])


def _serialize_org_chart(employee: Employee, direct_map: dict[int, list[Employee]]) -> OrgChartNode:
    return OrgChartNode(
        id=employee.id,
        name=employee.name,
        designation=employee.designation,
        department=employee.department,
        reports=[_serialize_org_chart(report, direct_map) for report in direct_map.get(employee.id, [])],
    )


@router.get("", response_model=list[EmployeeOut])
def list_employees(query: str | None = None, db: Session = Depends(get_db)) -> list[Employee]:
    q = db.query(Employee)
    if query:
        like_query = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Employee.name.ilike(like_query),
                Employee.department.ilike(like_query),
                Employee.designation.ilike(like_query),
                Employee.contact.ilike(like_query),
                Employee.email.ilike(like_query),
            )
        )
    return q.order_by(Employee.name).all()


@router.post("", response_model=EmployeeOut)
def create_employee(payload: EmployeeUpdate, db: Session = Depends(get_db)) -> Employee:
    existing_profiles = [
        {"email": employee.email, "name": employee.name, "department": employee.department}
        for employee in db.query(Employee).all()
    ]
    employee = Employee(
        **payload.model_dump(),
        bio=generate_employee_bio(payload.name, payload.designation, payload.department, payload.skills, payload.joining_date),
        flags=detect_profile_flags(
            email=payload.email,
            name=payload.name,
            designation=payload.designation,
            department=payload.department,
            contact=payload.contact,
            skills=payload.skills,
            existing_profiles=existing_profiles,
        ),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)) -> Employee:
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for key, value in payload.model_dump().items():
        setattr(employee, key, value)

    others = [
        {"email": row.email, "name": row.name, "department": row.department}
        for row in db.query(Employee).filter(Employee.id != employee_id).all()
    ]
    employee.bio = generate_employee_bio(payload.name, payload.designation, payload.department, payload.skills, payload.joining_date)
    employee.flags = detect_profile_flags(
        email=payload.email,
        name=payload.name,
        designation=payload.designation,
        department=payload.department,
        contact=payload.contact,
        skills=payload.skills,
        existing_profiles=others,
    )
    db.commit()
    db.refresh(employee)
    return employee


@router.post("/{employee_id}/deactivate", response_model=EmployeeOut)
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)) -> Employee:
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.status = "inactive"
    db.commit()
    db.refresh(employee)
    return employee


@router.post("/{employee_id}/documents", response_model=dict)
def upload_employee_document(
    employee_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    file_path, stored_name = save_upload(file, "employee-documents")
    document = EmployeeDocument(
        employee_id=employee_id,
        title=title,
        file_name=stored_name,
        file_path=file_path,
        content_type=file.content_type or "application/octet-stream",
    )
    db.add(document)
    db.commit()
    return {"message": "Document uploaded", "file_path": file_path}


@router.get("/org-chart", response_model=list[OrgChartNode])
def get_org_chart(db: Session = Depends(get_db)) -> list[OrgChartNode]:
    employees = db.query(Employee).order_by(Employee.name).all()
    direct_map: dict[int, list[Employee]] = {}
    roots: list[Employee] = []
    for employee in employees:
        if employee.manager_id:
            direct_map.setdefault(employee.manager_id, []).append(employee)
        else:
            roots.append(employee)
    return [_serialize_org_chart(root, direct_map) for root in roots]


@router.get("/export/csv")
def export_employees(db: Session = Depends(get_db)) -> StreamingResponse:
    employees = db.query(Employee).order_by(Employee.name).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Designation", "Department", "Email", "Contact", "Status", "Skills"])
    for employee in employees:
        writer.writerow(
            [
                employee.name,
                employee.designation,
                employee.department,
                employee.email,
                employee.contact,
                employee.status,
                ", ".join(employee.skills),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )
