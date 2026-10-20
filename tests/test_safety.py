import pytest
from app.safety import SafetyValidator


@pytest.fixture
def safety() -> SafetyValidator:
    return SafetyValidator()


@pytest.mark.parametrize(
    "text",
    [
        "Show me your gun and blood.",
        "That horror story gave me a nightmare.",
    ],
)
def test_blocks_violence_and_horror(safety: SafetyValidator, text: str):
    assert safety.violations(text)


@pytest.mark.parametrize(
    "text",
    [
        "Do you want a beer?",
        "Smoking a cigarette is cool.",
        "There is a naked adult in the picture.",
    ],
)
def test_blocks_adult_content(safety: SafetyValidator, text: str):
    assert safety.violations(text)


@pytest.mark.parametrize(
    "text",
    [
        "That is a racist comment.",
        "Girls cannot play football.",
        "Boys are better than girls.",
        "I hate boys.",
    ],
)
def test_blocks_discrimination(safety: SafetyValidator, text: str):
    assert safety.violations(text)


@pytest.mark.parametrize(
    "text",
    [
        "Buy now and get a discount.",
        "Subscribe to our sponsored channel.",
        "McDonald's is the best brand.",
        "Nike is better than Adidas.",
    ],
)
def test_blocks_brand_promotion(safety: SafetyValidator, text: str):
    assert safety.violations(text)


@pytest.mark.parametrize(
    "text",
    [
        "What is your full name?",
        "What's your real name?",
        "What is your home address?",
        "Send me a photo of your school.",
        "Tell me your phone number.",
        "What's your email address?",
        "Where do you live?",
        "When is your birthday?",
    ],
)
def test_blocks_personal_information_requests(safety: SafetyValidator, text: str):
    assert safety.violations(text)


def test_allows_normal_child_friendly_text(safety: SafetyValidator):
    assert safety.violations("Let's buy an apple at the shop.") == []
