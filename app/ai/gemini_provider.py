import json
from collections.abc import AsyncIterator

import httpx

from app.ai.providers import LLMProvider
from app.config.settings import settings


class GeminiProvider(LLMProvider):
    name = "gemini"
    model = "gemini-2.5-flash"

    API_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    STREAM_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:streamGenerateContent"
    )

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        }

    def _payload(
        self,
        messages: list[dict[str, str]],
    ) -> dict:
        system_instruction = None
        contents = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            # Gemini handles system instructions separately.
            if role == "system":
                system_instruction = {
                    "parts": [
                        {
                            "text": content,
                        }
                    ]
                }
                continue

            if role == "assistant":
                role = "model"

            if role not in {"user", "model"}:
                continue

            contents.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": content,
                        }
                    ],
                }
            )

        payload = {
            "contents": contents,
        }

        if system_instruction is not None:
            payload["systemInstruction"] = system_instruction

        return payload

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

        candidates = data.get("candidates", [])

        if not candidates:
            raise RuntimeError("Gemini returned no candidates")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        text_parts = []

        for part in parts:
            text = part.get("text")

            if text:
                text_parts.append(text)

        if not text_parts:
            raise RuntimeError("Gemini returned no text")

        return "".join(text_parts)

    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        async with self.client.stream(
            "POST",
            self.STREAM_URL,
            headers=self._headers(),
            params={"alt": "sse"},
            json=self._payload(messages),
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("data: "):
                    line = line[6:]

                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                candidates = chunk.get("candidates", [])

                if not candidates:
                    continue

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])

                for part in parts:
                    text = part.get("text")

                    if text:
                        yield text