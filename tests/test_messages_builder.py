"""
Tests for the MessageBuilder module.
"""

import pytest
from src.messages.builder import (
    MessageBuilder,
    _extract_message_content,
    format_messages_for_display
)


class TestExtractMessageContent:
    """Test cases for _extract_message_content function."""

    def test_extract_string_content(self):
        """Test extracting plain string content."""
        result = _extract_message_content("Hello, world!")
        assert result == "Hello, world!"

    def test_extract_none_content(self):
        """Test extracting None content."""
        result = _extract_message_content(None)
        assert result == ""

    def test_extract_multimodal_content(self):
        """Test extracting content from multimodal format."""
        content = [
            {"type": "text", "text": "First line"},
            {"type": "text", "text": "Second line"}
        ]
        result = _extract_message_content(content)
        assert result == "First line\nSecond line"

    def test_extract_multimodal_filters_non_text(self):
        """Test that non-text items are filtered out."""
        content = [
            {"type": "text", "text": "Text content"},
            {"type": "image_url", "url": "https://example.com/image.png"}
        ]
        result = _extract_message_content(content)
        assert result == "Text content"

    def test_extract_empty_list(self):
        """Test extracting from empty list."""
        result = _extract_message_content([])
        assert result == ""

    def test_extract_other_type(self):
        """Test extracting from non-string, non-list types."""
        result = _extract_message_content(123)
        assert result == "123"


class TestFormatMessagesForDisplay:
    """Test cases for format_messages_for_display function."""

    def test_format_simple_messages(self):
        """Test formatting simple messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        result = format_messages_for_display(messages)
        assert "user: Hello" in result
        assert "assistant: Hi there" in result

    def test_format_with_multimodal(self):
        """Test formatting messages with multimodal content."""
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Query"}]
            }
        ]
        result = format_messages_for_display(messages)
        assert "user: Query" in result

    def test_format_truncates_long_content(self):
        """Test that long content is truncated."""
        messages = [
            {"role": "user", "content": "a" * 1000}
        ]
        result = format_messages_for_display(messages, max_content_length=50)
        assert len(result) < 100
        assert "user: " + "a" * 50 in result

    def test_format_skips_empty_content(self):
        """Test that messages with empty content are skipped."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "World"}
        ]
        result = format_messages_for_display(messages)
        assert "Hello" in result
        assert "World" in result

    def test_format_none_content(self):
        """Test formatting messages with None content."""
        messages = [
            {"role": "user", "content": None}
        ]
        result = format_messages_for_display(messages)
        assert result == ""


class TestMessageBuilder:
    """Test cases for MessageBuilder class."""

    def test_build_copy_first_call(self):
        """Test building copy on first call."""
        messages = [{"role": "system", "content": "System prompt"}]
        result = MessageBuilder.build_copy(
            messages, "Hello", True, "Use tools"
        )
        assert len(result) == 2
        assert result[1]["role"] == "user"
        assert isinstance(result[1]["content"], list)

    def test_build_copy_subsequent_call(self):
        """Test building copy on subsequent call."""
        messages = [{"role": "system", "content": "System prompt"}]
        result = MessageBuilder.build_copy(
            messages, "Hello", False, "Use tools"
        )
        assert len(result) == 2
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Hello"

    def test_build_copy_does_not_modify_original(self):
        """Test that build_copy does not modify original messages."""
        original = [{"role": "system", "content": "System"}]
        result = MessageBuilder.build_copy(original, "Hello", False, "Reminder")
        assert len(result) == 2
        assert len(original) == 1  # Original unchanged

    def test_get_message_count(self):
        """Test counting non-system messages."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "tool", "content": "Result"},
            {"role": "system", "content": "Another system"}
        ]
        count = MessageBuilder.get_message_count(messages)
        assert count == 3  # user, assistant, tool

    def test_format_for_summary(self):
        """Test format_for_summary method."""
        messages = [
            {"role": "user", "content": "Request"},
            {"role": "assistant", "content": "Response"}
        ]
        result = MessageBuilder.format_for_summary(messages)
        assert "user: Request" in result
        assert "assistant: Response" in result

    def test_extract_conversation_turns(self):
        """Test extracting conversation turns."""
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Second"},
            {"role": "assistant", "tool_calls": [{"id": "1"}], "content": ""},
            {"role": "tool", "tool_call_id": "1", "content": "Result"},
            {"role": "assistant", "content": "Final answer"}
        ]
        turns = MessageBuilder.extract_conversation_turns(messages)
        assert len(turns) == 2
        assert turns[0][0]["content"] == "First"
        assert turns[1][0]["content"] == "Second"

    def test_extract_response_text(self):
        """Test extracting response text."""
        class MockResponse:
            content = "Response text"

        response = MockResponse()
        result = MessageBuilder.extract_response_text(response)
        assert result == "Response text"

    def test_extract_response_text_no_content(self):
        """Test extracting response when content is None."""
        class MockResponse:
            content = None

        response = MockResponse()
        result = MessageBuilder.extract_response_text(response)
        assert result == ""
