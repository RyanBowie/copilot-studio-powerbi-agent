"""Check publication assets, local HTML links, and common accidental deployment data."""
import json
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from build_site import DOWNLOAD_SOURCES

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "__pycache__", ".venv", "node_modules"}
TEXT_SUFFIXES = {".md", ".html", ".yml", ".yaml", ".json", ".py", ".js", ".cjs", ".cs", ".csproj", ".svg", ".excalidraw", ".txt", ".xml"}
SOLUTION_ZIP = ROOT / "solution" / "PowerBIQueryStarter_unmanaged.zip"


def solution_texts(path):
    """Only accept the reviewed starter archive, and inspect every decompressed entry."""
    manifest = json.loads((path.parent / "package-manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Solution ZIP checksum differs from its manifest.")
    observation = json.loads((path.parent / "import-verification.json").read_text(encoding="utf-8"))
    if observation["sha256"] != manifest["sha256"]:
        raise ValueError("Import observation is for a different ZIP; verify this rebuilt artifact.")
    if manifest["configured"] or manifest["publishOnImport"] or manifest["managed"]:
        raise ValueError("Publication package must remain an unconfigured unmanaged starter.")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if (len(entries) != len({item.filename for item in entries})
                or len(entries) > 30 or sum(item.file_size for item in entries) > 2_000_000
                or set(archive.namelist()) != set(manifest["entries"])):
            raise ValueError("Unexpected or oversized solution archive inventory.")
        result = []
        for item in entries:
            name = item.filename
            if (name.startswith(("/", "\\")) or ".." in name.split("/")
                    or "\\" in name or item.flag_bits & 1):
                raise ValueError("Unsafe solution archive entry.")
            if not (name.endswith((".xml", ".json", "/data"))):
                raise ValueError("Unexpected nontext solution entry: " + name)
            data = archive.read(item)
            expected = manifest["entries"][name]
            if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
                raise ValueError("Solution entry differs from manifest: " + name)
            text = data.decode("utf-8-sig")
            if name.endswith(".xml"):
                ET.fromstring(text)
            if name.endswith(".json"):
                json.loads(text)
            # PAC aggregates the two XML manifests; all other payloads must match tracked source.
            if name not in {"solution.xml", "customizations.xml", "[Content_Types].xml"}:
                source = path.parent / "src" / name
                if source.read_text(encoding="utf-8-sig").replace("\r\n", "\n") != text.replace("\r\n", "\n"):
                    raise ValueError("Solution payload differs from source: " + name)
            result.append((str(path.relative_to(ROOT)) + "::" + name, text))
        config = json.loads(archive.read("bots/poc_PowerBIQueryStarter/configuration.json"))
        if config["publishOnImport"] or config["channels"]:
            raise ValueError("Starter must not publish or configure channels on import.")
        return result


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
        "docs/assets/architecture-simple.excalidraw", "docs/assets/architecture-simple.svg",
        "docs/assets/studio-query-details.png", "docs/assets/studio-query-input.png",
        "docs/assets/studio-powerbi-action.png", "docs/assets/m365-connection-consent.png",
        "agent/README.md",
        "solution/PowerBIQueryStarter_unmanaged.zip", "solution/package-manifest.json",
        "docs/solution-import.md",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f"Missing publication asset: {name}")
    for filename, source in DOWNLOAD_SOURCES.items():
        download = ROOT / "docs" / "downloads" / filename
        if not download.is_file():
            errors.append(f"Missing complete YAML download: {filename}")
        elif download.read_text(encoding="utf-8") != (ROOT / source).read_text(encoding="utf-8"):
            errors.append(f"YAML download differs from complete source: {filename}")

    # Live deployment GUIDs are not needed in this public template.
    guid = re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b")
    token = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+)")
    private_url = re.compile(r"https://[A-Za-z0-9-]+\.(?:crm\d*\.dynamics\.com|onmicrosoft\.com)", re.I)
    file_count = 0
    archive_texts = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        relative = str(path.relative_to(ROOT))
        if (
            (path.suffix.lower() == ".zip" and path != SOLUTION_ZIP)
            or path.suffix.lower() in {".har", ".log"}
            or ".mcs" in path.parts
            or ".generated-private" in path.parts
            or path.name.endswith(".private.json")
        ):
            errors.append(f"Tenant-bound/private artifact: {relative}")
        if path == SOLUTION_ZIP:
            try:
                archive_texts.extend(solution_texts(path))
            except (ValueError, KeyError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
                errors.append(f"Invalid starter solution: {exc}")
        if path.suffix.lower() not in TEXT_SUFFIXES and not (path.name == "data" and "solution" in path.parts):
            continue
        file_count += 1
        text = path.read_text(encoding="utf-8")
        # SVG source is scanned separately; base64 is not meaningful plaintext.
        scan_text = re.sub(r"data:image/(?:png|svg\+xml);base64,[A-Za-z0-9+/=]+", "EMBEDDED_IMAGE", text)
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

    for relative, text in archive_texts:
        file_count += 1
        for label, pattern in [("deployment GUID", guid), ("credential", token), ("private tenant URL", private_url)]:
            if pattern.search(text):
                errors.append(f"Possible {label} inside archive: {relative}")
        if "C:\\Users\\" in text:
            errors.append(f"Local user path inside archive: {relative}")

    index = ROOT / "docs" / "index.html"
    if index.exists():
        source = index.read_text(encoding="utf-8")
        page = Page()
        page.feed(source)
        if page.duplicates:
            errors.append(f"Duplicate HTML IDs: {page.duplicates}")
        if page.images_missing_alt:
            errors.append("HTML images are missing alternative text.")
        if re.search(r"__[A-Z][A-Z0-9_]*__", re.sub(r"data:image/(?:png|svg\+xml);base64,[A-Za-z0-9+/=]+", "", source)):
            errors.append("Site still contains unresolved screenshot markers.")
        template = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
        for retired in ("__TOOLS_SCREENSHOT__", "__CURRENT_TOOLS__", "Historical initial PoC"):
            if retired in template:
                errors.append(f"Walkthrough contains retired screenshot content: {retired}")
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
