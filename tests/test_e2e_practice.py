from playwright.sync_api import Error as PlaywrightError


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
    page.get_by_test_id("mic-button").click(force=True)


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

def test_record_one_turn_waits_for_slow_microphone_start(
    live_server,
    browser_page,
):
    page = browser_page
    page.add_init_script(
        """
        const getUserMedia = navigator.mediaDevices.getUserMedia.bind(
          navigator.mediaDevices,
        );
        navigator.mediaDevices.getUserMedia = async (...args) => {
          await new Promise((resolve) => setTimeout(resolve, 700));
          return getUserMedia(...args);
        };
        """
    )
    start_practice(page, live_server)
    record_one_turn(page)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent"
        " === '2 / 5'",
        timeout=15000,
    )

def test_audio_playback_failure_falls_back_to_speech(
    live_server,
    browser_page,
):
    page = browser_page
    page.add_init_script(
        """
        window.__spoken = [];
        HTMLMediaElement.prototype.play = () => Promise.reject(
          new DOMException('blocked', 'NotAllowedError'),
        );
        window.speechSynthesis.cancel = () => {};
        window.speechSynthesis.speak = (utterance) => {
          window.__spoken.push(utterance.text);
        };
        """
    )
    start_practice(page, live_server)
    page.wait_for_function(
        "window.__spoken.length > 0",
        timeout=3000,
    )
    assert page.evaluate("window.__spoken[0]") == (
        page.get_by_test_id("opening-text").inner_text()
    )


def test_stalled_audio_playback_does_not_block_turns(
    live_server,
    browser_page,
):
    page = browser_page
    page.add_init_script(
        """
        window.__spoken = [];
        HTMLMediaElement.prototype.play = () => new Promise(() => {});
        window.speechSynthesis.cancel = () => {};
        window.speechSynthesis.speak = (utterance) => {
          window.__spoken.push(utterance.text);
        };
        """
    )
    start_practice(page, live_server)
    page.wait_for_function(
        "window.__spoken.length > 0",
        timeout=4000,
    )
    record_one_turn(page)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent"
        " === '2 / 5'",
        timeout=3000,
    )

def open_text_fallback(page):
    page.evaluate(
        "document.getElementById('text-fallback').classList.remove('hidden')"
    )


def test_practice_turn_timeout_reenables_controls(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    open_text_fallback(page)
    stalled = []
    page.route("**/api/turn", lambda route: stalled.append(route))
    page.clock.install()
    page.get_by_test_id("text-input").fill("hello")
    page.get_by_test_id("text-submit").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=text-input]').disabled",
    )
    page.clock.fast_forward(16000)
    page.wait_for_function(
        "document.querySelector('[data-testid=status]').textContent"
        " === '等得有点久，请再试一次。'",
        timeout=3000,
    )
    assert not page.get_by_test_id("mic-button").is_disabled()
    assert not page.get_by_test_id("text-input").is_disabled()
    assert not page.get_by_test_id("text-submit").is_disabled()
    for route in stalled:
        try:
            route.abort()
        except PlaywrightError:
            continue


def test_practice_network_error_reenables_controls(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    open_text_fallback(page)
    stalled = []
    page.route("**/api/turn", lambda route: stalled.append(route))
    page.get_by_test_id("text-input").fill("hello")
    page.get_by_test_id("text-submit").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=text-input]').disabled",
    )
    assert page.get_by_test_id("mic-button").is_disabled()
    stalled[0].abort()
    page.wait_for_function(
        "document.querySelector('[data-testid=status]').textContent"
        " === '网络暂时没有连上，请再试一次。'",
        timeout=3000,
    )
    assert not page.get_by_test_id("mic-button").is_disabled()
    assert not page.get_by_test_id("text-input").is_disabled()
    assert not page.get_by_test_id("text-submit").is_disabled()

def test_recorder_releases_stream_when_media_recorder_fails(
    live_server,
    browser_page,
):
    page = browser_page
    page.goto(live_server)
    for failure_point, expected_error in (
        ("constructor", "recorder constructor failed"),
        ("start", "recorder start failed"),
    ):
        result = page.evaluate(
            """
            async ({failurePoint}) => {
              const stopped = [];
              const errors = [];
              Object.defineProperty(navigator, 'mediaDevices', {
                configurable: true,
                value: {
                  getUserMedia: async () => ({
                    getTracks: () => [{
                      stop: () => stopped.push('track'),
                    }],
                  }),
                },
              });
              class FakeMediaRecorder {
                constructor() {
                  if (failurePoint === 'constructor') {
                    throw new Error('recorder constructor failed');
                  }
                  this.state = 'inactive';
                  this.mimeType = 'audio/webm';
                }

                static isTypeSupported() {
                  return false;
                }

                start() {
                  throw new Error('recorder start failed');
                }
              }
              window.MediaRecorder = FakeMediaRecorder;
              const {MicRecorder} = await import('/static/js/recorder.js');
              const recorder = new MicRecorder({
                maxSeconds: 15,
                onComplete: () => errors.push('complete'),
                onError: (error) => errors.push(error.message),
              });
              const started = await recorder.start();
              return {started, stopped, errors};
            }
            """,
            {"failurePoint": failure_point},
        )
        assert result == {
            "started": False,
            "stopped": ["track"],
            "errors": [expected_error],
        }
