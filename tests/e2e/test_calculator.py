import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def open_calculator(page, base_url):
    assert base_url, "Pass --base-url for the running application"
    page.goto(base_url + '/calculator')
    expect(page.get_by_role("heading", name="Calculator", exact=True)).to_be_visible()


def submit(page, a="6", b="7", operation="multiply"):
    page.get_by_label("First number", exact=True).fill(a)
    page.get_by_label("Second number", exact=True).fill(b)
    page.get_by_label("Operation", exact=True).select_option(operation)
    page.get_by_role("button", name="Calculate").click()


def test_browser_and_api_agree(page):
    submit(page)
    expect(page.locator("#browser-result")).to_have_text("42")
    expect(page.locator("#api-result")).to_have_text("42")
    expect(page.locator("#comparison")).to_have_text("Results match")
    expect(page.locator("#api-status")).to_have_text("API available")
    expect(page.locator("#environment")).not_to_have_text("Loading…")


@pytest.mark.parametrize("a,b,operation,error", [
    ("", "7", "add", "Enter both numbers."),
    ("6", "0", "divide", "Cannot divide by zero."),
])
def test_invalid_input_never_claims_a_match(page, a, b, operation, error):
    submit(page, a, b, operation)
    expect(page.locator("#error")).to_have_text(error)
    expect(page.locator("#comparison")).to_be_empty()
    expect(page.locator("#api-result")).to_have_text("—")


def test_decimal_comparison(page):
    submit(page, "0.1", "0.2", "add")
    expect(page.locator("#browser-result")).to_have_text("0.3")
    expect(page.locator("#api-result")).to_have_text("0.3")
    expect(page.locator("#comparison")).to_have_text("Results match")


def test_api_failure_preserves_local_result(page):
    page.route("**/api/calculate", lambda route: route.abort())
    submit(page)
    expect(page.locator("#browser-result")).to_have_text("42")
    expect(page.locator("#api-result")).to_have_text("Unavailable")
    expect(page.locator("#error")).to_contain_text("API verification failed")
    expect(page.locator("#comparison")).to_be_empty()
    expect(page.get_by_role("button", name="Calculate")).to_be_enabled()


def test_mismatch_is_visible(page):
    page.route("**/api/calculate", lambda route: route.fulfill(json={"result": 99}))
    submit(page)
    expect(page.locator("#comparison")).to_have_text("Results differ")


def test_keyboard_and_narrow_screen(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_label("Second number", exact=True).press("Enter")
    expect(page.locator("#comparison")).to_have_text("Results match")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
