import re

from app.schemas import Difficulty, SceneStep


def normalize_text(text: str) -> str:
    spaced = re.sub(r"[^a-z0-9' ]+", " ", text.lower())
    return re.sub(r"\s+", " ", spaced).strip()


def phrase_in_text(phrase: str, text: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    normalized_text = normalize_text(text)
    if not normalized_phrase:
        return False
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def rule_match(text: str, step: SceneStep, difficulty: Difficulty) -> bool:
    if any(phrase_in_text(phrase, text) for phrase in step.target_phrases):
        return True
    if difficulty == Difficulty.sprout:
        return any(
            phrase_in_text(keyword, text)
            for keyword in step.accepted_keywords
        )
    return False

