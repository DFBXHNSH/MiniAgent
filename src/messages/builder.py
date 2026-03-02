"""
Message building and management utilities.

This module handles the construction and formatting of messages for LLM interaction.
"""

from typing import List, Dict, Any, Optional, Union


def _extract_message_content(content: Any) -> str:
    """
    Extract text content from a message's content field.

    Handles various content formats:
    - List of dict with type/text (multimodal format)
    - Plain string
    - None (returns empty string)

    Args:
        content: The content field from a message

    Returns:
        Extracted text content as a string
    """
    if content is None:
        return ""

    if isinstance(content, list):
        # Handle multimodal content: [{"type": "text", "text": "..."}]
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(text_parts)

    if isinstance(content, str):
        return content

    # Handle other types by converting to string
    return str(content)


def format_messages_for_display(
    messages: List[Dict[str, Any]],
    max_content_length: int = 500
) -> str:
    """
    Format messages for display (e.g., in summary prompts).

    This is a shared utility function to avoid code duplication between
    MessageBuilder.format_for_summary() and LLMClient._format_messages().

    Args:
        messages: The messages to format
        max_content_length: Maximum length of content per message

    Returns:
        A formatted string with "role: content" format, one per line
    """
    result = []
    for msg in messages:
        role = msg.get("role", "")
        content = _extract_message_content(msg.get("content"))

        if content:
            truncated = content[:max_content_length]
            result.append(f"{role}: {truncated}")

    return "\n".join(result)


class MessageBuilder:
    """
    Builder for constructing messages for LLM interaction.
    """

    @staticmethod
    def build_copy(
        messages: List[Dict[str, Any]],
        user_input: str,
        first_call: bool,
        initial_reminder: str
    ) -> List[Dict[str, Any]]:
        """
        Build a copy of messages with the new user input added.

        Args:
            messages: The current message history
            user_input: The user's message to add
            first_call: Whether this is the first call
            initial_reminder: The initial reminder to include on first call

        Returns:
            A new list of messages ready for LLM processing
        """
        messages = messages.copy()

        if first_call:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": initial_reminder},
                    {"type": "text", "text": user_input}
                ]
            })
        else:
            messages.append({"role": "user", "content": user_input})

        return messages

    @staticmethod
    def format_for_summary(messages: List[Dict[str, Any]]) -> str:
        """
        Format messages for use in a summary prompt.

        Args:
            messages: Messages to format

        Returns:
            A formatted string of messages
        """
        return format_messages_for_display(messages, max_content_length=500)

    @staticmethod
    def get_message_count(messages: List[Dict[str, Any]]) -> int:
        """
        Get the count of non-system messages.

        Args:
            messages: The message history

        Returns:
            The number of user, assistant, and tool messages
        """
        return len([m for m in messages if m["role"] in ("user", "assistant", "tool")])

    @staticmethod
    def extract_conversation_turns(messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Extract conversation turns from the message history.

        A turn consists of: user message + assistant response (may include tool_calls) + tool results.

        Args:
            messages: The message history

        Returns:
            A list of turns, where each turn is a list of messages
        """
        turns: List[List[Dict[str, Any]]] = []
        current_turn: List[Dict[str, Any]] = []

        for msg in messages:
            if msg["role"] in ("user", "assistant", "tool"):
                current_turn.append(msg)
                # End of turn: assistant response without tool_calls
                if msg["role"] == "assistant" and not msg.get("tool_calls"):
                    turns.append(current_turn)
                    current_turn = []

        # Don't forget the last (potentially incomplete) turn
        if current_turn:
            turns.append(current_turn)

        return turns

    @staticmethod
    def extract_response_text(response_message: Any) -> str:
        """
        Extract the text content from the LLM response message.

        Args:
            response_message: The response message from the LLM

        Returns:
            The text content, or empty string if not available
        """
        if hasattr(response_message, 'content') and response_message.content:
            return response_message.content
        return ""
