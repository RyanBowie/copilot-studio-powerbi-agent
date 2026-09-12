"""Build the dependency-free, self-contained walkthrough from reviewed local assets."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    html = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    images = {
        "__TOOLS_SCREENSHOT__": "tools-initial-poc.png",
        "__CONSENT_SCREENSHOT__": "connection-approval.png",
    }
    for marker, filename in images.items():
        if html.count(marker) != 1:
            raise ValueError(f"Expected one image marker: {marker}")
        image = ROOT / "docs" / "assets" / filename
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        html = html.replace(marker, f"data:image/png;base64,{encoded}")
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print("Built docs/index.html with embedded screenshots.")


if __name__ == "__main__":
    main()
