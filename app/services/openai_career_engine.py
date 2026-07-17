from __future__ import annotations

import json
import os
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CareerEngineError(RuntimeError):
    pass


class OpenAICareerEngine:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise CareerEngineError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6")

    def structured(
        self,
        *,
        schema: type[T],
        task: str,
        profile_bundle: dict,
        request_data: dict,
    ) -> T:
        system_prompt = """
You are Makwande Careers AI Career Engine.

Your role is to produce accurate, practical and ethical career-development
outputs using only the candidate information supplied.

Rules:
- Never invent qualifications, employers, dates, achievements or metrics.
- Clearly distinguish recommendations from verified candidate facts.
- Use professional South African and global recruitment standards.
- Optimise for ATS readability without keyword stuffing.
- Avoid discriminatory assumptions.
- Produce actionable, concise and evidence-based guidance.
- Where evidence is missing, recommend what the candidate should collect.
"""

        input_payload = {
            "task": task,
            "candidate_source_of_truth": profile_bundle,
            "request": request_data,
        }

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            input_payload,
                            ensure_ascii=False,
                            default=str,
                        ),
                    },
                ],
                text_format=schema,
            )
        except Exception as exc:
            raise CareerEngineError(f"OpenAI request failed: {exc}") from exc

        if response.output_parsed is None:
            raise CareerEngineError("OpenAI returned no structured result")

        return response.output_parsed
