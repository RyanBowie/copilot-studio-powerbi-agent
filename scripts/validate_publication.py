"""Check publication assets, local HTML links, and common accidental deployment data."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "__pycache__", ".venv", "node_modules"}
TEXT_SUFFIXES = {".md", ".html", ".yml", ".yaml", ".json", ".py", ".js", ".cjs", ".svg", ".excalidraw", ".txt"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = []
        self.links = []
        self.images_missing_alt = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicates.append(attrs["id"])
            self.ids.add(attrs["id"])
        if tag in {"a", "img", "script", "link"}:
            ref = attrs.get("href") if tag in {"a", "link"} else attrs.get("src")
            if ref:
                self.links.append(ref)
        if tag == "img" and not attrs.get("alt"):
            self.images_missing_alt += 1


def main():
    errors = []
    required = [
        "README.md", "docs/index.html", "docs/architecture.md", "docs/setup.md",
        "docs/examples.md", "docs/verification.md", "docs/public-release.md",
        "docs/capabilities-and-limits.md", "docs/scalability-experiment.md",
        "docs/date-filtering.md",
        "docs/assets/architecture.excalidraw", "docs/assets/architecture.svg",
        "docs/assets/tools-initial-poc.png", "docs/assets/connection-approval.png",
        "agent/README.md",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f"Missing publication asset: {name}")

    # Live deployment GUIDs are not needed in this public template.
    guid = re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b")
    token = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+)")
    private_url = re.compile(r"https://[A-Za-z0-9-]+\.(?:crm\d*\.dynamics\.com|onmicrosoft\.com)", re.I)
    file_count = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        relative = str(path.relative_to(ROOT))
        if (
            path.suffix.lower() in {".zip", ".har", ".log"}
            or ".mcs" in path.parts
            or ".generated-private" in path.parts
            or path.name.endswith(".private.json")
        ):
            errors.append(f"Tenant-bound/private artifact: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        file_count += 1
        text = path.read_text(encoding="utf-8")
        # Embedded PNGs are binary assets, not text to scan for coincidental patterns.
        scan_text = re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "EMBEDDED_IMAGE", text)
        for label, pattern in [("deployment GUID", guid), ("credential", token), ("private tenant URL", private_url)]:
            if pattern.search(scan_text):
                errors.append(f"Possible {label}: {relative}")
        if "C:\\Users\\" in scan_text and path.name != "validate_publication.py":
            errors.append(f"Local user path: {relative}")
        if path.suffix.lower() in {".json", ".excalidraw"}:
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON in {relative}: {exc}")

    index = ROOT / "docs" / "index.html"
    if index.exists():
        source = index.read_text(encoding="utf-8")
        page = Page()
        page.feed(source)
        if page.duplicates:
            errors.append(f"Duplicate HTML IDs: {page.duplicates}")
        if page.images_missing_alt:
            errors.append("HTML images are missing alternative text.")
        if "__TOOLS_SCREENSHOT__" in source or "__CONSENT_SCREENSHOT__" in source:
            errors.append("Site still contains unresolved screenshot markers.")
        for ref in page.links:
            url = urlparse(ref)
            if url.scheme or url.netloc:
                continue
            if not url.path:
                if url.fragment and unquote(url.fragment) not in page.ids:
                    errors.append(f"Broken section link: {ref}")
            elif not (index.parent / unquote(url.path)).is_file():
                errors.append(f"Broken local asset link: {ref}")
        if "not the Microsoft product" not in source:
            errors.append("Site is missing the custom-model product distinction.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Publication checks passed for {file_count} text assets. Manually review screenshots and history before release.")


if __name__ == "__main__":
    main()
