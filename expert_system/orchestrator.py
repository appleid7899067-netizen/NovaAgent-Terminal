import logging
import os

import requests
from .schemas import CodeReview

logger = logging.getLogger(__name__)


class ExpertOrchestrator:
    def __init__(self):
        self.base_url = os.environ.get("EXPERT_UPSTREAM_URL", "http://127.0.0.1:8741/v1").rstrip("/")
        self.api_key = os.environ.get("EXPERT_UPSTREAM_API_KEY", "")
        self.timeout = float(os.environ.get("EXPERT_UPSTREAM_TIMEOUT", "60"))
        self.coding_blueprint = (
            "You are 'Codex-Engineer', an elite Senior Software Engineer. "
            "You MUST respond ONLY with valid JSON. No markdown, no backticks, no explanation outside JSON. "
            "The JSON must follow this exact schema:\n"
            "{\n"
            '  "has_bugs": true/false,\n'
            '  "security_issues": ["issue1", "issue2"],\n'
            '  "performance_issues": ["issue1"],\n'
            '  "refactored_code": "the improved code as a single string",\n'
            '  "reasoning": "the concise reasoning"\n'
            "}\n"
            "Analyze the code for bugs, security (OWASP Top 10), and performance. Then output the JSON."
        )

    def review_code(self, code_snippet: str, language: str = "python") -> CodeReview:
        prompt = f"Language: {language}\n\nCode to review:\n```{language}\n{code_snippet}\n```"
        payload = {
            "model": os.environ.get("EXPERT_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": self.coding_blueprint},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("Expert upstream request failed: %s", type(exc).__name__)
            raise RuntimeError("expert upstream unavailable") from exc

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        try:
            return CodeReview.model_validate_json(content.strip())
        except (ValueError, TypeError) as exc:
            logger.warning("Expert upstream returned invalid review payload")
            raise RuntimeError("invalid expert response") from exc
