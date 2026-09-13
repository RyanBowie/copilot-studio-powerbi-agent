"""Redact genuine captures with opaque pixels; optionally combine a prompt and response."""
import argparse
import json
import math
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render(spec):
    source = Path(spec["source"]).resolve()
    output = Path(spec["output"]).resolve()
    if source == output:
        raise ValueError("Keep the original capture separate from its publication derivative.")
    with Image.open(source) as original:
        image = original.convert("RGB")
    font = ImageFont.truetype(str(Path(os.environ["WINDIR"]) / "Fonts" / "segoeui.ttf"), 15)
    draw = ImageDraw.Draw(image)
    for mask in spec.get("redactions", []):
        x, y, width, height = (float(mask[key]) for key in ("x", "y", "width", "height"))
        if not all(math.isfinite(v) for v in (x, y, width, height)) or width <= 0 or height <= 0:
            raise ValueError("Invalid redaction rectangle.")
        left, top = max(0, math.floor(x) - 2), max(0, math.floor(y) - 2)
        right = min(image.width - 1, math.ceil(x + width) + 2)
        bottom = min(image.height - 1, math.ceil(y + height) + 2)
        if left >= right or top >= bottom:
            raise ValueError("Redaction rectangle falls outside the capture.")
        draw.rectangle((left, top, right, bottom), fill="#242424")
        label = mask.get("label", "Redacted")
        if draw.textbbox((0, 0), label, font=font)[2] < right - left - 12:
            draw.text((left + 6, top + 3), label, fill="#ffffff", font=font)
    parts = []
    if spec.get("prompt"):
        with Image.open(spec["prompt"]) as prompt:
            parts.append(prompt.convert("RGB"))
    parts.append(image)
    width = max(part.width for part in parts) + 32
    caption = spec["caption"]
    lines = textwrap.wrap(caption, width=max(30, (width - 32) // 8))
    header = 24 + len(lines) * 22
    canvas = Image.new("RGB", (width, header + sum(part.height + 16 for part in parts)), "#ffffff")
    caption_draw = ImageDraw.Draw(canvas)
    for index, line in enumerate(lines):
        caption_draw.text((16, 12 + index * 22), line, fill="#242424", font=font)
    y = header
    for part in parts:
        canvas.paste(part, (16, y))
        y += part.height + 16
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG")
    print(f"Created reviewed-capture derivative: {output.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path, help="Private JSON specification; never commit originals or private paths.")
    args = parser.parse_args()
    render(json.loads(args.spec.read_text(encoding="utf-8")))
