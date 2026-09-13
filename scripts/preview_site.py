"""Optional local Playwright preview; never connects to a tenant or changes browser profiles."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        url = (ROOT / "docs" / "index.html").as_uri()
        page.goto(url + "?scoutTheme=light", wait_until="load")
        assert page.locator("html").get_attribute("data-theme") == "light"
        assert "generate DAX" in page.locator(".hero .lead").inner_text()
        assert page.locator("#setup").count() == 1
        assert page.get_by_role("link", name="Download solution ZIP", exact=True).get_attribute("href") == (
            "https://github.com/RyanBowie/copilot-studio-powerbi-agent/raw/refs/heads/main/"
            "solution/PowerBIQueryStarter_unmanaged.zip")
        page.locator("img").evaluate_all("(images) => Promise.all(images.map(img => { img.loading = 'eager'; return img.decode(); }))")
        assert page.locator("img").evaluate_all("(images) => images.every(img => img.complete && img.naturalWidth > 0)")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(ROOT / "docs" / "assets" / "walkthrough-light.png"), full_page=True)
        page.locator(".hero .chat-card").screenshot(path=str(ROOT / "docs" / "assets" / "illustrative-ranking-output.png"))
        page.locator("#tab-dax").click()
        assert page.locator("#panel-dax").is_visible()
        page.locator("#tab-dax").press("ArrowUp")
        assert page.locator("#panel-analyze").is_visible()
        page.locator("#tab-analyze").press("Home")
        assert page.locator("#panel-rank").is_visible()
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path=str(ROOT / "docs" / "assets" / "walkthrough-dark.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(url + "?scoutTheme=light", wait_until="load")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile layout overflows."
        page.screenshot(path=str(ROOT / "docs" / "assets" / "walkthrough-mobile.png"), full_page=True)
        assert not errors, f"Browser JavaScript errors: {errors}"
        browser.close()
    print("Light/dark/mobile rendering, embedded images, tabs, keyboard navigation, and browser errors checked.")


if __name__ == "__main__":
    main()
