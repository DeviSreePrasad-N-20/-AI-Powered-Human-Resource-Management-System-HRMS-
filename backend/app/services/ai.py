from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from datetime import date
from functools import lru_cache
from statistics import mean
from typing import Any

from pydantic import BaseModel, ValidationError

from ..settings import get_settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - fallback only when dependency is missing
    OpenAI = None


logger = logging.getLogger(__name__)

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "have",
    "has",
    "into",
    "your",
    "their",
    "about",
    "would",
    "should",
    "will",
    "been",
    "able",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "also",
    "using",
    "used",
    "more",
    "than",
    "they",
    "them",
    "into",
    "across",
}


class ResumeAnalysis(BaseModel):
    match_percent: float
    match_reasoning: str
    strengths: list[str]
    gaps: list[str]
    interview_questions: list[str]


class ReviewSummaryResult(BaseModel):
    summary: str
    mismatches: list[str]
    development_actions: list[str]


class DocumentAnswerResult(BaseModel):
    answer: str
    matched_doc_title: str


class MonthlySummaryResult(BaseModel):
    summary: str
    highlights: list[str]
    risks: list[str]
    recommended_actions: list[str]


_MONTHLY_SUMMARY_CACHE: dict[str, dict[str, object]] = {}


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9+#.]+", text.lower()) if token not in STOP_WORDS]


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def _truncate(text: str, limit: int = 12000) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _normalize_list(values: list[str], *, limit: int) -> list[str]:
    cleaned = [re.sub(r"\s+", " ", value).strip(" -") for value in values if value and value.strip()]
    return cleaned[:limit]


def ai_provider_name() -> str:
    settings = get_settings()
    if settings.openai_enabled and OpenAI is not None:
        return "openai"
    return "local-fallback"


@lru_cache(maxsize=1)
def _openai_client() -> OpenAI | None:
    settings = get_settings()
    if not settings.openai_enabled or OpenAI is None:
        return None
    return OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)


def _request_text(
    instructions: str,
    user_input: str,
    *,
    json_output: bool = False,
    max_output_tokens: int = 600,
    prefer_openai: bool = True,
) -> str | None:
    if not prefer_openai:
        return None

    client = _openai_client()
    if client is None:
        return None

    settings = get_settings()
    normalized_instructions = instructions.strip()
    normalized_input = user_input.strip()
    if json_output:
        normalized_instructions = (
            f"{normalized_instructions} Return only valid JSON that matches the requested shape."
        )
        normalized_input = f"JSON response required.\n\n{normalized_input}"

    request_kwargs: dict[str, Any] = {
        "model": settings.openai_model,
        "instructions": normalized_instructions,
        "input": normalized_input,
        "max_output_tokens": max_output_tokens,
    }
    if settings.openai_model.startswith("gpt-5"):
        request_kwargs["reasoning"] = {"effort": settings.openai_reasoning_effort}
    if json_output:
        request_kwargs["text"] = {"format": {"type": "json_object"}}

    try:
        response = client.responses.create(**request_kwargs)
        text = (response.output_text or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("OpenAI request failed; falling back to local AI helpers: %s", exc)
        return None


def _request_json(
    model_type: type[BaseModel],
    instructions: str,
    user_input: str,
    *,
    max_output_tokens: int = 800,
    prefer_openai: bool = True,
) -> BaseModel | None:
    raw = _request_text(
        instructions,
        user_input,
        json_output=True,
        max_output_tokens=max_output_tokens,
        prefer_openai=prefer_openai,
    )
    if not raw:
        return None
    try:
        return model_type.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("OpenAI returned invalid JSON for %s: %s", model_type.__name__, exc)
        return None


def _fallback_generate_employee_bio(name: str, designation: str, department: str, skills: list[str], joining_date: date) -> str:
    skills_text = ", ".join(skills[:3]) if skills else "cross-functional collaboration"
    return (
        f"{name} joined the {department} team on {joining_date.isoformat()} as {designation}. "
        f"They bring strength in {skills_text} and contribute across day-to-day delivery, team coordination, "
        "and continuous process improvement."
    )


def generate_employee_bio(
    name: str,
    designation: str,
    department: str,
    skills: list[str],
    joining_date: date,
    *,
    prefer_openai: bool = True,
) -> str:
    text = _request_text(
        (
            "You write short professional employee bios for internal HR profiles. "
            "Use only the facts provided, keep it to 2 or 3 sentences, and do not invent achievements."
        ),
        (
            f"Name: {name}\n"
            f"Role: {designation}\n"
            f"Department: {department}\n"
            f"Joining date: {joining_date.isoformat()}\n"
            f"Skills: {', '.join(skills) if skills else 'None provided'}"
        ),
        max_output_tokens=180,
        prefer_openai=prefer_openai,
    )
    return text or _fallback_generate_employee_bio(name, designation, department, skills, joining_date)


def detect_profile_flags(
    *,
    email: str,
    name: str,
    designation: str,
    department: str,
    contact: str,
    skills: list[str],
    existing_profiles: list[dict[str, str]],
) -> list[str]:
    flags: list[str] = []
    if not designation or not department or not contact or not skills:
        flags.append("Incomplete profile data")
    for profile in existing_profiles:
        if profile["email"].lower() == email.lower():
            flags.append("Potential duplicate email")
        if profile["name"].lower() == name.lower() and profile["department"].lower() == department.lower():
            flags.append("Potential duplicate employee")
    return list(dict.fromkeys(flags))


def _fallback_build_interview_questions(required_skills: list[str], matched_skills: list[str], gaps: list[str]) -> list[str]:
    prompts = [
        f"Tell us about a project where you used {matched_skills[0]} to deliver a measurable outcome."
        if matched_skills
        else "Tell us about the most relevant project in your recent experience."
    ]
    prompts.append(
        f"How would you approach ramping up on {gaps[0]} in your first 30 days?"
        if gaps
        else "How do you prioritize work when requirements are ambiguous?"
    )
    prompts.append("Describe a time you balanced speed and quality under pressure.")
    prompts.append("How do you collaborate with cross-functional stakeholders during delivery?")
    prompts.append(
        f"Which of these skills feels strongest today: {', '.join(required_skills[:3])}?"
        if required_skills
        else "What type of work energizes you most?"
    )
    return prompts[:5]


def _fallback_score_resume(job_description: str, required_skills: list[str], resume_text: str, candidate_skills: list[str]) -> dict[str, object]:
    jd_tokens = set(_tokens(job_description))
    skill_set = {skill.strip().lower() for skill in required_skills if skill.strip()}
    resume_tokens = set(_tokens(resume_text))
    candidate_skill_set = {skill.strip().lower() for skill in candidate_skills if skill.strip()}

    matched_skills = sorted(skill_set & (resume_tokens | candidate_skill_set))
    missing_skills = sorted(skill_set - set(matched_skills))
    coverage = (len(matched_skills) / max(len(skill_set), 1)) * 100
    context_bonus = (len(jd_tokens & resume_tokens) / max(len(jd_tokens), 1)) * 20
    match_percent = min(98, round(coverage * 0.8 + context_bonus, 1))

    top_strengths = matched_skills[:3] or ["Relevant transferable experience", "Clear role alignment", "Resume mentions delivery outcomes"]
    top_gaps = missing_skills[:2] or ["Add more quantified impact", "Highlight domain-specific depth"]
    reasoning = (
        f"The profile matches {len(matched_skills)} of {len(skill_set)} required skills. "
        f"Resume language shows overlap with the job description, leading to a {match_percent}% fit score."
    )
    interview_questions = _fallback_build_interview_questions(required_skills, matched_skills, top_gaps)

    return {
        "match_percent": match_percent,
        "match_reasoning": reasoning,
        "strengths": [strength.replace("-", " ").title() for strength in top_strengths[:3]],
        "gaps": [gap.replace("-", " ").title() for gap in top_gaps[:2]],
        "interview_questions": interview_questions,
    }


def score_resume(
    job_description: str,
    required_skills: list[str],
    resume_text: str,
    candidate_skills: list[str],
    *,
    prefer_openai: bool = True,
) -> dict[str, object]:
    result = _request_json(
        ResumeAnalysis,
        (
            "You are an HR recruiter. Score a candidate against the job details provided. "
            "Return JSON with: match_percent (0-100), match_reasoning, strengths (3 items), gaps (2 items), "
            "interview_questions (5 tailored questions). Use only the information provided."
        ),
        (
            f"Job description:\n{_truncate(job_description, 5000)}\n\n"
            f"Required skills:\n{', '.join(required_skills) if required_skills else 'None provided'}\n\n"
            f"Candidate skills:\n{', '.join(candidate_skills) if candidate_skills else 'None provided'}\n\n"
            f"Resume text:\n{_truncate(resume_text, 9000) or 'No resume text extracted.'}"
        ),
        prefer_openai=prefer_openai,
    )
    if result:
        parsed = ResumeAnalysis.model_validate(result)
        return {
            "match_percent": max(0.0, min(100.0, round(parsed.match_percent, 1))),
            "match_reasoning": _truncate(parsed.match_reasoning, 320),
            "strengths": _normalize_list(parsed.strengths, limit=3),
            "gaps": _normalize_list(parsed.gaps, limit=2),
            "interview_questions": _normalize_list(parsed.interview_questions, limit=5),
        }
    return _fallback_score_resume(job_description, required_skills, resume_text, candidate_skills)


def flag_leave_patterns(leave_dates: list[date]) -> list[str]:
    if not leave_dates:
        return []
    weekday_counts = Counter(day.weekday() for day in leave_dates)
    flags: list[str] = []
    if weekday_counts.get(0, 0) >= 2:
        flags.append("Repeated Monday leave pattern detected")
    if weekday_counts.get(4, 0) >= 2:
        flags.append("Repeated Friday leave pattern detected")
    return flags


def predict_capacity_risk(department: str, overlapping_people: list[str], total_people: int) -> str:
    if total_people <= 0:
        return "No capacity risk signal available."
    ratio = len(overlapping_people) / total_people
    if ratio >= 0.5:
        return f"High risk: {len(overlapping_people)} people from {department} are out during the same window."
    if ratio >= 0.3:
        return f"Moderate risk: coverage for {department} may be tight during these dates."
    return "Low risk: current leave overlap should be manageable."


def _fallback_review_summary(
    *,
    employee_name: str,
    achievements: str,
    challenges: str,
    goals: str,
    self_rating: int,
    ratings: dict[str, int],
    manager_comments: str,
) -> dict[str, object]:
    average_rating = round(mean(ratings.values()), 1)
    mismatches: list[str] = []
    if abs(self_rating - round(average_rating)) >= 2:
        mismatches.append(
            f"Self-rating ({self_rating}/5) differs significantly from manager average ({average_rating}/5)."
        )
    lowest_area = min(ratings, key=ratings.get)
    highest_area = max(ratings, key=ratings.get)
    development_actions = [
        f"Create a 60-day action plan to improve {lowest_area} with weekly manager checkpoints.",
        f"Keep stretching assignments that use strong {highest_area} skills.",
        "Document wins with measurable impact to support the next review cycle.",
    ]
    summary = (
        f"{employee_name} reported achievements around {shorten(achievements)} while noting challenges in {shorten(challenges)}. "
        f"The manager scored overall performance at {average_rating}/5 and highlighted: {shorten(manager_comments)}. "
        f"Next-cycle goals should focus on {shorten(goals)} while strengthening {lowest_area} and sustaining {highest_area}."
    )
    return {
        "summary": summary,
        "mismatches": mismatches,
        "development_actions": development_actions,
    }


def review_summary(
    *,
    employee_name: str,
    achievements: str,
    challenges: str,
    goals: str,
    self_rating: int,
    ratings: dict[str, int],
    manager_comments: str,
    prefer_openai: bool = True,
) -> dict[str, object]:
    result = _request_json(
        ReviewSummaryResult,
        (
            "You are an HR performance review assistant. Compare employee self-review details with manager ratings and comments. "
            "Return JSON with summary, mismatches, and development_actions. Keep the summary balanced and professional."
        ),
        (
            f"Employee: {employee_name}\n"
            f"Achievements: {_truncate(achievements, 3000)}\n"
            f"Challenges: {_truncate(challenges, 3000)}\n"
            f"Goals: {_truncate(goals, 3000)}\n"
            f"Self rating: {self_rating}/5\n"
            f"Manager ratings: {json.dumps(ratings)}\n"
            f"Manager comments: {_truncate(manager_comments, 3000)}"
        ),
        prefer_openai=prefer_openai,
    )
    if result:
        parsed = ReviewSummaryResult.model_validate(result)
        return {
            "summary": _truncate(parsed.summary, 900),
            "mismatches": _normalize_list(parsed.mismatches, limit=3),
            "development_actions": _normalize_list(parsed.development_actions, limit=3),
        }
    return _fallback_review_summary(
        employee_name=employee_name,
        achievements=achievements,
        challenges=challenges,
        goals=goals,
        self_rating=self_rating,
        ratings=ratings,
        manager_comments=manager_comments,
    )


def shorten(text: str, limit: int = 90) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _retrieve_document_context(question: str, documents: list[dict[str, str]]) -> tuple[float, list[dict[str, str | float]]]:
    question_tokens = Counter(_tokens(question))
    candidates: list[dict[str, str | float]] = []

    for document in documents:
        text = document["text"]
        title = document["title"]
        for sentence in _sentences(text):
            sentence_tokens = Counter(_tokens(sentence))
            if not sentence_tokens:
                continue
            overlap = set(question_tokens) & set(sentence_tokens)
            score = sum(question_tokens[token] + sentence_tokens[token] for token in overlap)
            if score == 0:
                continue
            score /= math.sqrt(max(sum(question_tokens.values()) * sum(sentence_tokens.values()), 1))
            candidates.append({"score": score, "title": title, "excerpt": sentence})

    ranked = sorted(candidates, key=lambda item: float(item["score"]), reverse=True)
    best_score = float(ranked[0]["score"]) if ranked else 0.0
    return best_score, ranked[:5]


def answer_from_documents(
    question: str,
    documents: list[dict[str, str]],
    hr_email: str | None = None,
    *,
    prefer_openai: bool = True,
) -> dict[str, str]:
    settings = get_settings()
    contact_email = hr_email or settings.hr_contact_email
    best_score, excerpts = _retrieve_document_context(question, documents)

    if best_score < 0.35 or not excerpts:
        return {
            "answer": f"I could not find that in the uploaded documents. Please contact HR at {contact_email}.",
            "matched_doc_title": "",
        }

    top_excerpt = excerpts[0]
    result = _request_json(
        DocumentAnswerResult,
        (
            "You are an onboarding assistant. Answer ONLY from the supporting excerpts provided. "
            "If the excerpts are not enough, tell the user to contact HR. Return JSON with answer and matched_doc_title."
        ),
        (
            f"Question:\n{question}\n\n"
            f"Supporting excerpts:\n{json.dumps(excerpts, ensure_ascii=False)}\n\n"
            f"HR contact email: {contact_email}"
        ),
        max_output_tokens=500,
        prefer_openai=prefer_openai,
    )
    if result:
        parsed = DocumentAnswerResult.model_validate(result)
        answer_text = _truncate(parsed.answer, 700)
        if contact_email not in answer_text and "could not find" in answer_text.lower():
            answer_text = f"{answer_text.rstrip('.')} Please contact HR at {contact_email}."
        return {
            "answer": answer_text,
            "matched_doc_title": parsed.matched_doc_title or str(top_excerpt["title"]),
        }

    return {
        "answer": f"According to {top_excerpt['title']}: {top_excerpt['excerpt']}",
        "matched_doc_title": str(top_excerpt["title"]),
    }


def _fallback_build_monthly_summary(
    *,
    headcount_by_department: dict[str, int],
    attrition_rate: float,
    open_positions: int,
    leave_utilisation_rate: float,
    leave_flags: list[str],
) -> dict[str, object]:
    largest_department = max(headcount_by_department, key=headcount_by_department.get, default="No department")
    highlights = [
        f"{largest_department} remains the largest team with {headcount_by_department.get(largest_department, 0)} employees.",
        f"There are currently {open_positions} open positions under active hiring.",
    ]
    risks = []
    if attrition_rate > 10:
        risks.append("Attrition is elevated and may require manager-level retention checks.")
    if leave_utilisation_rate > 70:
        risks.append("Leave utilisation is high and could affect near-term capacity.")
    risks.extend(leave_flags[:2])
    recommended_actions = [
        "Review succession plans for teams with the highest leave overlap.",
        "Prioritize filling open roles in delivery-critical departments.",
        "Share manager coaching guidance before the next performance cycle.",
    ]
    summary = (
        f"Monthly HR snapshot: headcount is stable across {len(headcount_by_department)} departments, "
        f"attrition is {attrition_rate:.1f}%, and leave utilisation is {leave_utilisation_rate:.1f}%. "
        f"Immediate attention should stay on open hiring demand and capacity planning."
    )
    return {
        "summary": summary,
        "highlights": highlights,
        "risks": risks,
        "recommended_actions": recommended_actions,
    }


def build_monthly_summary(
    *,
    headcount_by_department: dict[str, int],
    attrition_rate: float,
    open_positions: int,
    leave_utilisation_rate: float,
    leave_flags: list[str],
    prefer_openai: bool = True,
) -> dict[str, object]:
    signature = json.dumps(
        {
            "headcount_by_department": headcount_by_department,
            "attrition_rate": round(attrition_rate, 3),
            "open_positions": open_positions,
            "leave_utilisation_rate": round(leave_utilisation_rate, 3),
            "leave_flags": leave_flags,
        },
        sort_keys=True,
    )

    if prefer_openai and signature in _MONTHLY_SUMMARY_CACHE:
        return _MONTHLY_SUMMARY_CACHE[signature]

    result = _request_json(
        MonthlySummaryResult,
        (
            "You are an HR operations analyst. Create a concise monthly HR summary. "
            "Return JSON with summary, highlights, risks, and recommended_actions. Use only the metrics provided."
        ),
        (
            f"Headcount by department: {json.dumps(headcount_by_department)}\n"
            f"Attrition rate: {attrition_rate:.2f}%\n"
            f"Open positions: {open_positions}\n"
            f"Leave utilisation rate: {leave_utilisation_rate:.2f}%\n"
            f"Leave flags: {json.dumps(leave_flags)}"
        ),
        prefer_openai=prefer_openai,
    )
    if result:
        parsed = MonthlySummaryResult.model_validate(result)
        normalized = {
            "summary": _truncate(parsed.summary, 900),
            "highlights": _normalize_list(parsed.highlights, limit=3),
            "risks": _normalize_list(parsed.risks, limit=3),
            "recommended_actions": _normalize_list(parsed.recommended_actions, limit=3),
        }
        _MONTHLY_SUMMARY_CACHE[signature] = normalized
        return normalized

    return _fallback_build_monthly_summary(
        headcount_by_department=headcount_by_department,
        attrition_rate=attrition_rate,
        open_positions=open_positions,
        leave_utilisation_rate=leave_utilisation_rate,
        leave_flags=leave_flags,
    )
