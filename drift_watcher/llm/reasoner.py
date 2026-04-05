import json
from .base import BaseLLMClient


class LLMReasoner:
    """Handles LLM-based reasoning for focus state assessment."""

    FOCUS_ASSESSMENT_PROMPT = """You are Drift Watcher, a personal focus monitoring system.

Goal: "{goal}"

Recent browser activity:
{pages}

For each page, decide if it is relevant to the goal.
Then give an overall FOCUSED or DRIFTING state based on time-weighted relevance.

Rules:
- FOCUSED: Most time spent on content directly related to the goal
- DRIFTING: Most time spent on unrelated content
- Educational content (tutorials, docs, articles) counts as relevant if topic relates to goal
- Entertainment (unrelated videos, social media, news) = irrelevant
- When in doubt about relevance, lean towards irrelevant

Return JSON only:
{{
  "state": "FOCUSED | DRIFTING",
  "confidence": 0.0,
  "reason": "brief explanation",
  "relevant_percent": 0.0,
  "irrelevant_percent": 0.0
}}"""

    def __init__(self, client: BaseLLMClient):
        if client is None:
            raise ValueError("LLM client is required")
        self.client = client

    def assess_focus_state(self, goal: str, activity_summary: dict) -> dict:
        """Single LLM call to assess focus state and relevance breakdown."""
        pages = activity_summary.get("pages", [])
        pages_text = "\n".join(
            f"- [{p['duration_min']}min] {p['title']} ({p['url']})"
            + (f"\n  Content: {p['content'][:150]}" if p.get("content") else "")
            for p in pages
        )

        prompt = self.FOCUS_ASSESSMENT_PROMPT.format(
            goal=goal,
            pages=pages_text or "No pages visited"
        )

        result = self.client.invoke(prompt, max_tokens=500)

        # Ensure required fields exist
        result.setdefault("state", "FOCUSED")
        result.setdefault("confidence", 0.5)
        result.setdefault("reason", "")
        result.setdefault("relevant_percent", 0.0)
        result.setdefault("irrelevant_percent", 0.0)

        return result
