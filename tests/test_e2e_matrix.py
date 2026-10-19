import pytest

from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector

STEP_COUNTS = {
    Difficulty.sprout: 4,
    Difficulty.explorer: 5,
    Difficulty.star: 6,
}


@pytest.mark.slow
@pytest.mark.parametrize("difficulty", list(Difficulty))
@pytest.mark.parametrize("theme", list(ThemeId))
def test_all_theme_difficulty_combinations_complete(
    live_server_app,
    browser_page,
    theme,
    difficulty,
):
    url, app = live_server_app
    app.state.services.scene_generator.selector = ThemeSelector([theme])
    page = browser_page
    page.goto(url)
    page.evaluate("localStorage.clear()")
    page.get_by_test_id(f"difficulty-{difficulty.value}").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")
    page.evaluate(
        """() => {
          navigator.mediaDevices.getUserMedia = () =>
            Promise.reject(new DOMException('denied', 'NotAllowedError'));
        }"""
    )
    page.get_by_test_id("mic-button").click()
    page.wait_for_selector("#text-fallback:not(.hidden)")
    total = STEP_COUNTS[difficulty]
    for index in range(total):
        page.get_by_test_id("text-input").fill("yes")
        page.get_by_test_id("text-submit").click()
        if index < total - 1:
            expected = f"{index + 2} / {total}"
            page.wait_for_function(
                "document.querySelector('[data-testid=progress-label]').textContent === "
                f"'{expected}'",
                timeout=15000,
            )
        else:
            page.wait_for_selector(
                "[data-testid=end-screen]:not(.hidden)",
                timeout=15000,
            )
    assert page.get_by_test_id("end-screen").is_visible()
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["completed"] is True
    assert state["envelope"]["scene"]["theme"] == theme.value
    assert state["envelope"]["scene"]["difficulty"] == difficulty.value
