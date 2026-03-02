"""
Sliding window compression strategy.

This strategy keeps only the most recent N turns.
"""

from typing import List, Dict, Any

from src.compression.base import CompressionStrategy, separate_system_messages
from src.messages.builder import MessageBuilder


class SlidingWindowCompression(CompressionStrategy):
    """
    Sliding window compression: keep only the most recent max_turns turns.

    System messages are always preserved.
    A turn consists of: user message + assistant response + tool results.
    """

    def compress(
        self,
        messages: List[Dict[str, Any]],
        max_turns: int = 10,
        verbose: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Compress messages using sliding window.

        Args:
            messages: The current message history
            max_turns: Number of recent turns to keep
            verbose: If True, print compression details
            **kwargs: Ignored additional parameters

        Returns:
            The compressed message history
        """
        if verbose:
            print(f"[SlidingWindow] Original messages: {len(messages)}")

        # Always preserve system messages
        system_messages = separate_system_messages(messages)

        # Extract conversation turns
        turns = MessageBuilder.extract_conversation_turns(messages)
        if verbose:
            print(f"[SlidingWindow] Extracted turns: {len(turns)}")

        # Keep only the most recent max_turns turns
        recent_turns = turns[-max_turns:] if len(turns) > max_turns else turns
        turns_dropped = len(turns) - len(recent_turns)

        # Rebuild history: system messages + recent turns
        compressed = system_messages.copy()
        for turn in recent_turns:
            compressed.extend(turn)

        if verbose:
            print(f"[SlidingWindow] Compressed messages: {len(compressed)}")
            print(f"[SlidingWindow] Turns dropped: {turns_dropped}")

        return compressed
