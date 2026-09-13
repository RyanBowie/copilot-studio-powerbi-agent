"""Build the dependency-free, self-contained walkthrough from reviewed local assets."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    html = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    images = {
        "__SIMPLE_ARCHITECTURE__": "architecture-simple.svg",
        "__M365_CONSENT__": "m365-connection-consent.png",
        "__M365_RANKING__": "m365-ranking-redacted.png",
        "__M365_FOLLOWUP__": "m365-followup-redacted.png",
        "__M365_ADVICE__": "m365-dax-advice.png",
        "__CURRENT_TOPICS__": "studio-current-topics.png",
        "__QUERY_DETAILS__": "studio-query-details.png",
        "__QUERY_INPUT__": "studio-query-input.png",
        "__POWERBI_ACTION__": "studio-powerbi-action.png",
        "__MODEL_SELECTION__": "studio-model-selection.png",
        "__UPDATED_STARTER__": "studio-updated-starter.png",
    }
    for marker, filename in images.items():
        if html.count(marker) != 1:
            raise ValueError(f"Expected one image marker: {marker}")
        image = ROOT / "docs" / "assets" / filename
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        mime = "image/svg+xml" if image.suffix == ".svg" else "image/png"
        html = html.replace(marker, f"data:{mime};base64,{encoded}")
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print("Built docs/index.html with embedded screenshots.")


if __name__ == "__main__":
    main()
