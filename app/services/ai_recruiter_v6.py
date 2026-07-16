from __future__ import annotations

import re
from collections import Counter
from typing import Any


STOPWORDS = {
    "and", "the", "with", "for", "that", "this", "from", "are", "was",
    "were", "have", "has", "will", "your", "you", "our", "their", "they",
    "into", "using", "a", "an", "of", "to", "in", "on", "at", "as", "or",
    "be", "is", "it",
}


def _words(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())
    return [word for word in raw if word not in STOPWORDS and len(word) > 2]


def _keywords(text: str, limit: int) -> list[str]:
    return [word for word, _ in Counter(_words(text)).most_common(limit)]


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return "" if value is None else str(value)


def job_match(cv_content: dict[str, Any], job_description: str) -> dict[str, Any]:
    cv_words = set(_words(_flatten(cv_content)))
    keywords = _keywords(job_description, 40)

    matched = [word for word in keywords if word in cv_words]
    missing = [word for word in keywords if word not in cv_words]

    return {
        "score": int((len(matched) / max(len(keywords), 1)) * 100),
        "strengths": matched[:15],
        "missing_keywords": missing[:20],
        "recommendations": [
            "Use missing keywords only where they truthfully reflect verified skills or experience.",
            "Add measurable evidence for your strongest matched requirements.",
            "Tailor the professional summary to the role.",
        ],
    }


def cover_letter(
    candidate_name: str,
    target_role: str,
    company_name: str,
    verified_strengths: list[str],
    verified_experience: list[str],
) -> str:
    paragraphs = [
        "Dear Hiring Manager,",
        f"I am applying for the {target_role} opportunity at {company_name}.",
    ]

    strengths = [item.strip() for item in verified_strengths[:5] if item.strip()]
    if strengths:
        paragraphs.append(
            "My verified strengths include " + ", ".join(strengths) + "."
        )

    experience = [
        item.strip().rstrip(".") + "."
        for item in verified_experience[:4]
        if item.strip()
    ]
    if experience:
        paragraphs.append(" ".join(experience))

    paragraphs.extend(
        [
            f"I would welcome the opportunity to discuss how my background can contribute to {company_name}.",
            f"Kind regards,\n{candidate_name}",
        ]
    )

    return "\n\n".join(paragraphs)


def interview_questions(
    target_role: str,
    job_description: str,
    candidate_strengths: list[str],
) -> list[dict[str, str]]:
    strength = (
        candidate_strengths[0]
        if candidate_strengths
        else "a relevant professional strength"
    )

    questions = [
        {
            "question": f"Tell us about yourself and why you want the {target_role} role.",
            "guidance": "Connect verified experience and strengths to the role.",
        },
        {
            "question": f"Describe a situation where you demonstrated {strength}.",
            "guidance": "Use the Situation, Task, Action, Result structure.",
        },
    ]

    for keyword in _keywords(job_description, 6):
        questions.append(
            {
                "question": f"How have you applied {keyword}?",
                "guidance": "Give one specific and verified example.",
            }
        )

    return questions


def skills_gap(
    current_skills: list[str],
    job_description: str,
) -> dict[str, list[str]]:
    current = {item.strip().lower() for item in current_skills}
    required = _keywords(job_description, 30)

    matched = [skill for skill in required if skill.lower() in current]
    missing = [skill for skill in required if skill.lower() not in current]

    return {
        "matched_skills": matched,
        "missing_skills": missing[:20],
        "next_steps": [
            f"Build evidence for {skill} through a course, project, internship, or verified work task."
            for skill in missing[:5]
        ],
    }


def career_roadmap(
    current_role: str | None,
    target_role: str,
    qualifications: list[str],
    skills: list[str],
) -> dict[str, Any]:
    return {
        "current_position": current_role or "Not specified",
        "target_role": target_role,
        "foundation": {
            "qualifications": qualifications,
            "skills": skills,
        },
        "roadmap": [
            "Review ten current job descriptions for the target role.",
            "Identify the five most repeated requirements.",
            "Map each requirement to verified evidence.",
            "Build practical evidence for the two highest-priority gaps.",
            "Update the CV and LinkedIn profile.",
            "Apply consistently and track outcomes.",
        ],
    }
