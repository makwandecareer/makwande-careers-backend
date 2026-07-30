from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


class AIProvider:
    """
    Central AI provider abstraction.

    Configure:
        OPENAI_API_KEY
        OPENAI_MODEL (optional)
    """

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 1200,
    ) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        text = getattr(response, "output_text", "")
        usage = getattr(response, "usage", None)

        return {
            "text": text,
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
            "model": self.model,
        }
