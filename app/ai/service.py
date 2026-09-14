from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.guardrails import (
    scrub_pii,
    validate_input,
    validate_output,
)
from app.ai.prompt import SAK_AI_SYSTEM_PROMPT
from app.ai.router import LLMRouter
from app.database.repositories import (
    create_message,
    get_or_create_conversation,
    get_recent_messages,
)


class AIService:
    """Main service connecting memory, guardrails, and LLM routing."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def generate_response(
        self,
        session: AsyncSession,
        telegram_id: int,
        user_message: str,
    ) -> tuple[str, str]:

        # -------------------------------------------------
        # 1. Validate input
        # -------------------------------------------------

        is_valid, cleaned_message = validate_input(
            user_message
        )

        if not is_valid:
            raise ValueError(cleaned_message)

        # -------------------------------------------------
        # 2. Get/create conversation
        # -------------------------------------------------

        conversation = await get_or_create_conversation(
            session=session,
            telegram_id=telegram_id,
        )

        # -------------------------------------------------
        # 3. Store original user message
        # -------------------------------------------------

        await create_message(
            session=session,
            conversation_id=conversation.id,
            role="user",
            content=cleaned_message,
        )

        # -------------------------------------------------
        # 4. Load recent memory
        # -------------------------------------------------

        history = await get_recent_messages(
            session=session,
            conversation_id=conversation.id,
            limit=20,
        )

        # -------------------------------------------------
        # 5. Build LLM context
        # -------------------------------------------------

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": SAK_AI_SYSTEM_PROMPT,
            }
        ]

        for message in history:
            content = message.content

            # Scrub PII before sending conversation content
            # to the external LLM provider.
            content = scrub_pii(content)

            messages.append(
                {
                    "role": message.role,
                    "content": content,
                }
            )

        # -------------------------------------------------
        # 6. Generate response
        # -------------------------------------------------

        response, model = await self.router.generate(
            messages=messages,
        )

        # -------------------------------------------------
        # 7. Validate model output
        # -------------------------------------------------

        response = validate_output(response)

        # -------------------------------------------------
        # 8. Store assistant response
        # -------------------------------------------------

        await create_message(
            session=session,
            conversation_id=conversation.id,
            role="assistant",
            content=response,
            model=model,
        )

        # -------------------------------------------------
        # 9. Return
        # -------------------------------------------------

        return response, model