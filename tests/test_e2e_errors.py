import json


def start_practice(page, live_server):
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def test_microphone_denial_exposes_text_fallback(live_server, browser_page):
    page = browser_page
    start_practice(page, live_server)
    page.evaluate(
        """() => {
          navigator.mediaDevices.getUserMedia = () =>
            Promise.reject(new DOMException('denied', 'NotAllowedError'));
        }"""
    )
    page.get_by_test_id("mic-button").click()
    page.wait_for_selector("#text-fallback:not(.hidden)")
    page.get_by_test_id("text-input").fill("yes")
    page.get_by_test_id("text-submit").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )


def test_network_failure_is_recoverable(live_server, browser_page):
    page = browser_page
    start_practice(page, live_server)
    page.route("**/api/turn", lambda route: route.abort())
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click(force=True)
    page.wait_for_function(
        "document.querySelector('[data-testid=status]').textContent.includes('网络暂时没有连上')",
        timeout=15000,
    )
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"
    page.unroute("**/api/turn")
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click(force=True)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )


def test_help_then_answer_logs_continued_after_help(
    live_server,
    browser_page,
):
    page = browser_page
    events = []

    def capture(request):
        if request.url.endswith("/api/event"):
            try:
                events.append(json.loads(request.post_data))
            except (TypeError, json.JSONDecodeError):
                pass

    page.on("request", capture)
    start_practice(page, live_server)
    page.get_by_test_id("help-button").click()
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click(force=True)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )
    page.wait_for_timeout(500)
    assert any(
        event.get("name") == "continued_after_help"
        for event in events
    )

def open_text_fallback(page):
    page.evaluate(
        "document.getElementById('text-fallback').classList.remove('hidden')"
    )


def test_invalid_scene_signature_regenerates_and_recovers(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    page.evaluate(
        """() => {
          const key = 'kidsEnglishPracticeV1';
          const data = JSON.parse(localStorage.getItem(key));
          data.signature = 'tampered';
          localStorage.setItem(key, JSON.stringify(data));
        }"""
    )
    page.reload()
    page.wait_for_url("**/practice")
    page.wait_for_selector("#dialogue:not(.hidden)")
    open_text_fallback(page)
    page.get_by_test_id("text-input").fill("yes")
    page.get_by_test_id("text-submit").click()
    page.wait_for_selector("#task-intro:not(.hidden)", timeout=15000)
    assert page.locator("#dialogue").evaluate(
        "el => el.classList.contains('hidden')"
    )
    signature = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1')).signature"
    )
    assert signature != "tampered"
    assert len(signature) > 0

