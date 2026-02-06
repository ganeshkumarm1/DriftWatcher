import json
from .base import BaseLLMClient
from .bedrock_client import BedrockClient


class LLMReasoner:
    """Handles LLM-based reasoning for focus state and activity classification."""
    
    ALLOWED_CATEGORIES = [
        "IMPLEMENTATION",
        "DEBUGGING",
        "READING_DOCUMENTATION",
        "PLANNING",
        "COMMUNICATION",
        "BROWSING",
        "OTHER"
    ]
    
    STATE_ASSESSMENT_PROMPT = """You are helping Drift Watcher, a personal focus monitoring system.

Current goal:
"{goal}"

Recent activity:
- Breakdown: {breakdown}
- Sample page titles: {sample_titles}
- Sample page content: {sample_content}

Choose ONE state:
- FOCUSED: Working on or learning about the goal
- DRIFTING: Off-topic or entertainment

Rules:
- Page titles AND content are strong indicators
- Entertainment sites (YouTube, Reddit, social media) = DRIFTING
- Documentation, learning, implementation related to goal = FOCUSED
- Use content to disambiguate unclear titles

Return JSON only:
{{
  "state": "FOCUSED | DRIFTING",
  "confidence": 0.0,
  "reason": "short explanation"
}}"""

    ACTIVITY_CLASSIFICATION_PROMPT = """You are classifying browser activity for Drift Watcher, a personal focus monitoring system.

Choose ONE category from:
{categories}

Rules:
- Base your judgment on title, URL, content, and interaction patterns.
- Content provides context for ambiguous titles
- Do NOT invent information.
- Use OTHER if unsure.
- Return JSON only.

Activity slice:
{activity_slice}

Return:
{{ "category": "<one of the allowed categories>" }}"""
    
    def __init__(self, client: BaseLLMClient = None):
        """
        Initialize reasoner with an LLM client.
        
        Args:
            client: LLM client instance. If None, uses default Bedrock client.
        """
        self.client = client or BedrockClient()
    
    def assess_focus_state(self, goal, activity_summary):
        """Assess the current focus state based on goal and activity."""
        prompt = self.STATE_ASSESSMENT_PROMPT.format(
            goal=goal,
            breakdown=activity_summary.get("breakdown"),
            sample_titles=activity_summary.get("sample_titles"),
            sample_content=activity_summary.get("sample_content", [])
        )
        return self.client.invoke(prompt, max_tokens=100)
    
    def classify_activity(self, activity_slice):
        """Classify a single activity slice."""
        prompt = self.ACTIVITY_CLASSIFICATION_PROMPT.format(
            categories=", ".join(self.ALLOWED_CATEGORIES),
            activity_slice=json.dumps(activity_slice, indent=2)
        )
        response = self.client.invoke(prompt)
        category = response.get("category", "OTHER")
        
        if category not in self.ALLOWED_CATEGORIES:
            category = "OTHER"
        
        return category
