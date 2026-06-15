"""LLM client for structured document extraction."""

from __future__ import annotations

import json
import re
from typing import Any

import requests
from openai import OpenAI

from backend.core.config import get_settings

SYSTEM_PROMPT = """You are VisionDoc AI, an information extraction engine.
Analyze OCR text and return ONLY valid JSON with this exact schema:
{
  "document_type": "invoice|receipt|form|bank_statement|contract|id_document|unknown",
  "fields": {
    "vendor_or_issuer": null,
    "customer_or_recipient": null,
    "document_number": null,
    "date": null,
    "due_date": null,
    "subtotal": null,
    "tax": null,
    "total": null,
    "currency": null,
    "line_items": [],
    "summary": null
  }
}
Rules:
- Use null when a value is missing or uncertain.
- Do not invent values.
- Normalize currency amounts as numbers when possible.
- Keep line_items as an array of objects when itemized rows are visible.
- Return JSON only; no markdown, commentary, or code fences.
"""


class LLMClient:
    """Unified local/OAI client used by the document extraction pipeline."""

    def __init__(self) -> None:
        self.cfg = get_settings()
        self.provider = self.cfg.llm_provider.lower().strip()

    def analyze(self, raw_text: str) -> dict[str, Any]:
        """Analyze OCR text and return parsed structured JSON."""
        prompt = f"OCR TEXT:\n{raw_text[:12000]}\n\nReturn structured JSON only."
        if self.provider == "openai":
            content = self._openai(prompt)
        elif self.provider == "ollama":
            content = self._ollama(prompt)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")
        return self._parse_json(content)

    def _ollama(self, prompt: str) -> str:
        url = f"{self.cfg.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.cfg.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    def _openai(self, prompt: str) -> str:
        if not self.cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        client = OpenAI(api_key=self.cfg.openai_api_key)
        response = client.chat.completions.create(
            model=self.cfg.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1500,
        )
        return response.choices[0].message.content or "{}"

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                return {"document_type": "unknown", "fields": {"summary": cleaned[:500]}}
            parsed = json.loads(match.group(0))

        if "fields" not in parsed or not isinstance(parsed["fields"], dict):
            parsed["fields"] = {}
        parsed.setdefault("document_type", "unknown")
        return parsed
