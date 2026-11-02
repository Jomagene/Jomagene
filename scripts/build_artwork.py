#!/usr/bin/env python3
"""Rebuild the original vector artwork. No downloads, fonts or packages needed."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from profile_svg import CYAN, INK, MUTED, ORANGE, PINK, WHITE, WIDTH, Svg

ASSETS = Path(__file__).resolve().parents[1] / "assets"


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
    canvas.element(
        "path",
        d="M 1 330 C 220 297 380 371 643 337 S 980 311 1199 327 L 1199 340 Q 1199 359 1180 359 H 20 Q 1 359 1 340 Z",
        fill=glow,
        opacity="0.3",
    )
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
    canvas.text(28, 238, "HNG12 finalist · top 432 / 11,285", 13, CYAN, mono=True)
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
    canvas.circle(1136, 70, 28, "#ad83eb")
    canvas.text(1122, 81, "↗", 32, WHITE, 700)
    return canvas


def main() -> None:
    artwork = {
        "hero.svg": hero(),
        "hero-mobile.svg": mobile_hero(),
        "contact.svg": footer(),
    }
    for position, project in enumerate(PROJECTS, start=1):
        artwork[project.filename] = project_card(project, position)
    for filename, canvas in artwork.items():
        canvas.save(ASSETS / filename)
    print(f"Built {len(artwork)} original SVG illustrations")


if __name__ == "__main__":
    main()
