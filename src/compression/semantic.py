"""
Semantic summary compression strategy.

This strategy summarizes early dialogues with the LLM.
"""

from typing import List, Dict, Any

from src.compression.base import CompressionStrategy, separate_system_messages
from src.llm.client import LLMClient


class SemanticSummaryCompression(CompressionStrategy):
    """
    Semantic summary compression: summarize early dialogues with LLM.

    System messages are always preserved.
    Early dialogues beyond summary_threshold are summarized.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize with an LLM client.

        Args:
            llm_client: The LLM client to use for summarization
        """
        self.llm_client = llm_client

    def compress(
        self,
        messages: List[Dict[str, Any]],
        summary_threshold: int = 5,
        max_summary_length: int = 200,
        verbose: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Compress messages using semantic summary.

        Args:
            messages: The current message history
            summary_threshold: Number of turns after which to start summarizing
            max_summary_length: Maximum length of summary
            verbose: If True, print compression details
            **kwargs: Ignored additional parameters

        Returns:
            The compressed message history
        """
        # Separate system messages and dialogue
        system_messages = separate_system_messages(messages)
        dialogue = [m for m in messages if m["role"] != "system"]

        # Check if enough messages to compress
        if len(dialogue) <= summary_threshold * 3:
            if verbose:
                print("[SemanticSummary] Skipping: not enough messages")
            return messages

        if verbose:
            print(f"[SemanticSummary] Original messages: {len(messages)}")
            print(f"[SemanticSummary] Dialogue messages: {len(dialogue)}")

        # Determine compression point (compress first half of dialogue)
        compress_point = len(dialogue) // 2
        to_summarize = dialogue[:compress_point]

        if verbose:
            print(f"[SemanticSummary] Summarizing {len(to_summarize)} messages...")

        # Generate summary via LLM
        summary = self.llm_client.generate_summary(to_summarize, max_summary_length)

        if verbose:
            print(f"[SemanticSummary] Summary generated: {len(summary)} chars")
            print(f"[SemanticSummary] Summary: {summary[:100]}...")

        # Build compressed history: system + summary + retained dialogue
        compressed = system_messages + [
            {
                "role": "system",
                "content": f"[Conversation Summary] {summary}"
            }
        ] + dialogue[compress_point:]

        if verbose:
            print(f"[SemanticSummary] Compressed messages: {len(compressed)}")

        return compressed
