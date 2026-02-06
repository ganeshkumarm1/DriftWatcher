"""
Example: Adding a Custom LLM Provider

This example shows how to create a custom LLM provider for Drift Watcher.
You can use this to integrate any LLM API (OpenAI, Anthropic, Ollama, etc.)
"""

import json
from drift_watcher.llm.base import BaseLLMClient


class CustomLLMClient(BaseLLMClient):
    """Example custom LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        """
        Initialize your custom client.
        
        Args:
            api_key: Your API key
            model: Model identifier
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        self.model = model
        # Add any other initialization here
    
    @property
    def name(self) -> str:
        """Return a display name for your provider."""
        return f"Custom Provider ({self.model})"
    
    def invoke(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> dict:
        """
        Invoke the LLM with a prompt and return parsed JSON response.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            dict: Parsed JSON response from the LLM
            
        Example response format:
            {
                "state": "ALIGNED",
                "confidence": 0.85,
                "reason": "User is coding"
            }
        """
        # Example: OpenAI-style API call
        import requests
        
        response = requests.post(
            "https://api.example.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract and parse the JSON response
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)


# Usage example
if __name__ == "__main__":
    from drift_watcher.llm import LLMReasoner
    
    # Create your custom client
    client = CustomLLMClient(
        api_key="your-api-key-here",
        model="gpt-4"
    )
    
    # Use it with the reasoner
    reasoner = LLMReasoner(client=client)
    
    # Test it
    activity_summary = {
        "breakdown": "BROWSING: 80%, IMPLEMENTATION: 20%",
        "sample_titles": ["YouTube - Cat Videos", "GitHub - Project"],
        "sample_content": ["Funny cat compilation", "Pull request review"]
    }
    
    result = reasoner.assess_focus_state(
        goal="Learn Python programming",
        activity_summary=activity_summary
    )
    
    print(f"State: {result['state']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reason: {result['reason']}")
