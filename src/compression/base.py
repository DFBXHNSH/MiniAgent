"""
Base compression strategy.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class CompressionStrategy(ABC):
    """
    Abstract base class for compression strategies.
    """

    @abstractmethod
    def compress(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Compress the message history.

        Args:
            messages: The current message history
            **kwargs: Additional parameters for the compression strategy

        Returns:
            The compressed message history
        """
        pass


def separate_system_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract system messages from the history.

    Args:
        messages: The message history

    Returns:
        List of system messages
    """
    return [m for m in messages if m["role"] == "system"]
