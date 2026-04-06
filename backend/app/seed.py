from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from .models import (
    AttendanceRecord,
    Candidate,
    Employee,
    JobPosting,
    LeaveBalance,
    LeaveRequest,
    ManagerReview,
    OnboardingQuestion,
    OnboardingRole,
    OnboardingTask,
    PolicyDocument,
    ReviewCycle,
    SelfAssessment,
)
from .services.ai import generate_employee_bio, review_summary, score_resume


def seed_database(db: Session, uploads_dir: Path) -> None:
    if db.query(Employee).first():
        return

    employees = [
        Employee(
            name="Aarav Mehta",
            designation="HR Director",
            department="People Ops",
            joining_date=date(2022, 1, 12),
            contact="+91-98765-10001",
            email="aarav.mehta@hrms.local",
            skills=["Workforce planning", "Policy design", "Coaching"],
            status="active",
            bio=generate_employee_bio(
                "Aarav Mehta",
                "HR Director",
                "People Ops",
                ["Workforce planning", "Policy design", "Coaching"],
                date(2022, 1, 12),
                prefer_openai=False,
            ),
            flags=[],
        ),
        Employee(
            name="Neha Iyer",
            designation="Engineering Manager",
            department="Engineering",
            joining_date=date(2023, 3, 6),
            manager_id=1,
            contact="+91-98765-10002",
            email="neha.iyer@hrms.local",
            skills=["React", "System design", "Mentoring"],
            status="active",
            bio=generate_employee_bio(
                "Neha Iyer",
                "Engineering Manager",
                "Engineering",
                ["React", "System design", "Mentoring"],
                date(2023, 3, 6),
                prefer_openai=False,
            ),
            flags=[],
        ),
        Employee(
            name="Rohan Gupta",
            designation="Software Engineer",
            department="Engineering",
            joining_date=date(2024, 7, 15),
            manager_id=2,
            contact="+91-98765-10003",
            email="rohan.gupta@hrms.local",
            skills=["Python", "FastAPI", "SQL"],
            status="active",
            bio=generate_employee_bio(
                "Rohan Gupta",
                "Software Engineer",
                "Engineering",
                ["Python", "FastAPI", "SQL"],
                date(2024, 7, 15),
                prefer_openai=False,
            ),
            flags=[],
        ),
        Employee(
            name="Priya Nair",
            designation="Marketing Executive",
            department="Marketing",
            joining_date=date(2024, 2, 20),
            manager_id=1,
            contact="+91-98765-10004",
            email="priya.nair@hrms.local",
            skills=["Campaigns", "Content strategy", "Analytics"],
            status="active",
            bio=generate_employee_bio(
                "Priya Nair",
                "Marketing Executive",
                "Marketing",
                ["Campaigns", "Content strategy", "Analytics"],
                date(2024, 2, 20),
                prefer_openai=False,
            ),
            flags=[],
        ),
        Employee(
            name="Karan Singh",
            designation="People Partner",
            department="People Ops",
            joining_date=date(2023, 11, 1),
            manager_id=1,
            contact="+91-98765-10005",
            email="karan.singh@hrms.local",
            skills=["Employee relations", "Onboarding", "HRIS"],
            status="active",
            bio=generate_employee_bio(
                "Karan Singh",
                "People Partner",
                "People Ops",
                ["Employee relations", "Onboarding", "HRIS"],
                date(2023, 11, 1),
                prefer_openai=False,
            ),
            flags=[],
        ),
    ]
    db.add_all(employees)
    db.flush()

    db.add_all(
        [
            LeaveBalance(employee_id=1, sick=10, casual=8, earned=15, wfh=20),
            LeaveBalance(employee_id=2, sick=8, casual=6, earned=12, wfh=24),
            LeaveBalance(employee_id=3, sick=6, casual=7, earned=15, wfh=24),
            LeaveBalance(employee_id=4, sick=8, casual=8, earned=12, wfh=20),
            LeaveBalance(employee_id=5, sick=9, casual=7, earned=14, wfh=24),
        ]
    )

    job = JobPosting(
        role="Full Stack Engineer",
        job_description="Build React and FastAPI features, own SQLite-backed APIs, and collaborate with product and design teams.",
        required_skills=["React", "TypeScript", "FastAPI", "SQL", "REST APIs"],
        experience_level="Mid-Senior",
        status="open",
    )
    db.add(job)
    db.flush()

    resume_one = "Experienced engineer with React, TypeScript, FastAPI, REST APIs, and SQL delivery across internal tools."
    resume_two = "Backend-focused engineer with Python, Django, PostgreSQL, and stakeholder communication."

    score_one = score_resume(
        job.job_description,
        job.required_skills,
        resume_one,
        ["React", "TypeScript", "FastAPI", "SQL"],
        prefer_openai=False,
    )
    score_two = score_resume(
        job.job_description,
        job.required_skills,
        resume_two,
        ["Python", "Django", "PostgreSQL"],
        prefer_openai=False,
    )

    candidate_one = Candidate(
        job_posting_id=job.id,
        name="Ishita Rao",
        email="ishita.rao@example.com",
        skills=["React", "TypeScript", "FastAPI", "SQL"],
        stage="Interview",
        resume_filename="ishita-rao.pdf",
        resume_path=(uploads_dir / "seed-ishita.txt").as_posix(),
        resume_text=resume_one,
        **score_one,
    )
    candidate_two = Candidate(
        job_posting_id=job.id,
        name="Manav Kapoor",
        email="manav.kapoor@example.com",
        skills=["Python", "Django", "PostgreSQL"],
        stage="Screening",
        resume_filename="manav-kapoor.pdf",
        resume_path=(uploads_dir / "seed-manav.txt").as_posix(),
        resume_text=resume_two,
        **score_two,
    )
    db.add_all([candidate_one, candidate_two])

    db.add_all(
        [
            LeaveRequest(
                employee_id=3,
                manager_id=2,
                leave_type="Casual",
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=4),
                reason="Family event",
                status="Approved",
                manager_comment="Approved. Please hand over sprint items.",
                ai_flags=[],
                capacity_risk="Low risk: current leave overlap should be manageable.",
            ),
            LeaveRequest(
                employee_id=4,
                manager_id=1,
                leave_type="WFH",
                start_date=date.today(),
                end_date=date.today(),
                reason="Vendor coordination from home",
                status="Approved",
                manager_comment="Approved.",
                ai_flags=[],
                capacity_risk="Low risk: current leave overlap should be manageable.",
            ),
        ]
    )

    current_month = date.today().replace(day=1)
    attendance = [
        AttendanceRecord(employee_id=3, record_date=current_month + timedelta(days=day), status="Present", notes="")
        for day in range(0, 5)
    ]
    attendance.append(AttendanceRecord(employee_id=3, record_date=current_month + timedelta(days=5), status="WFH", notes="Deep work day"))
    attendance.append(AttendanceRecord(employee_id=4, record_date=current_month + timedelta(days=1), status="Half Day", notes="Client shoot"))
    db.add_all(attendance)

    cycle = ReviewCycle(
        period_label="Q2 2026",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        employee_ids=[2, 3, 4],
    )
    db.add(cycle)
    db.flush()

    self_assessment = SelfAssessment(
        cycle_id=cycle.id,
        employee_id=3,
        achievements="Delivered employee directory filters, fixed API latency, and supported release stabilization.",
        challenges="Context switching between bugs and roadmap work.",
        goals="Improve test coverage and mentor one junior teammate.",
        self_rating=4,
    )
    db.add(self_assessment)
    db.flush()

    review_ai = review_summary(
        employee_name="Rohan Gupta",
        achievements=self_assessment.achievements,
        challenges=self_assessment.challenges,
        goals=self_assessment.goals,
        self_rating=self_assessment.self_rating,
        ratings={
            "quality": 4,
            "delivery": 4,
            "communication": 3,
            "initiative": 4,
            "teamwork": 5,
        },
        manager_comments="Strong ownership in sprint execution and reliable collaboration with design and QA.",
        prefer_openai=False,
    )
    manager_review = ManagerReview(
        cycle_id=cycle.id,
        employee_id=3,
        manager_id=2,
        quality=4,
        delivery=4,
        communication=3,
        initiative=4,
        teamwork=5,
        manager_comments="Strong ownership in sprint execution and reliable collaboration with design and QA.",
        ai_summary=review_ai["summary"],
        mismatches=review_ai["mismatches"],
        development_actions=review_ai["development_actions"],
    )
    db.add(manager_review)

    engineer_role = OnboardingRole(
        role_name="Software Engineer",
        checklist_template=[
            {"title": "Set up laptop and SSO", "due_offset_days": 1, "assignee": "IT"},
            {"title": "Read engineering handbook", "due_offset_days": 2, "assignee": "Employee"},
            {"title": "Meet team manager", "due_offset_days": 3, "assignee": "Manager"},
            {"title": "Complete secure coding training", "due_offset_days": 5, "assignee": "Employee"},
        ],
    )
    db.add(engineer_role)
    db.flush()

    new_joiner_start = date.today() - timedelta(days=2)
    db.add_all(
        [
            OnboardingTask(employee_id=3, role_id=engineer_role.id, title="Set up laptop and SSO", due_date=new_joiner_start + timedelta(days=1), assignee="IT", status="Completed"),
            OnboardingTask(employee_id=3, role_id=engineer_role.id, title="Read engineering handbook", due_date=new_joiner_start + timedelta(days=2), assignee="Employee", status="In Progress"),
            OnboardingTask(employee_id=3, role_id=engineer_role.id, title="Meet team manager", due_date=new_joiner_start + timedelta(days=3), assignee="Manager", status="Pending"),
        ]
    )

    policies_dir = uploads_dir / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)
    handbook_path = policies_dir / "employee-handbook.txt"
    handbook_text = (
        "Employees may work from home up to two days per week with manager approval. "
        "Sick leave should be reported to the reporting manager before 10 AM. "
        "New joiners receive laptop access on day one and must complete secure coding training within five days."
    )
    handbook_path.write_text(handbook_text, encoding="utf-8")
    db.add(
        PolicyDocument(
            title="Employee Handbook",
            file_name=handbook_path.name,
            file_path=handbook_path.as_posix(),
            extracted_text=handbook_text,
        )
    )

    db.add(
        OnboardingQuestion(
            employee_id=3,
            question="How many WFH days are allowed?",
            answer="According to Employee Handbook: Employees may work from home up to two days per week with manager approval.",
            matched_doc_title="Employee Handbook",
        )
    )

    db.commit()
