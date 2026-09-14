import re


# ---------------------------------------------------------
# Limits
# ---------------------------------------------------------

MAX_INPUT_LENGTH = 10_000
MAX_OUTPUT_LENGTH = 20_000


# ---------------------------------------------------------
# Potentially dangerous secrets
# ---------------------------------------------------------

SECRET_PATTERNS = [
    # Generic API keys / tokens
    re.compile(
        r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)"
        r"\s*[:=]\s*[A-Za-z0-9_\-./+=]{16,}"
    ),

    # Bearer tokens
    re.compile(
        r"(?i)\bbearer\s+[A-Za-z0-9_\-./+=]{20,}"
    ),

    # OpenAI-style keys
    re.compile(
        r"\bsk-[A-Za-z0-9]{20,}\b"
    ),

    # Google API keys
    re.compile(
        r"\bAIza[A-Za-z0-9_\-]{20,}\b"
    ),
]


# ---------------------------------------------------------
# PII patterns
# ---------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+91[\s-]?)?"
    r"[6-9]\d{9}"
    r"(?!\d)"
)

AADHAAR_PATTERN = re.compile(
    r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"
)


# ---------------------------------------------------------
# Input validation
# ---------------------------------------------------------

def validate_input(text: str) -> tuple[bool, str]:
    """
    Validate incoming user input.

    Returns:
        (True, cleaned_text) when valid
        (False, reason) when blocked
    """

    if not isinstance(text, str):
        return False, "Invalid input."

    text = text.strip()

    if not text:
        return False, "Please enter a message."

    if len(text) > MAX_INPUT_LENGTH:
        return (
            False,
            "Your message is too long. "
            "Please keep it under 10,000 characters.",
        )

    # Block obvious secret leakage.
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return (
                False,
                "For security, please don't send API keys, "
                "passwords, access tokens, or other secrets here.",
            )

    return True, text


# ---------------------------------------------------------
# PII scrubbing
# ---------------------------------------------------------

def scrub_pii(text: str) -> str:
    """
    Replace common sensitive identifiers before sending
    user content to an LLM.
    """

    text = EMAIL_PATTERN.sub(
        "[EMAIL_REDACTED]",
        text,
    )

    text = PHONE_PATTERN.sub(
        "[PHONE_REDACTED]",
        text,
    )

    text = AADHAAR_PATTERN.sub(
        "[ID_REDACTED]",
        text,
    )

    return text


# ---------------------------------------------------------
# Output validation
# ---------------------------------------------------------

def validate_output(text: str) -> str:
    """
    Validate and sanitize model output before returning it
    to the user.
    """

    if not text:
        return (
            "I couldn't generate a response right now. "
            "Please try again."
        )

    text = text.strip()

    if len(text) > MAX_OUTPUT_LENGTH:
        text = text[:MAX_OUTPUT_LENGTH].rstrip()

    # Never allow obvious secrets generated accidentally
    # by the model to be returned unchanged.
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(
            "[SECRET_REDACTED]",
            text,
        )

    return text