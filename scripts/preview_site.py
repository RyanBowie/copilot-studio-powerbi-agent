"""Optional local Playwright preview; never connects to a tenant or changes browser profiles."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from build_site import DOWNLOAD_SOURCES

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
        assert "Microsoft 365 Copilot channel configured" in page.locator(".hero .lead").inner_text()
        assert "not an Agent Builder agent" in page.locator(".hero .lead").inner_text()
        assert page.locator(".hero img").count() == 2
        assert "Synthetic illustration" not in page.locator(".hero").inner_text()
        assert "first 8 of 20 rows" in page.locator("#hero-output").inner_text()
        for selector in ("#hero-prompt img", "#hero-output img"):
            bounds = page.locator(selector).bounding_box()
            assert bounds and bounds["y"] + bounds["height"] <= 900, "Opening screenshots must fit before scrolling on desktop."
        assert page.locator("#setup").count() == 1
        assert "semantic model containing agents" in page.locator("#examples").inner_text()
        assert page.locator("#prompt-metadata").inner_text() == "Give me some details of the semantic model"
        assert page.locator("#metadata-example img").count() == 1
        assert "Studio test pane, not the M365 Copilot channel" in page.locator("#metadata-example").inner_text()
        assert page.locator("#tested-model-report img").count() == 1
        assert "not an agent response" in page.locator("#tested-model-report").inner_text()
        assert page.locator("#tools-topics").count() == 1
        assert page.locator("#source-downloads a[download]").count() == 5
        for filename in DOWNLOAD_SOURCES:
            link = page.locator(f'#source-downloads a[href="downloads/{filename}"]')
            assert link.count() == 1 and link.get_attribute("download") is not None
        for name in ("Get model metadata", "Run generated DAX", "Compile DAX advice", "Generated query error"):
            assert name in page.locator("#tools-topics").inner_text()
        assert page.locator("#tools-topics img").count() == 3
        connector = page.locator("#connector-setup")
        assert "Run a query against a dataset" in connector.inner_text()
        for binding in ("ExecuteDatasetQuery", "groupid", "datasetid", "Topic.generatedDax", "Topic.RawRows", "Invoker"):
            assert binding in connector.inner_text()
        assert "Updated starter, not another tool" not in page.locator("main").inner_text()
        assert page.get_by_role("heading", name="What a useful scalability test measures", exact=True).count() == 0
        assert page.locator('img[data-diagram="simple"]').count() == 1
        diagram = (ROOT / "docs" / "assets" / "architecture-simple.svg").read_text(encoding="utf-8")
        assert "Power BI tool" in diagram and "Run a query against a dataset" in diagram
        assert page.get_by_role("heading", name="Historical initial PoC", exact=True).count() == 0
        assert page.get_by_role("img", name="Actual empty standalone Tools tab.", exact=True).count() == 0
        assert page.get_by_role("link", name="Download solution ZIP", exact=True).get_attribute("href") == (
            "https://github.com/RyanBowie/copilot-studio-powerbi-agent/raw/refs/heads/main/"
            "solution/PowerBIQueryStarter_unmanaged.zip")
        page.locator("img").evaluate_all("(images) => Promise.all(images.map(img => { img.loading = 'eager'; return img.decode(); }))")
        assert page.locator("img").evaluate_all("(images) => images.every(img => img.complete && img.naturalWidth > 0)")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(ROOT / "docs" / "assets" / "walkthrough-light.png"), full_page=True)
        page.locator("#panel-rank").screenshot(path=str(ROOT / "docs" / "assets" / "illustrative-ranking-output.png"))
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
        bounds = page.locator("#hero-output img").bounding_box()
        assert bounds and bounds["y"] < 844, "The real output should begin in the first mobile viewport."
        page.screenshot(path=str(ROOT / "docs" / "assets" / "walkthrough-mobile.png"), full_page=True)
        assert not errors, f"Browser JavaScript errors: {errors}"
        browser.close()
    print("Light/dark/mobile rendering, embedded images, tabs, keyboard navigation, and browser errors checked.")


if __name__ == "__main__":
    main()
