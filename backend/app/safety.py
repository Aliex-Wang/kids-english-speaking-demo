import re


class SafetyValidator:
    BANNED_PATTERNS = [
        r"\b(kill|gun|blood|horror|naked|sex|adult)\b",
        r"\b(girlfriend|boyfriend|dating)\b",
        r"\b(buy now|discount|subscribe|brand)\b",
        r"\b(your (real )?name|your school|your (home )?address|your phone|send (me )?a photo)\b",
        r"\b(what is your address|where do you live)\b",
    ]

    def violations(self, text: str) -> list[str]:
        normalized = text.lower()
        return [
            pattern
            for pattern in self.BANNED_PATTERNS
            if re.search(pattern, normalized, flags=re.IGNORECASE)
        ]
