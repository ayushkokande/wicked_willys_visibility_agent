"""LLM Client wrapper for OpenAI and Anthropic integration."""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient:
    """
    Unified LLM client supporting OpenAI and Anthropic.
    """
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            provider: "openai" or "anthropic"
            model: Model name (defaults to gpt-4o for OpenAI, claude-3-5-sonnet for Anthropic)
        """
        self.provider = provider.lower()
        self.client = None
        self.model = model
        
        if self.provider == "openai":
            self._init_openai(model)
        elif self.provider == "anthropic":
            self._init_anthropic(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")
    
    def _init_openai(self, model: Optional[str] = None):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4o"
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def _init_anthropic(self, model: Optional[str] = None):
        """Initialize Anthropic client."""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: int = 4096) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Assistant response text
        """
        if self.provider == "openai":
            return self._chat_openai(messages, system_prompt, temperature, max_tokens)
        else:
            return self._chat_anthropic(messages, system_prompt, temperature, max_tokens)
    
    def _chat_openai(self, messages: List[Dict[str, str]], 
                     system_prompt: Optional[str],
                     temperature: float,
                     max_tokens: int) -> str:
        """OpenAI chat completion."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def _chat_anthropic(self, messages: List[Dict[str, str]], 
                        system_prompt: Optional[str],
                        temperature: float,
                        max_tokens: int) -> str:
        """Anthropic chat completion."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=messages
        )
        return response.content[0].text
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Simple text generation from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, system_prompt=system_prompt, **kwargs)


# Convenience function for quick LLM calls
def get_llm_client(provider: str = "openai") -> LLMClient:
    """Get an LLM client instance."""
    return LLMClient(provider=provider)
