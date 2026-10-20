import re
from typing import ClassVar


class SafetyValidator:
    VIOLENCE_HORROR_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(kill|killing|killed|murder|fight|fighting|attack|attacking|gun|guns|knife|knives|weapon|weapons|blood|bloody|horror|nightmare|nightmares)\b",
    )
    ADULT_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(beer|wine|alcohol|drunk|smoke|smoking|cigarette|cigarettes|naked|sex|sexual|adult|adults)\b",
    )
    DISCRIMINATION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(racist|racism|sexist|sexism|discrimination|discriminate)\b",
        r"\b(inferior|superior race)\b",
        r"\b(boys|girls)\s+(are|is)\s+(better|worse)\b",
        r"\b(boys|girls)\s+(cannot|can't|cant)\b",
        r"\bhate\s+(boys|girls|people|women|men|children)\b",
    )
    BRAND_PROMOTION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(buy now|discount|subscribe|sponsored|brand|best brand)\b",
        r"\b(coca[- ]?cola|pepsi|mcdonald(?:'s|s)?|nike|adidas|disney)\b",
    )
    PERSONAL_INFORMATION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(your (full|real) name|your name|your school|your (home )?address|your phone( number)?|your email( address)?|your birthday)\b",
        r"\b(what(?:'s| is) your (full |real |home )?(name|address|phone( number)?|email( address)?|birthday))\b",
        r"\b(send (me )?a (photo|picture))\b",
        r"\b(where do you live)\b",
        r"\b((what|which) school do you (go to|attend)|what(?:'s| is) your school('s name)?)\b",
    )
    BANNED_PATTERNS: ClassVar[tuple[str, ...]] = (
        *VIOLENCE_HORROR_PATTERNS,
        *ADULT_PATTERNS,
        *DISCRIMINATION_PATTERNS,
        *BRAND_PROMOTION_PATTERNS,
        *PERSONAL_INFORMATION_PATTERNS,
    )

    def violations(self, text: str) -> list[str]:
        normalized = text.lower()
        return [
            pattern
            for pattern in self.BANNED_PATTERNS
            if re.search(pattern, normalized, flags=re.IGNORECASE)
        ]
