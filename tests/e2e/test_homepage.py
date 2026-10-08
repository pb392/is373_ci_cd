from playwright.sync_api import expect


def test_homepage_on_mobile(page, base_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url)
    expect(page.get_by_role("heading", name="The test website is working.")).to_be_visible()
    expect(page.get_by_text("This page loaded successfully.")).to_be_visible()
    expect(page.get_by_role("button", name="Calculate")).not_to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_homepage_without_javascript(browser, base_url):
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(base_url)
        expect(page.get_by_role("heading", name="The test website is working.")).to_be_visible()
        expect(page.get_by_role("heading", name="Calculator", exact=True)).not_to_be_visible()
    finally:
        context.close()
