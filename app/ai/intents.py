from enum import StrEnum


class AIIntent(StrEnum):
    NONE = "none"
    CONTACT_US = "contact_us"
    UPDATES = "updates"
    ASK_AI = "ask_ai"


def detect_intent(text: str) -> AIIntent:
    """
    Detect simple navigation intents from user language.

    This is intentionally deterministic. We do not ask the LLM
    to decide whether a Telegram navigation action should happen.
    """

    text = text.lower().strip()

    # ---------------------------------------------------------
    # Contact intent
    # ---------------------------------------------------------

    contact_keywords = (
        "contact",
        "contact us",
        "talk to you",
        "talk to team",
        "talk with team",
        "reach you",
        "reach the team",
        "reach team",
        "get in touch",
        "speak to team",
        "speak with team",
        "send requirement",
        "submit requirement",
        "submit my requirement",
        "business inquiry",
        "business enquiry",
        "contact team",
    )

    if any(keyword in text for keyword in contact_keywords):
        return AIIntent.CONTACT_US

    # ---------------------------------------------------------
    # Updates intent
    # ---------------------------------------------------------

    updates_keywords = (
        "updates",
        "latest update",
        "latest updates",
        "latest news",
        "news from sak ai",
        "what's new",
        "whats new",
        "recent updates",
        "recent news",
        "announcements",
        "announcement",
    )

    if any(keyword in text for keyword in updates_keywords):
        return AIIntent.UPDATES

    # ---------------------------------------------------------
    # Ask AI intent
    # ---------------------------------------------------------

    ask_ai_keywords = (
        "ask sak ai",
        "ask you",
        "ask a question",
        "ask question",
        "ask something",
        "ai assistant",
        "talk to ai",
        "talk with ai",
    )

    if any(keyword in text for keyword in ask_ai_keywords):
        return AIIntent.ASK_AI

    return AIIntent.NONE