"""Isolated site checks; screenshots never overwrite publication/evidence assets."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import expect, sync_playwright
from build_site import DOWNLOAD_SOURCES

ROOT = Path(__file__).resolve().parents[1]
LIGHT = {
    "bg": "#f2f2f8", "bg-elevated": "#f8f7fc", "surface": "#ffffff",
    "surface-soft": "#f2f2f8", "border": "#e3dfed", "border-strong": "#9285aa",
    "text": "#102631", "text-muted": "#52637a", "text-soft": "#667287",
    "accent": "#7653ae", "accent-hover": "#58378b", "accent-soft": "#eee8f7",
    "accent-fg": "#ffffff", "link": "#066bc7", "success": "#207346",
    "danger": "#b4233e", "warning": "#8c6208", "chart-blue": "#0877dd",
    "chart-indigo": "#5364ba", "chart-purple": "#7653ae", "chart-violet": "#9651bb",
    "chart-magenta": "#b535c3", "chart-track": "#e8e3f0", "transparent": "transparent",
}
DARK = {
    **LIGHT,
    "bg": "#171717", "bg-elevated": "#222222", "surface": "#1f1f1f",
    "surface-soft": "#262626", "border": "#3b3b3b", "border-strong": "#858585",
    "text": "#f2f2f2", "text-muted": "#bdbdbd", "text-soft": "#aaaaaa",
    "accent": "#c3a0ef", "accent-hover": "#debeff", "accent-soft": "#2b2b2b",
    "accent-fg": "#181818", "link": "#80baff", "success": "#4ade80",
    "danger": "#f87171", "warning": "#fbbf24", "chart-blue": "#69aeff",
    "chart-indigo": "#98a5ff", "chart-purple": "#bc98ed", "chart-violet": "#d097ee",
    "chart-magenta": "#ed8fea", "chart-track": "#3b3b3b",
}


def theme_url(url, theme):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query.pop("scoutTheme", None)
    if theme:
        query["scoutTheme"] = theme
    return urlunsplit(parts._replace(query=urlencode(query), fragment=""))


def rgb(value):
    return "rgb(" + ", ".join(str(int(value[i:i + 2], 16)) for i in (1, 3, 5)) + ")"


def check_theme(page, theme):
    expected = DARK if theme == "dark" else LIGHT
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    actual = page.evaluate("""keys => {
        const style = getComputedStyle(document.documentElement);
        return Object.fromEntries(keys.map(key => [key, style.getPropertyValue('--cp-' + key).trim()]));
    }""", list(expected))
    assert actual == expected, (theme, actual)
    expect(page.locator("body")).to_have_css("background-color", rgb(expected["bg"]))
    expect(page.locator("body")).to_have_css("color", rgb(expected["text"]))
    expect(page.locator("body")).to_have_css("font-size", "16px")
    expect(page.locator("body")).to_have_css("line-height", "26.4px")
    expect(page.locator("header")).to_have_css("background-color", rgb(expected["surface"]))
    expect(page.locator(".panel").first).to_have_css("border-radius", "16px")
    expect(page.locator(".button").first).to_have_css("border-radius", "10px")
    expect(page.locator(".eyebrow").first).to_have_css("color", rgb(expected["accent"]))
    expect(page.locator(".note a").first).to_have_css("color", rgb(expected["accent-hover"]))
    heading = page.locator("h1")
    expect(heading).to_have_css("font-weight", "450")
    expect(heading).to_have_css("background-clip", "text")
    expect(heading).to_have_css("color", "rgba(0, 0, 0, 0)")
    expect(page.locator("h1 em")).to_have_css("color", "rgba(0, 0, 0, 0)")
    gradient = heading.evaluate("el => getComputedStyle(el).backgroundImage")
    assert gradient == (
        f'linear-gradient(105deg, {rgb(expected["chart-blue"])}, '
        f'{rgb(expected["chart-purple"])} 56%, {rgb(expected["chart-magenta"])})'
    ), gradient
    typography = heading.evaluate("""el => {
        const s = getComputedStyle(el);
        return [parseFloat(s.fontSize), parseFloat(s.lineHeight), parseFloat(s.letterSpacing)];
    }""")
    size, line_height, spacing = typography
    assert 32 <= size <= 56 and abs(line_height / size - 1.12) < .001
    assert abs(spacing / size + .035) < .001
    expect(page.locator("h2").first).to_have_css("font-weight", "600")
    expect(page.locator("h3").first).to_have_css("font-weight", "600")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
        theme, page.viewport_size, "Horizontal page overflow")


def check_interactions(page):
    page.keyboard.press("Tab")
    expect(page.locator(".skip")).to_be_focused()
    expect(page.locator(".skip")).to_have_css("outline-style", "solid")
    expect(page.locator(".skip")).to_have_css("outline-width", "3px")
    for link in page.locator("nav a").all():
        link.click()
        assert urlsplit(page.url).fragment == link.get_attribute("href")[1:]
    tabs = page.get_by_role("tab")
    for tab in tabs.all():
        tab.click()
        expect(tab).to_have_attribute("aria-selected", "true")
        expect(page.locator("#" + tab.get_attribute("aria-controls"))).to_be_visible()
        expect(page.get_by_role("tabpanel")).to_have_count(1)
    page.locator("#tab-dax").focus()
    page.locator("#tab-dax").press("ArrowUp")
    expect(page.locator("#tab-analyze")).to_be_focused()
    expect(page.locator("#panel-analyze")).to_be_visible()
    page.locator("#tab-analyze").press("Home")
    expect(page.locator("#tab-rank")).to_be_focused()
    page.locator("#tab-rank").press("End")
    expect(tabs.last).to_be_focused()
    page.locator("#tab-rank").click()
    # Mock the clipboard to test both outcomes without touching the host clipboard.
    page.evaluate("""() => Object.defineProperty(navigator, 'clipboard', {
        configurable: true, value: {writeText: async text => { window.copiedPrompt = text; }}
    })""")
    copy = page.locator('[data-copy="prompt-rank"]')
    copy.click()
    expect(page.locator("#copy-status")).to_have_text("Prompt copied.")
    assert page.evaluate("window.copiedPrompt") == page.locator("#prompt-rank").text_content()
    page.evaluate("() => Object.defineProperty(navigator, 'clipboard', {configurable: true, value: undefined})")
    copy.click()
    expect(page.locator("#copy-status")).to_contain_text("Select and copy the prompt text manually.")
    detail = page.locator("details").last
    summary = detail.locator("summary")
    summary.focus()
    summary.press("Enter")
    expect(detail).to_have_attribute("open", "")
    summary.press("Enter")
    expect(detail).not_to_have_attribute("open", "")


def check_theme_matrix(page, url, output):
    for width in (1440, 1024, 768, 640, 390, 320):
        page.set_viewport_size({"width": width, "height": 1080 if width > 640 else 844})
        for theme in ("light", "dark"):
            opposite = "dark" if theme == "light" else "light"
            page.emulate_media(color_scheme=opposite, reduced_motion="reduce")
            page.goto(theme_url(url, theme), wait_until="load")
            check_theme(page, theme)
            if width in (1440, 390):
                page.screenshot(path=str(output / f"walkthrough-{theme}-{width}.png"))
                check_interactions(page)
            toggle = page.locator("#theme-toggle")
            toggle.focus()
            toggle.press("Enter")
            check_theme(page, opposite)
            expect(toggle).to_have_text("Light theme" if opposite == "dark" else "Dark theme")
    for theme in ("light", "dark"):
        page.emulate_media(color_scheme=theme)
        page.goto(theme_url(url, None), wait_until="load")
        check_theme(page, theme)
    page.emulate_media(forced_colors="active")
    expect(page.locator("h1")).to_have_css("background-image", "none")
    assert page.locator("h1").evaluate("el => getComputedStyle(el).color") != "rgba(0, 0, 0, 0)"
    page.emulate_media(forced_colors="none", media="print")
    expect(page.locator("h1")).to_have_css("background-image", "none")
    expect(page.locator("h1")).to_have_css("color", rgb(DARK["text"]))
    page.emulate_media(media="screen")


def check_published_downloads(page, url):
    if urlsplit(url).scheme not in ("http", "https"):
        return
    for link in page.locator("a[download]").all():
        relative = link.get_attribute("href")
        with page.expect_download() as pending:
            link.click()
        download = pending.value
        assert download.failure() is None, relative
        expected = (ROOT / "docs" / relative).read_bytes()
        assert Path(download.path()).read_bytes() == expected, f"Download differs: {relative}"
    solution = page.get_by_role("link", name="Download solution ZIP", exact=True)
    response = page.context.request.get(solution.get_attribute("href"))
    assert response.ok, f"Solution download HTTP {response.status}"
    assert response.body() == (ROOT / "solution" / "PowerBIQueryStarter_unmanaged.zip").read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Check the published site instead of the local HTML.")
    parser.add_argument("--output-dir", type=Path, help="Keep screenshots outside the repository.")
    parser.add_argument("--browser-channel", choices=("msedge", "chrome", "chromium"), default="msedge")
    args = parser.parse_args()
    if args.output_dir and args.output_dir.resolve().is_relative_to(ROOT):
        parser.error("--output-dir must be outside the repository to protect evidence images.")
    with TemporaryDirectory(prefix="powerbi-site-preview-") as temporary, sync_playwright() as playwright:
        output = args.output_dir or Path(temporary)
        output.mkdir(parents=True, exist_ok=True)
        channel = None if args.browser_channel == "chromium" else args.browser_channel
        browser = playwright.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        url = args.url or (ROOT / "docs" / "index.html").as_uri()
        page.goto(theme_url(url, "light"), wait_until="load")
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
        page.locator("#panel-rank").screenshot(path=str(output / "illustrative-ranking-output.png"))
        page.locator("#tab-dax").click()
        assert page.locator("#panel-dax").is_visible()
        page.locator("#tab-dax").press("ArrowUp")
        assert page.locator("#panel-analyze").is_visible()
        page.locator("#tab-analyze").press("Home")
        assert page.locator("#panel-rank").is_visible()
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.evaluate("window.scrollTo(0,0)")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(theme_url(url, "light"), wait_until="load")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile layout overflows."
        bounds = page.locator("#hero-output img").bounding_box()
        assert bounds and bounds["y"] < 844, "The real output should begin in the first mobile viewport."
        check_theme_matrix(page, url, output)
        check_published_downloads(page, url)
        assert not errors, f"Browser JavaScript errors: {errors}"
        browser.close()
    print("Checked light/dark at six viewport widths, system preference, theme toggle, title gradient, "
          "focus, tabs, copy feedback, navigation, images, download links, forced colors, and print.")


if __name__ == "__main__":
    main()
