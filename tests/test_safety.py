from app.safety import SafetyValidator


def test_blocks_violence_and_personal_information_requests():
    safety = SafetyValidator()
    assert safety.violations("Show me your gun and blood.")
    assert safety.violations("What is your home address?")
    assert safety.violations("Send me a photo of your school.")


def test_allows_normal_child_friendly_text():
    safety = SafetyValidator()
    assert safety.violations("Let's buy an apple at the shop.") == []
