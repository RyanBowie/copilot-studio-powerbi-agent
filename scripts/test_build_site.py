"""The embedded site must be identical across Windows and Linux checkouts."""
import base64
from pathlib import Path
import tempfile
import unittest

from build_site import image_uri


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


if __name__ == "__main__":
    unittest.main()
