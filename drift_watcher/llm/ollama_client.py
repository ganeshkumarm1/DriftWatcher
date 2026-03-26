from ollama import Client
import json
from .base import BaseLLMClient

class OllamaClient(BaseLLMClient):
    def __init__(self, model="qwen2.5:latest", base_url="http://localhost:11434", **kwargs):
        """Initialize Ollama client.
        
        Args:
            model: Model name (e.g., "qwen2.5:latest")
            base_url: Ollama server URL
            **kwargs: Additional arguments (for backward compatibility)
        """
        self.model = model
        self.base_url = base_url
        self.client = Client(host=base_url)

    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"
    
    def invoke(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> dict:
        """Invoke Ollama and return parsed JSON response."""
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            options={
                "temperature": temperature,
                "num_ctx": max_tokens
            }
        )
        
        # Extract response text from GenerateResponse object
        response_text = response['response'] if isinstance(response, dict) else response.response
        
        # Try to extract JSON from response (handle reasoning models that add text)
        try:
            # First try direct parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response (look for {...})
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            print(f"⚠️ Failed to parse JSON from response: {response_text[:200]}")
            raise ValueError(f"Invalid JSON response from LLM. Response: {response_text[:500]}")