def test_start_flow_saves_practice_and_navigates(live_server, browser_page):
    page = browser_page
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    assert page.get_by_test_id("start-button").is_enabled()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["difficulty"] == "explorer"
    assert state["signature"]
    assert state["envelope"]["scene"]["steps"]
    assert state["currentStepId"] == "step_1"
