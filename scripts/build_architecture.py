"""Generate matching SVG and editable Excalidraw diagrams without external services."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"


def build(simple=False):
    elements = []
    height = 440 if simple else 680
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Copilot Studio and Power BI architecture</title>',
        '<desc id="desc">A user asks a question. Copilot Studio uses curated model context and a reusable analytics capability. The Power BI connector queries the model as the user. Advice-only DAX returns without execution. The custom Agent365 example is not Microsoft Agent 365.</desc>',
        '<style>svg{--cp-bg:#f7f4ef;--cp-surface:#ffffff;--cp-border:#dedede;--cp-text:#242424;--cp-text-muted:#5c5c5c;--cp-accent:#b11f4b;--cp-accent-soft:rgba(177,31,75,0.08);font-family:"Segoe UI",Aptos,Calibri,sans-serif}text{fill:var(--cp-text)}.box{fill:var(--cp-surface);stroke:var(--cp-border)}.branch{fill:var(--cp-accent-soft);stroke:var(--cp-accent)}.line{fill:none;stroke:var(--cp-accent);stroke-width:2}</style>',
        '<defs><marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" style="fill:var(--cp-accent)"/></marker></defs>',
        f'<rect width="1440" height="{height}" style="fill:var(--cp-bg)"/>',
    ]

    def base(kind, identity, x, y, width, height):
        return {
            "id": identity, "type": kind, "x": x, "y": y,
            "width": width, "height": height, "angle": 0,
            "strokeColor": "#b11f4b", "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "seed": 1, "version": 1,
            "versionNonce": 1, "isDeleted": False, "groupIds": [],
            "frameId": None, "roundness": None, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
        }

    def text(identity, x, y, value, size=16, width=1200):
        line_count = value.count("\n") + 1
        item = base("text", identity, x, y, width, size * 2.5 * line_count)
        item.update({
            "text": value, "originalText": value, "fontSize": size,
            "fontFamily": 2, "textAlign": "left", "verticalAlign": "top",
            "strokeColor": "#000000", "containerId": None,
            "autoResize": True, "lineHeight": 1.25,
        })
        elements.append(item)
        for index, line in enumerate(value.split("\n")):
            svg.append(f'<text x="{x}" y="{y + size + index * size * 1.55}" font-size="{size}">{html.escape(line)}</text>')

    def box(identity, x, y, width, height, title, description, branch=False):
        item = base("rectangle", identity, x, y, width, height)
        item.update({"backgroundColor": "#f7f4ef" if branch else "#ffffff", "roundness": {"type": 3}})
        elements.append(item)
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" class="{"branch" if branch else "box"}"/>')
        text(identity + "-title", x + 16, y + 16, title, 18, width - 32)
        text(identity + "-description", x + 16, y + 58, description, 14, width - 32)

    def arrow(identity, x1, y1, x2, y2):
        item = base("arrow", identity, min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        item.update({
            "x": x1, "y": y1, "points": [[0, 0], [x2 - x1, y2 - y1]],
            "startBinding": None, "endBinding": None,
            "startArrowhead": None, "endArrowhead": "arrow",
        })
        elements.append(item)
        svg.append(f'<path class="line" marker-end="url(#arrowhead)" d="M{x1} {y1} L{x2} {y2}"/>')

    if simple:
        text("heading", 40, 24, "Message -> reusable capabilities -> answer", 30)
        text("subheading", 40, 80, "Copilot Studio orchestrates the work. A different question does not require another fixed-query tool.", 17)
        box("message", 40, 150, 300, 160, "Message", "Natural-language question\nSigned-in user")
        box("capabilities", 400, 150, 600, 160, "Copilot Studio + callable topics", "Get metadata -> generate DAX\nTopic validates -> Power BI executes as user")
        box("answer", 1060, 150, 340, 160, "Answer", "Explain returned rows\nOr label DAX as unexecuted")
        arrow("ask", 352, 230, 388, 230)
        arrow("respond", 1012, 230, 1048, 230)
        text("connector-note", 40, 350, "The standard Power BI connector queries the semantic model. No Fabric data agent or MCP is required.", 17, 1360)
        text("advice-note", 40, 390, "Advice skips the proposed business query; metadata authorization may still probe Power BI.", 16, 1360)
        write_assets("architecture-simple", elements, svg)
        return

    text("heading", 40, 24, "Copilot Studio + Power BI", 30)
    text("subheading", 40, 80, "A reusable pattern for compatible semantic models. No Fabric data agent required.", 17)
    nodes = [
        ("user", "Business question", "Authenticated user\nNatural-language request"),
        ("copilot", "Copilot Studio", "Retrieve metadata\nGenerate DAX expression"),
        ("analytics", "Query envelope", "Structural checks\nProjection and bounds"),
        ("connector", "Power BI connector", "Execute DAX\nEnd-user / Invoker"),
        ("model", "Semantic model", "Approved measures\nPermitted result data"),
    ]
    for index, (identity, title, description) in enumerate(nodes):
        x = 40 + index * 280
        box(identity, x, 160, 240, 170, title, description)
        if index < len(nodes) - 1:
            arrow(f"main-{index}", x + 244, 245, x + 272, 245)
    box("contract", 320, 400, 430, 150, "Governed metadata snapshot", "Owner preparation / refresh; caller visibility probe.\nNo complete business-meaning guarantee.", True)
    box("advice", 800, 400, 560, 150, "Advice: business query is unexecuted", "Metadata authorization may still query Power BI.\nOther query shapes still require validation.", True)
    arrow("grounding", 435, 395, 435, 340)
    arrow("advice-path", 560, 335, 870, 395)
    text("identity-note", 40, 580, "Power BI permissions and RLS follow the execution identity. Agent instructions are not an authorization boundary.", 16, 1350)
    text("model-note", 40, 625, "Example: Agent365 is a custom model/report name, not the Microsoft Agent 365 product.", 16, 1350)
    write_assets("architecture", elements, svg)


def write_assets(name, elements, svg):
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / (name + ".excalidraw")).write_text(json.dumps({
        "type": "excalidraw", "version": 2, "source": "copilot",
        "elements": elements, "appState": {"viewBackgroundColor": "#f7f4ef"}, "files": {},
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    svg.append("</svg>")
    (ASSETS / (name + ".svg")).write_text("\n".join(svg) + "\n", encoding="utf-8", newline="\n")
    print(f"Built {name}: editable Excalidraw and SVG.")


if __name__ == "__main__":
    build()
    build(simple=True)
