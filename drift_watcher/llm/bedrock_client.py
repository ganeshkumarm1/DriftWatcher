import boto3
import json
from .base import BaseLLMClient


class BedrockClient(BaseLLMClient):
    """AWS Bedrock client wrapper for LLM interactions."""
    
    def __init__(self, model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1"):
        self.model_id = model_id
        self.region_name = region_name
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name
        )
    
    @property
    def name(self) -> str:
        return f"AWS Bedrock ({self.model_id})"
    
    def invoke(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> dict:
        """Invoke the LLM with a prompt and return parsed JSON response."""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        
        raw = json.loads(response["body"].read())
        text = raw["content"][0]["text"]
        
        return json.loads(text)
