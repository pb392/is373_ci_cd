"""Capture public QA and production pages as reproducible grading evidence."""
import json
from pathlib import Path
import urllib.request
from playwright.sync_api import sync_playwright

folder = Path("artifacts/screenshots")
folder.mkdir(parents=True, exist_ok=True)
records = {}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    for name, url in [("qa", "https://qa.xenoshin.com"), ("production", "https://xenoshin.com")]:
        response = page.goto(url, wait_until="networkidle")
        assert response and response.status == 200
        page.get_by_role("heading", name="The test website is working.").wait_for()
        page.screenshot(path=str(folder / f"{name}.png"), full_page=True)
        with urllib.request.urlopen(url + "/health", timeout=10) as health:
            records[name] = {"url": url, "health": json.load(health)}
    browser.close()
(folder / "observations.json").write_text(json.dumps(records, indent=2))
