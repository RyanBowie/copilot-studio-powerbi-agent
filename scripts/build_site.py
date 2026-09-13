"""Build the dependency-free, self-contained walkthrough from reviewed local assets."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def image_uri(image):
    if image.suffix == ".svg":
        # Git checkout line endings must not change the embedded text asset.
        data = image.read_text(encoding="utf-8").encode("utf-8")
        mime = "image/svg+xml"
    else:
        data = image.read_bytes()
        mime = "image/png"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def main():
    html = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    images = {
        "__HERO_PROMPT__": "m365-prompt-intro.png",
        "__HERO_OUTPUT__": "m365-output-intro.png",
        "__SIMPLE_ARCHITECTURE__": "architecture-simple.svg",
        "__TESTED_MODEL_REPORT__": "powerbi-agents-report.png",
        "__STUDIO_METADATA_EXAMPLE__": "studio-metadata-example.png",
        "__M365_CONSENT__": "m365-connection-consent.png",
        "__M365_RANKING__": "m365-ranking-redacted.png",
        "__M365_FOLLOWUP__": "m365-followup-redacted.png",
        "__M365_ADVICE__": "m365-dax-advice.png",
        "__CURRENT_TOPICS__": "studio-current-topics.png",
        "__QUERY_DETAILS__": "studio-query-details.png",
        "__QUERY_INPUT__": "studio-query-input.png",
        "__POWERBI_ACTION__": "studio-powerbi-action.png",
        "__MODEL_SELECTION__": "studio-model-selection.png",
    }
    for marker, filename in images.items():
        if html.count(marker) != 1:
            raise ValueError(f"Expected one image marker: {marker}")
        image = ROOT / "docs" / "assets" / filename
        html = html.replace(marker, image_uri(image))
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print("Built docs/index.html with embedded screenshots.")


if __name__ == "__main__":
    main()
