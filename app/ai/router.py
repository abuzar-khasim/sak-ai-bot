from collections.abc import AsyncIterator
from time import monotonic

import httpx

from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.providers import LLMProvider


class LLMRouter:
    """
    Routes SAK AI requests through available LLM providers.

    Provider order:
        1. Groq
        2. Gemini

    Temporary provider failures trigger fallback and cooldown.
    Permanent configuration/request errors are not treated as
    temporary outages.
    """

    # How long a temporarily failing provider is skipped.
    COOLDOWN_SECONDS = 60.0

    # HTTP errors that are normally temporary and suitable for fallback.
    TEMPORARY_STATUS_CODES = {
        429,  # Rate limit
        500,  # Internal server error
        502,  # Bad gateway
        503,  # Service unavailable
        504,  # Gateway timeout
    }

    def __init__(
        self,
        client: httpx.AsyncClient,
    ):
        self.providers: list[LLMProvider] = [
            GroqProvider(client),
            GeminiProvider(client),
        ]

        # provider.name -> monotonic timestamp until which it is unavailable
        self._cooldowns: dict[str, float] = {}

    def _is_on_cooldown(self, provider: LLMProvider) -> bool:
        cooldown_until = self._cooldowns.get(provider.name)

        if cooldown_until is None:
            return False

        if monotonic() >= cooldown_until:
            self._cooldowns.pop(provider.name, None)
            print(f"✅ {provider.name} cooldown expired")
            return False

        return True

    def _set_cooldown(self, provider: LLMProvider) -> None:
        cooldown_until = monotonic() + self.COOLDOWN_SECONDS
        self._cooldowns[provider.name] = cooldown_until

        print(
            f"⏸️ {provider.name} temporarily disabled "
            f"for {self.COOLDOWN_SECONDS:.0f}s"
        )

    def _is_temporary_error(self, error: Exception) -> bool:
        if isinstance(
            error,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
            ),
        ):
            return True

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            return status_code in self.TEMPORARY_STATUS_CODES

        return False

    def _log_failure(
        self,
        provider: LLMProvider,
        error: Exception,
    ) -> None:
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code

            print(
                f"⚠️ {provider.name} failed "
                f"({provider.model}) "
                f"HTTP {status}: "
                f"{type(error).__name__}"
            )
        else:
            print(
                f"⚠️ {provider.name} failed "
                f"({provider.model}): "
                f"{type(error).__name__}: {error}"
            )

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[str, str]:
        """
        Generate a complete response.

        Providers are attempted in priority order.
        Providers currently on cooldown are skipped.

        Returns:
            (response_text, model_name)
        """

        last_error: Exception | None = None

        for provider in self.providers:
            if self._is_on_cooldown(provider):
                print(
                    f"⏭️ Skipping {provider.name} "
                    f"because it is on cooldown"
                )
                continue

            try:
                response = await provider.generate(messages)

                # Successful request means the provider is healthy.
                self._cooldowns.pop(provider.name, None)

                return response, provider.model

            except Exception as error:
                last_error = error

                self._log_failure(
                    provider,
                    error,
                )

                if not self._is_temporary_error(error):
                    print(
                        f"🛑 {provider.name} error is not "
                        f"considered temporary"
                    )
                    raise

                self._set_cooldown(provider)

                print(
                    f"🔄 Falling back from "
                    f"{provider.name} to the next provider"
                )

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "No LLM providers are currently available"
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Stream a response with safe provider fallback.

        Fallback is allowed only before the first chunk.

        Once a provider has produced output, the router will
        not switch providers during that response.
        """

        for provider_index, provider in enumerate(self.providers):
            if self._is_on_cooldown(provider):
                print(
                    f"⏭️ Skipping {provider.name} "
                    f"because it is on cooldown"
                )
                continue

            received_chunk = False

            try:
                async for chunk in provider.stream(messages):
                    received_chunk = True
                    yield chunk

                # Successful stream completed.
                self._cooldowns.pop(provider.name, None)
                return

            except Exception as error:
                self._log_failure(
                    provider,
                    error,
                )

                # Never switch providers after output has
                # already been delivered to the user.
                if received_chunk:
                    raise

                if not self._is_temporary_error(error):
                    print(
                        f"🛑 {provider.name} stream error is "
                        f"not considered temporary"
                    )
                    raise

                self._set_cooldown(provider)

                if provider_index < len(self.providers) - 1:
                    print(
                        f"🔄 Falling back from "
                        f"{provider.name} to "
                        f"{self.providers[provider_index + 1].name}"
                    )
                    continue

                raise

        raise RuntimeError(
            "No LLM providers are currently available"
        )