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
    """
    Main AI service for SAK AI.

    Responsibilities:
    - Validate user input
    - Protect secrets
    - Scrub PII
    - Manage conversation memory
    - Call the LLM router
    - Validate model output
    - Store safe conversation messages
    """

    def __init__(self, router: LLMRouter):
        self.router = router

    async def generate_response(
        self,
        session: AsyncSession,
        telegram_id: int,
        user_message: str,
    ) -> tuple[str, str]:

        # ====================================================
        # 1. VALIDATE INPUT FIRST
        # ====================================================
        #
        # IMPORTANT:
        # Nothing should be stored in PostgreSQL or sent
        # to an LLM before this validation succeeds.
        #

        is_valid, cleaned_message = validate_input(
            user_message
        )

        if not is_valid:
            raise ValueError(
                cleaned_message
            )

        # ====================================================
        # 2. SCRUB PII
        # ====================================================
        #
        # Email, phone numbers, Aadhaar-like IDs, etc.
        # are removed before memory/LLM processing.
        #

        safe_message = scrub_pii(
            cleaned_message
        )

        # ====================================================
        # 3. GET OR CREATE CONVERSATION
        # ====================================================

        conversation = await get_or_create_conversation(
            session=session,
            telegram_id=telegram_id,
        )

        # ====================================================
        # 4. STORE SAFE USER MESSAGE
        # ====================================================

        await create_message(
            session=session,
            conversation_id=conversation.id,
            role="user",
            content=safe_message,
        )

        # ====================================================
        # 5. LOAD RECENT CONVERSATION
        # ====================================================

        history = await get_recent_messages(
            session=session,
            conversation_id=conversation.id,
            limit=20,
        )

        # ====================================================
        # 6. BUILD LLM MESSAGE LIST
        # ====================================================

        messages = [
            {
                "role": "system",
                "content": SAK_AI_SYSTEM_PROMPT,
            }
        ]

        for message in history:

            messages.append(
                {
                    "role": message.role,
                    "content": scrub_pii(
                        message.content
                    ),
                }
            )

        # ====================================================
        # 7. CALL LLM ROUTER
        # ====================================================

        response, model = await self.router.generate(
            messages=messages
        )

        # ====================================================
        # 8. VALIDATE MODEL OUTPUT
        # ====================================================

        response = validate_output(
            response
        )

        # ====================================================
        # 9. STORE SAFE ASSISTANT RESPONSE
        # ====================================================

        await create_message(
            session=session,
            conversation_id=conversation.id,
            role="assistant",
            content=response,
            model=model,
        )

        # ====================================================
        # 10. RETURN RESPONSE
        # ====================================================

        return response, model