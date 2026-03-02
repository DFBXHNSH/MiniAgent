"""
Tests for the compression strategies.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from compression.base import separate_system_messages


class TestSeparateSystemMessages:
    """Test cases for separate_system_messages function."""

    def test_separate_system_only(self):
        """Test separating only system messages."""
        messages = [
            {"role": "system", "content": "System 1"},
            {"role": "system", "content": "System 2"}
        ]
        result = separate_system_messages(messages)
        assert len(result) == 2
        assert all(m["role"] == "system" for m in result)

    def test_separate_mixed_messages(self):
        """Test separating system messages from mixed content."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "tool", "content": "Result"},
            {"role": "system", "content": "Another system"}
        ]
        result = separate_system_messages(messages)
        assert len(result) == 2
        assert result[0]["content"] == "System"
        assert result[1]["content"] == "Another system"

    def test_separate_no_system_messages(self):
        """Test separating when no system messages exist."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        result = separate_system_messages(messages)
        assert len(result) == 0

    def test_separate_empty_list(self):
        """Test separating from empty list."""
        result = separate_system_messages([])
        assert result == []


class TestCompressionStrategies:
    """Base tests for compression strategies."""

    def test_sliding_window_preserves_system(self):
        """Test that sliding window preserves system messages."""
        from src.compression.sliding import SlidingWindowCompression

        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "2"},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "3"},
            {"role": "assistant", "content": "A3"},
        ]
        strategy = SlidingWindowCompression()
        result = strategy.compress(messages, max_turns=1)

        # System message should always be preserved
        assert any(m["role"] == "system" for m in result)

    def test_semantic_preserves_system(self):
        """Test that semantic summary preserves system messages."""
        from src.compression.semantic import SemanticSummaryCompression
        from src.llm.client import LLMClient

        # We can't easily test actual LLM calls, but we can verify
        # the structure and that system messages would be preserved
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        # Create a mock client - we just want to verify structure
        client = LLMClient(model="test")
        strategy = SemanticSummaryCompression(client)

        # Not enough messages to compress should return unchanged
        result = strategy.compress(messages, summary_threshold=10)
        assert result == messages
