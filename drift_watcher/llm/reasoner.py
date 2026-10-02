# @steered SNARE-1 2026-09-18
import json
from .base import BaseLLMClient


class LLMReasoner:
    """Handles LLM-based reasoning for focus state assessment."""

    FOCUS_ASSESSMENT_PROMPT = """You are Drift Watcher, a personal focus monitoring assistant.

## Step 1 — Establish work context
The user's stated goal is: "{goal}"

If you have access to Taskei, builder-mcp, or internal wiki tools, call them now to list the user's currently assigned or in-progress tasks. Use that task list as the primary reference for what counts as relevant work. If tools are unavailable, use the goal text alone.

## Step 2 — Evaluate browser activity
Total window: {total_minutes} minutes

{pages}

For each page:
- Compute its weight = duration_min / {total_minutes}
- A page with scroll=0 and keys=0 was likely a background tab — reduce its weight by 50%
- For type:video, scroll=0 is normal — use keys and duration instead to judge engagement
- For type:wiki_internal or type:docs, scroll=0 with duration > 1min means the user likely was not actively reading — reduce weight
- Judge whether the content is relevant to the goal or any in-progress task from Step 1

## Step 3 — Classify
- FOCUSED: Weighted relevant time >= weighted irrelevant time
- DRIFTING: Weighted irrelevant time > weighted relevant time
- Relevant = directly related to the goal or an in-progress task (includes docs, tutorials, internal tools on that topic)
- Irrelevant = entertainment, social media, or work content unrelated to the current goal/tasks
- If content is ambiguous but clearly work-adjacent (internal tools, engineering docs on a different topic), mark it irrelevant — the goal is current focus, not general productivity

## Step 4 — Return JSON only, no other text
{{
  "state": "FOCUSED or DRIFTING",
  "confidence": 0.0,
  "reason": "One sentence written directly to the user explaining what they were doing and why it is focused or drifting. Example: 'You spent 6 of 8 minutes on a YouTube video unrelated to your goal.'",
  "relevant_percent": 0.0,
  "irrelevant_percent": 0.0
}}

relevant_percent and irrelevant_percent must sum to 100.
confidence is how certain you are of the classification: 0.0 = very uncertain, 1.0 = completely certain based on clear evidence."""

    def __init__(self, client: BaseLLMClient):
        if client is None:
            raise ValueError("LLM client is required")
        self.client = client

    def assess_focus_state(self, goal: str, activity_summary: dict) -> dict:
        """Single LLM call to assess focus state and relevance breakdown."""
        pages = activity_summary.get("pages", [])
        total_minutes = activity_summary.get("total_minutes", 1.0)

        pages_text = "\n".join(
            f"- [{p['duration_min']}min, scroll:{p.get('scroll_count', 0)}, keys:{p.get('key_count', 0)}, type:{p.get('page_type', 'webpage')}]"
            f" {p['title']} ({p['url']})"
            + (f"\n  Content: {p['content'][:400]}" if p.get("content") else "")
            for p in pages
        )

        prompt = self.FOCUS_ASSESSMENT_PROMPT.format(
            goal=goal,
            total_minutes=round(total_minutes, 1),
            pages=pages_text or "No pages visited"
        )

        result = self.client.invoke(prompt, max_tokens=500)

        result.setdefault("state", "FOCUSED")
        result.setdefault("confidence", 0.5)
        result.setdefault("reason", "")
        result.setdefault("relevant_percent", 0.0)
        result.setdefault("irrelevant_percent", 0.0)

        return result
