"""The embedded site must be identical across Windows and Linux checkouts."""
import base64
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote, urlparse

from build_site import DOWNLOAD_SOURCES, SOLUTION_DOWNLOADS, ROOT, build_downloads, image_uri
from validate_publication import Page


class ImageEmbeddingTests(unittest.TestCase):
    def test_svg_checkout_line_endings_are_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "diagram.svg"
            source = b'<svg xmlns="http://www.w3.org/2000/svg">\n</svg>\n'
            image.write_bytes(source)
            expected = image_uri(image)
            image.write_bytes(source.replace(b"\n", b"\r\n"))
            self.assertEqual(image_uri(image), expected)
            self.assertEqual(base64.b64decode(expected.split(",", 1)[1]), source)

    def test_png_bytes_are_not_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "capture.png"
            source = b"\x89PNG\r\n\x1a\n\x00\r\n"
            image.write_bytes(source)
            actual = image_uri(image)
            self.assertTrue(actual.startswith("data:image/png;base64,"))
            self.assertEqual(base64.b64decode(actual.split(",", 1)[1]), source)

    def test_downloads_preserve_complete_sources_and_normalize_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename, relative in DOWNLOAD_SOURCES.items():
                source = root / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes((filename + "\r\n" + "  complete source line\r\n" * 1500).encode("utf-8"))
            for filename, relative in SOLUTION_DOWNLOADS.items():
                source = root / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(b"PK\x03\x04\r\n\x00\xff" + filename.encode("utf-8"))
            build_downloads(root)
            self.assertEqual(len(list((root / "docs" / "downloads").iterdir())),
                             len(DOWNLOAD_SOURCES) + len(SOLUTION_DOWNLOADS))
            for filename, relative in DOWNLOAD_SOURCES.items():
                expected = (root / relative).read_text(encoding="utf-8").encode("utf-8")
                self.assertEqual((root / "docs" / "downloads" / filename).read_bytes(), expected)
            for filename, relative in SOLUTION_DOWNLOADS.items():
                self.assertEqual((root / "docs" / "downloads" / filename).read_bytes(),
                                 (root / relative).read_bytes())

    def test_primary_solution_is_a_same_origin_download(self):
        source = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
        page = Page()
        page.feed(source)
        self.assertIn("downloads/PowerBIQueryRuntime_unmanaged.zip", page.links)
        self.assertNotIn("PowerBIQueryStarter_unmanaged.zip", source)
        self.assertIn('href="downloads/PowerBIQueryRuntime_unmanaged.zip" download', source)

    def test_documentation_links_work_in_github_and_pages_contexts(self):
        docs = (ROOT / "docs").resolve()
        for document in docs.glob("*.md"):
            name = document.name
            text = document.read_text(encoding="utf-8")
            for ref in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                url = urlparse(ref)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (docs / unquote(url.path)).resolve()
                self.assertTrue(target.is_relative_to(docs),
                                f"{name}: repository-only links need an explicit GitHub URL: {ref}")
                self.assertTrue(target.exists(), f"{name}: missing publication link: {ref}")


if __name__ == "__main__":
    unittest.main()
