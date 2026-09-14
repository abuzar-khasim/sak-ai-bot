from collections.abc import AsyncIterator

import httpx

from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.providers import LLMProvider


class LLMRouter:
    """Routes SAK AI requests through the primary provider with fallback."""

    FALLBACK_ERRORS = (
        httpx.HTTPStatusError,
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.NetworkError,
    )

    def __init__(
        self,
        client: httpx.AsyncClient,
    ):
        self.providers: list[LLMProvider] = [
            GroqProvider(client),
            GeminiProvider(client),
        ]

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[str, str]:
        """
        Generate a complete response.

        If the primary provider fails, try the next provider.
        Returns:
            (response_text, model_name)
        """

        last_error: Exception | None = None

        for provider in self.providers:
            try:
                response = await provider.generate(messages)

                return response, provider.model

            except self.FALLBACK_ERRORS as error:
                last_error = error

                print(
                    f"⚠️ {provider.name} failed "
                    f"({provider.model}): "
                    f"{type(error).__name__}: {error}"
                )

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "No LLM providers configured"
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[AsyncIterator[str], str]:
        """
        Return a streaming iterator with fallback support.

        Fallback is only allowed if the provider fails before
        producing the first chunk.

        Once output has started, we never switch providers because
        doing so could duplicate or corrupt the response.
        """

        return self._stream_with_fallback(
            messages
        )

    async def _stream_with_fallback(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Try providers sequentially.

        The first provider that successfully produces a chunk
        becomes the active provider for the entire stream.
        """

        for provider_index, provider in enumerate(
            self.providers
        ):
            stream = provider.stream(messages)

            received_chunk = False

            try:
                async for chunk in stream:
                    received_chunk = True
                    yield chunk

                return

            except self.FALLBACK_ERRORS as error:

                print(
                    f"⚠️ {provider.name} stream failed "
                    f"({provider.model}): "
                    f"{type(error).__name__}: {error}"
                )

                # If output has already reached the user,
                # never switch providers.
                if received_chunk:
                    raise

                # No output was produced, so fallback is safe.
                if provider_index < len(self.providers) - 1:
                    print(
                        f"🔄 Falling back from "
                        f"{provider.name} to "
                        f"{self.providers[provider_index + 1].name}"
                    )
                    continue

                raise

        raise RuntimeError(
            "All LLM providers failed"
        )