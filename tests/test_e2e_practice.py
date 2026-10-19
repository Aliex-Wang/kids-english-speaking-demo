def start_practice(page, live_server, difficulty="explorer"):
    page.goto(live_server)
    page.get_by_test_id(f"difficulty-{difficulty}").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def record_one_turn(page):
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click()


def test_practice_records_a_turn_and_restores_progress(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"
    record_one_turn(page)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )
    assert page.get_by_test_id("ai-bubble").inner_text()
    page.reload()
    page.wait_for_selector("#dialogue:not(.hidden)")
    assert page.get_by_test_id("progress-label").inner_text() == "2 / 5"
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["currentStepId"] == "step_2"
    assert "recognized_text" not in state
    assert "transcript" not in str(state).lower()


def test_help_button_shows_hint_without_advancing(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    page.get_by_test_id("help-button").click()
    hint = page.get_by_test_id("hint")
    assert hint.is_visible()
    assert hint.inner_text()
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"