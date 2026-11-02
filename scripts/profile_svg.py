"""Small, dependency-free SVG primitives shared by the profile artwork."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET

WIDTH = 1200
INK = "#111125"
PANEL = "#1b1a34"
BORDER = "#393153"
WHITE = "#f6f2ff"
MUTED = "#b8b3d5"
PINK = "#ff85bd"
CYAN = "#7de0fa"
ORANGE = "#ffb86b"
FONT = "DejaVu Sans,Arial,sans-serif"
MONO = "DejaVu Sans Mono,monospace"


class Svg:
    """Build accessible SVGs with escaped text and no external resources."""

    def __init__(self, width: int, height: int, title: str, description: str = ""):
        self.root = ET.Element(
            "svg",
            {
                "xmlns": "http://www.w3.org/2000/svg",
                "width": str(width),
                "height": str(height),
                "viewBox": f"0 0 {width} {height}",
                "role": "img",
                "aria-labelledby": "title description",
            },
        )
        ET.SubElement(self.root, "title", {"id": "title"}).text = title
        ET.SubElement(self.root, "desc", {"id": "description"}).text = (
            description or title
        )
        self.rect(1, 1, width - 2, height - 2, INK, radius=20, stroke=BORDER)

    def element(self, tag: str, **attributes: object) -> ET.Element:
        return ET.SubElement(
            self.root,
            tag,
            {
                name.rstrip("_").replace("_", "-"): str(value)
                for name, value in attributes.items()
            },
        )

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        fill: str = PANEL,
        radius: int = 10,
        **attributes: object,
    ) -> ET.Element:
        return self.element(
            "rect",
            x=x,
            y=y,
            width=width,
            height=height,
            rx=radius,
            fill=fill,
            **attributes,
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        size: int = 16,
        fill: str = WHITE,
        weight: int = 400,
        mono: bool = False,
        **attributes: object,
    ) -> ET.Element:
        node = self.element(
            "text",
            x=x,
            y=y,
            font_size=size,
            fill=fill,
            font_weight=weight,
            font_family=MONO if mono else FONT,
            **attributes,
        )
        node.text = value
        return node

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = BORDER,
        **attributes: object,
    ) -> None:
        self.element("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke, **attributes)

    def circle(
        self, x: float, y: float, radius: float, fill: str, **attributes: object
    ) -> None:
        self.element("circle", cx=x, cy=y, r=radius, fill=fill, **attributes)

    def path(
        self, data: str, stroke: str, width: float = 2, **attributes: object
    ) -> None:
        self.element(
            "path", d=data, fill="none", stroke=stroke, stroke_width=width, **attributes
        )

    def label(self, x: float, y: float, value: str, fill: str = PINK) -> None:
        self.text(x, y, value, 12, fill, mono=True, letter_spacing=2)

    def gradient(self, name: str, stops: tuple[str, ...]) -> str:
        """Define a local gradient and return its paint reference."""
        if len(stops) < 2:
            raise ValueError("A gradient needs at least two colour stops")
        definitions = self.root.find("defs")
        if definitions is None:
            definitions = ET.SubElement(self.root, "defs")
        gradient = ET.SubElement(
            definitions,
            "linearGradient",
            {
                "id": name,
                "x1": "0%",
                "y1": "0%",
                "x2": "100%",
                "y2": "100%",
            },
        )
        for index, color in enumerate(stops):
            ET.SubElement(
                gradient,
                "stop",
                {
                    "offset": f"{index * 100 / (len(stops) - 1):g}%",
                    "stop-color": color,
                },
            )
        return f"url(#{name})"

    def save(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(self.root, space="  ")
        content = ET.tostring(self.root, encoding="unicode") + "\n"
        # Unique temporary names also make concurrent local builds safe.
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.stem}-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        try:
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
