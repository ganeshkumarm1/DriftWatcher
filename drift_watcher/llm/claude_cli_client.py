# @steered SNARE-1 2026-09-18
import json
import re
import shutil
import subprocess

from .base import BaseLLMClient


class ClaudeCliClient(BaseLLMClient):
    """LLM client that shells out to a locally installed `claude` CLI (print mode).

    Uses the user's existing Claude Code login — no API key or Bedrock config in
    this repo. By default allows all MCP tools (mcp__*) so internal tools like
    Taskei and wiki are available for org-context classification.
    """

    def __init__(self, model="claude-haiku-4-5-20251001", timeout_seconds=45,
                 allowed_tools="mcp__*", **kwargs):
        self._check_binary()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.allowed_tools = allowed_tools

    def _check_binary(self):
        if not shutil.which("claude"):
            raise RuntimeError(
                "claude CLI not found on PATH. Install Claude Code: https://claude.ai/code"
            )

    @property
    def name(self) -> str:
        return f"Claude CLI ({self.model})"

    def invoke(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> dict:
        tools = self.allowed_tools if self.allowed_tools else "mcp__*"
        cmd = [
            "claude", "-p", prompt,
            "--allowedTools", tools,
            "--model", self.model,
            "--output-format", "json",
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=self.timeout_seconds
        )
        if proc.returncode != 0:
            raise RuntimeError(f"claude CLI failed: {proc.stderr.strip()[:300]}")

        envelope = json.loads(proc.stdout)      # Claude Code JSON envelope
        text = envelope.get("result", "")       # model's text output

        # Strip ```json fences if present, then parse the classification JSON.
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Invalid JSON from claude CLI. Output: {text[:500]}")
