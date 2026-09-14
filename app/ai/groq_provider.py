import json
from collections.abc import AsyncIterator

import httpx

from app.ai.providers import LLMProvider
from app.config.settings import settings


class GroqProvider(LLMProvider):
    name = "groq"
    model = "openai/gpt-oss-120b"

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
    ) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        response = await self.client.post(
            self.API_URL,
            headers=self._headers(),
            json=self._payload(messages),
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        async with self.client.stream(
            "POST",
            self.API_URL,
            headers=self._headers(),
            json=self._payload(messages, stream=True),
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                if not line.startswith("data: "):
                    continue

                data = line[6:]

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                choices = chunk.get("choices", [])

                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content")

                if content:
                    yield content