#!/usr/bin/env python3
"""Rebuild the original vector artwork. No downloads, fonts or packages needed."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement

from profile_svg import CYAN, INK, MUTED, ORANGE, PINK, WHITE, WIDTH, Svg

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def animated_waves(canvas: Svg, width: int, height: int) -> None:
    """Loop two full wave periods inside the card's rounded outline."""
    definitions = canvas.root.find("defs")
    if definitions is None:
        definitions = SubElement(canvas.root, "defs")
    clip = SubElement(definitions, "clipPath", {"id": "wave-frame"})
    SubElement(
        clip,
        "rect",
        {
            "x": "1",
            "y": "1",
            "width": str(width - 2),
            "height": str(height - 2),
            "rx": "20",
        },
    )
    canvas.element("style").text = (
        f"@keyframes drift{{to{{transform:translateX(-{width}px)}}}}"
        ".wave{animation:drift 12s linear infinite}"
        ".wave-back{animation-duration:18s;animation-direction:reverse}"
        "@media(prefers-reduced-motion:reduce){.wave{animation:none}}"
    )
    frame = canvas.element("g", clip_path="url(#wave-frame)")
    paint = canvas.gradient("wave-colour", ("#9268ef", "#e878b1", "#73d1ed"))
    quarter = width / 4
    amplitude = 14 if width > 600 else 9
    for offset, opacity, class_name in (
        (0, ".45", "wave wave-back"),
        (10, ".35", "wave"),
    ):
        baseline = height - 23 + offset
        path = (
            f"M 0 {baseline} "
            f"C {quarter} {baseline - amplitude} {3 * quarter} {baseline + amplitude} {width} {baseline} "
            f"C {5 * quarter} {baseline - amplitude} {7 * quarter} {baseline + amplitude} {2 * width} {baseline} "
            f"L {2 * width} {height + 20} L 0 {height + 20} Z"
        )
        SubElement(
            frame,
            "path",
            {"d": path, "fill": paint, "opacity": opacity, "class": class_name},
        )


def typing_banner(width: int = WIDTH) -> Svg:
    roles = (
        "PHP & JavaScript Developer",
        "Tiki Wiki CMS Groupware Contributor",
        "Regression Tests & Browser QA",
        "Technical Writer / HNG12 Finalist",
    )
    canvas = Svg(width, 64, "Development, open source and testing", "; ".join(roles))
    canvas.root.remove(canvas.root.find("rect"))
    canvas.element("style").text = (
        ".role{opacity:0;animation:role-phase 16s linear infinite}"
        "@keyframes role-phase{0%,24.99%{opacity:1}25%,100%{opacity:0}}"
        ".reveal{animation:type-line 4s steps(34,end) infinite}"
        ".caret{animation:move-caret 4s steps(34,end) infinite,blink .8s steps(1,end) infinite}"
        "@keyframes type-line{0%,8%{width:0}45%,77%{width:var(--line-width)}98%,100%{width:0}}"
        "@keyframes move-caret{0%,8%{transform:translateX(0)}"
        "45%,77%{transform:translateX(var(--line-width))}98%,100%{transform:translateX(0)}}"
        "@keyframes blink{50%{opacity:0}}"
        "@media(prefers-reduced-motion:reduce){.role{animation:none;opacity:0}"
        ".role-first{opacity:1}.reveal{animation:none;width:var(--line-width)}.caret{display:none}}"
    )
    definitions = SubElement(canvas.root, "defs")
    font_size = 18 if width < 600 else 28
    for index, role in enumerate(roles):
        line_width = round(len(role) * font_size * 0.6)
        left = (width - line_width) / 2
        clip = SubElement(definitions, "clipPath", {"id": f"typing-{index}"})
        SubElement(
            clip,
            "rect",
            {
                "x": str(left),
                "y": "8",
                "height": "48",
                "width": "0",
                "class": "reveal",
                "style": f"--line-width:{line_width}px",
            },
        )
        group = canvas.element(
            "g",
            class_="role role-first" if index == 0 else "role",
            style=f"animation-delay:{index * 4}s;--line-width:{line_width}px",
        )
        SubElement(
            group,
            "text",
            {
                "x": str(left),
                "y": "42",
                "font-size": str(font_size),
                "font-family": "DejaVu Sans Mono,monospace",
                "fill": PINK,
                "textLength": str(line_width),
                "lengthAdjust": "spacingAndGlyphs",
                "clip-path": f"url(#typing-{index})",
            },
        ).text = role
        SubElement(
            group,
            "rect",
            {
                "x": str(left),
                "y": "17",
                "width": "2",
                "height": "30",
                "fill": CYAN,
                "class": "caret",
            },
        )
    return canvas


def hero() -> Svg:
    canvas = Svg(
        WIDTH,
        360,
        "Joël Magene — Web developer and Tiki contributor",
        "Also known as SemJo. PHP, JavaScript, Tiki Wiki CMS Groupware and QA. "
        "Civil engineer turned developer. HNG12 finalist. Based in Goma / Gisenyi.",
    )
    glow = canvas.gradient("hero-glow", ("#8e5cff", "#d95ca5", "#54b8ee"))
    canvas.rect(1, 1, 1198, 358, glow, radius=20, fill_opacity="0.13")
    canvas.circle(1048, 95, 132, "#9b70ff", opacity="0.07", class_="signal")
    canvas.circle(1105, 120, 172, "none", stroke="#b797ff", stroke_opacity="0.16")
    canvas.element("style").text = (
        ".signal{animation:breath 5s ease-in-out infinite}"
        "@keyframes breath{0%,100%{opacity:.05}50%{opacity:.18}}"
        "@media(prefers-reduced-motion:reduce){.signal{animation:none}}"
    )
    canvas.label(42, 47, "WEB DEVELOPER / TIKI CONTRIBUTOR", CYAN)
    canvas.text(38, 135, "Joël Magene", 70, WHITE, 700, letter_spacing=-3)
    canvas.text(43, 172, "aka SemJo", 20, PINK, mono=True)
    canvas.text(43, 221, "PHP. JavaScript. Open source. QA.", 26, WHITE, 500)
    canvas.text(
        43,
        258,
        "I build web applications and fix the details that get in the way.",
        17,
        MUTED,
    )
    canvas.line(43, 285, 741, 285, "#62507f", stroke_opacity="0.5")
    canvas.text(43, 312, "Goma / Gisenyi", 13, MUTED, mono=True)
    canvas.text(264, 312, "HNG12 finalist · top 432 / 11,285", 13, CYAN, mono=True)
    canvas.rect(825, 73, 324, 206, "#1a1833", radius=16, stroke="#776291")
    for x, color in ((846, PINK), (861, ORANGE), (876, CYAN)):
        canvas.circle(x, 94, 4, color)
    canvas.text(1012, 99, "THE DAY-TO-DAY", 11, MUTED, mono=True, text_anchor="middle")
    for x, label, color in (
        (846, "PHP", "#c8b2ff"),
        (941, "JS", ORANGE),
        (1036, "QA", CYAN),
    ):
        canvas.rect(
            x, 119, 75, 43, "#2a2344", radius=10, stroke=color, stroke_opacity="0.6"
        )
        canvas.text(x + 37, 147, label, 19, color, 700, mono=True, text_anchor="middle")
    for y, label in (
        (190, "Reproduce the issue"),
        (219, "Fix it and add tests"),
        (248, "Check it in the browser"),
    ):
        canvas.circle(851, y - 5, 4, PINK)
        canvas.text(866, y, label, 14, WHITE)
    animated_waves(canvas, WIDTH, 360)
    return canvas


def mobile_hero() -> Svg:
    canvas = Svg(480, 260, "Joël Magene — Web developer and Tiki contributor")
    glow = canvas.gradient("hero-glow", ("#8e5cff", "#d95ca5", "#54b8ee"))
    canvas.rect(1, 1, 478, 258, glow, radius=20, fill_opacity="0.15")
    canvas.label(26, 36, "WEB DEVELOPER / TIKI CONTRIBUTOR", CYAN)
    canvas.text(24, 102, "Joël Magene", 47, WHITE, 700, letter_spacing=-2)
    canvas.text(28, 133, "aka SemJo", 17, PINK, mono=True)
    canvas.text(28, 174, "PHP · JavaScript · Open source · QA", 18, WHITE)
    canvas.text(28, 211, "Goma / Gisenyi", 13, MUTED, mono=True)
    canvas.text(28, 228, "HNG12 finalist · top 432 / 11,285", 13, CYAN, mono=True)
    animated_waves(canvas, 480, 260)
    return canvas


def illustrate_ads(canvas: Svg, accent: str) -> None:
    canvas.rect(43, 72, 148, 142, "#2c2345", radius=8)
    canvas.label(55, 96, "CREATE", accent)
    for index, width in enumerate((108, 92, 108)):
        canvas.rect(55, 112 + index * 21, width, 10, "#554164", radius=3)
    canvas.rect(55, 181, 102, 20, accent, radius=5)
    canvas.text(68, 195, "Generate", 10, INK, 700)
    for x, color in ((207, accent), (373, CYAN)):
        canvas.rect(x, 72, 149, 142, "#302545", radius=8)
        canvas.circle(x + 75, 130, 36, "none", stroke=color, stroke_width=12)
        canvas.line(x + 22, 184, x + 111, 184, color, stroke_width=5)
        canvas.line(x + 22, 197, x + 87, 197, "#7a668c", stroke_width=4)


def illustrate_text(canvas: Svg, accent: str) -> None:
    canvas.rect(46, 75, 58, 26, accent, radius=6)
    canvas.text(59, 93, "Aa", 16, INK, 700)
    canvas.text(119, 94, "Chrome AI / Text tools", 15, WHITE, 700)
    canvas.rect(46, 114, 351, 37, "#32304e", radius=8)
    canvas.text(60, 138, "Detect. Summarize. Translate.", 14, MUTED)
    canvas.rect(149, 164, 380, 40, "#253b53", radius=8)
    canvas.text(167, 189, "Language detected · Summary ready", 14, accent)


def illustrate_ticket(canvas: Svg, accent: str) -> None:
    canvas.rect(73, 79, 434, 128, "#292140", radius=12, stroke=accent)
    canvas.line(383, 89, 383, 197, accent, stroke_dasharray="4 5")
    canvas.label(97, 109, "YOU’RE ON THE LIST", accent)
    canvas.text(97, 143, "Hello, world.", 26, WHITE, 700)
    canvas.text(98, 176, "FORM → VALIDATE → GENERATE", 11, MUTED, mono=True)
    for x in (403, 411, 425, 431, 443, 450, 460, 474):
        canvas.rect(x, 101, 4 if x % 2 else 7, 82, accent, radius=0)


def illustrate_tiki(canvas: Svg, accent: str) -> None:
    for index, (label, y) in enumerate(
        (
            ("PHP / Smarty / JavaScript", 86),
            ("Calendar / languages / SQL", 130),
            ("PHPUnit / coverage / QA", 174),
        )
    ):
        canvas.circle(61, y + 2, 10, "#352844", stroke=accent)
        canvas.path(f"M 56 {y + 2} l 4 4 l 7 -8", accent, 2)
        canvas.text(84, y + 7, label, 17, WHITE, 500)
        if index < 2:
            canvas.line(62, y + 13, 62, y + 32, "#66456b")


@dataclass(frozen=True)
class Project:
    filename: str
    name: str
    category: str
    stack: str
    accent: str
    illustrate: Callable[[Svg, str], None]


PROJECTS = (
    Project(
        filename="project-tiki.svg",
        name="Tiki CMS Groupware",
        category="OPEN SOURCE / CONTRIBUTIONS",
        stack="PHP · JavaScript · PHPUnit",
        accent="#c5a6ff",
        illustrate=illustrate_tiki,
    ),
    Project(
        filename="project-genz.svg",
        name="Genz.ad",
        category="TEAM PROJECT / AI",
        stack="Next.js · TypeScript · Tailwind",
        accent=PINK,
        illustrate=illustrate_ads,
    ),
    Project(
        filename="project-gtext.svg",
        name="GText AI",
        category="BROWSER AI / WEB APP",
        stack="Next.js · JavaScript · Chrome AI",
        accent=CYAN,
        illustrate=illustrate_text,
    ),
    Project(
        filename="project-ticket.svg",
        name="Conference Ticket Generator",
        category="FORMS / INTERACTION",
        stack="Next.js · Tailwind · Zod",
        accent="#c5a6ff",
        illustrate=illustrate_ticket,
    ),
)


def project_card(project: Project, position: int) -> Svg:
    canvas = Svg(
        580,
        340,
        project.name,
        f"Illustrated project card. {project.category}. {project.stack}.",
    )
    canvas.label(26, 33, f"{position:02} / {project.category}", project.accent)
    canvas.text(548, 34, "↗", 25, project.accent, text_anchor="end")
    canvas.rect(26, 55, 528, 176, "#211d38", radius=12)
    project.illustrate(canvas, project.accent)
    canvas.text(26, 272, project.name, 27, WHITE, 700, letter_spacing=-0.7)
    canvas.text(26, 308, project.stack, 13, MUTED, mono=True)
    return canvas


def footer() -> Svg:
    canvas = Svg(WIDTH, 140, "Have a project or a bug worth looking at? Get in touch.")
    glow = canvas.gradient("contact-glow", ("#9268ef", "#e878b1", "#73d1ed"))
    canvas.rect(1, 1, 1198, 138, glow, radius=20, fill_opacity="0.12")
    canvas.text(
        32,
        53,
        "Have a project or a bug worth looking at?",
        31,
        WHITE,
        700,
        letter_spacing=-1,
    )
    canvas.text(34, 100, "semjomagene@gmail.com", 20, CYAN, mono=True)
    animated_waves(canvas, WIDTH, 140)
    canvas.circle(1136, 70, 28, "#ad83eb")
    canvas.text(1122, 81, "↗", 32, WHITE, 700)
    return canvas


def skill_icons(mobile: bool = False) -> Svg:
    """Add staggered entrances to local Skill Icons; leave the licensed originals intact."""
    name = "stack-mobile.svg" if mobile else "stack.svg"
    source = ET.parse(ASSETS / "vendor" / name).getroot()
    canvas = Svg(
        1,
        1,
        "Development tools",
        "PHP, JavaScript, TypeScript, React, Next.js, HTML, CSS, Tailwind, Sass, Git, GitLab, Vite and Figma",
    )
    canvas.root.remove(canvas.root.find("rect"))
    for key in ("width", "height", "viewBox", "fill"):
        canvas.root.set(key, source.attrib[key])
    for index, original in enumerate(source):
        node = deepcopy(original)
        canvas.root.append(node)
        if node.tag.rsplit("}", 1)[-1] == "g":
            # Preserve the icon's layout transform on the outer group.
            canvas.entrance(list(node), delay=index * 0.035, lift=0, parent=node)
    return canvas


def main() -> None:
    artwork = {
        "hero.svg": hero(),
        "hero-mobile.svg": mobile_hero(),
        "typing.svg": typing_banner(),
        "typing-mobile.svg": typing_banner(480),
        "contact.svg": footer(),
        "skills.svg": skill_icons(),
        "skills-mobile.svg": skill_icons(mobile=True),
    }
    for position, project in enumerate(PROJECTS, start=1):
        artwork[project.filename] = project_card(project, position)
    for filename, canvas in artwork.items():
        canvas.save(ASSETS / filename)
    print(f"Built {len(artwork)} profile SVGs")


if __name__ == "__main__":
    main()
