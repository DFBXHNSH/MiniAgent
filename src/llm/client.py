"""
LLM client for making API calls.

This module wraps litellm completion with agent-specific configuration.
"""

from typing import List, Dict, Any, Optional
from litellm import completion
from litellm.exceptions import APIError, Timeout, RateLimitError

# Import the shared message formatting utility
# We import here to avoid circular imports (llm.client -> messages.builder -> llm.client)
# The format_messages_for_display is a module-level function, safe to import
from messages.builder import format_messages_for_display


class LLMClient:
    """
    Client for interacting with LLM via litellm.
    """

    def __init__(
        self,
        model: str = "dashscope/qwen-turbo",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize the LLM client.

        Args:
            model: The model to use
            temperature: Sampling temperature
            max_tokens: Optional max tokens limit
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def call(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Make a completion call to the LLM.

        Args:
            messages: The messages to send
            tools: Optional tool definitions

        Returns:
            The response message from the LLM
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        if tools:
            kwargs["tools"] = tools

        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        response = completion(**kwargs)
        return response.choices[0].message

    def generate_summary(
        self,
        messages: List[Dict[str, Any]],
        max_length: int
    ) -> str:
        """
        Generate a summary of the given messages.

        Args:
            messages: Messages to summarize
            max_length: Maximum length of the summary

        Returns:
            The generated summary, or fallback message on failure
        """
        prompt = (
            f"Please summarize the following conversation history, preserving key information:\n"
            f"- User's main requests\n"
            f"- Tool calls executed and results (important results must be preserved)\n"
            f"- Completed task status\n\n"
            f"Conversation history:\n"
            f"{self._format_messages(messages)}\n\n"
            f"Provide a concise English summary within {max_length} characters."
        )

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content or ""
        except (APIError, Timeout, RateLimitError) as e:
            return f"[Summary generation failed ({type(e).__name__}: {e}), keeping recent messages]"
        except Exception as e:
            return f"[Summary generation failed ({type(e).__name__}), keeping recent messages]"

    @staticmethod
    def _format_messages(messages: List[Dict[str, Any]]) -> str:
        """Format messages for summary prompt."""
        return format_messages_for_display(messages, max_content_length=500)
