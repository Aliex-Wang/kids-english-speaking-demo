def start_practice(page, live_server):
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def answer_until_complete(page, max_turns=8):
    for _ in range(max_turns):
        if page.get_by_test_id("end-screen").is_visible():
            return
        page.wait_for_function(
            "!document.querySelector('[data-testid=mic-button]').disabled",
            timeout=15000,
        )
        if page.get_by_test_id("end-screen").is_visible():
            return
        page.get_by_test_id("mic-button").click()
        page.wait_for_timeout(350)
        page.get_by_test_id("mic-button").click(force=True)
        page.wait_for_function(
            """() => {
              const end = document.querySelector(
                '[data-testid=end-screen]:not(.hidden)'
              );
              const mic = document.querySelector('[data-testid=mic-button]');
              const status = document.querySelector('[data-testid=status]');
              return Boolean(end) || (
                !mic.disabled
                && status.textContent !== '录音中... 点击麦克风结束'
              );
            }""",
            timeout=15000,
        )


def test_complete_practice_and_restart_with_new_theme(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    previous_theme = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1')).envelope.scene.theme"
    )
    answer_until_complete(page)
    page.wait_for_selector(
        "[data-testid=end-screen]:not(.hidden)",
        timeout=15000,
    )
    assert page.get_by_test_id("stars").inner_text()
    assert page.get_by_test_id("target-expressions").locator("li").count() >= 1
    page.get_by_test_id("restart-button").click()
    page.wait_for_selector("#task-intro:not(.hidden)", timeout=15000)
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["hasStarted"] is False
    assert state["stars"] == 0
    assert state["envelope"]["scene"]["theme"] != previous_theme


def test_mobile_layout_has_no_horizontal_overflow(
    live_server,
    browser_page,
):
    page = browser_page
    page.set_viewport_size({"width": 390, "height": 844})
    start_practice(page, live_server)
    assert page.get_by_test_id("mic-button").is_visible()
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - window.innerWidth"
    )
    assert overflow <= 1
