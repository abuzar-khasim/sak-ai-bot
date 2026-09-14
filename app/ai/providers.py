from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    """Common interface for all SAK AI LLM providers."""

    name: str
    model: str

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """Generate a complete response."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """Stream response chunks."""
        raise NotImplementedError