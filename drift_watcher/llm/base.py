from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def invoke(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Invoke the LLM with a prompt and return parsed JSON response.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON response as dictionary
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this LLM provider."""
        pass
