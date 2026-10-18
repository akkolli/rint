"""Render Rint's code-native monogram for the native apps and browser."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
LIME = "#d4f36b"
INK = "#192c25"
# Bezier outline of the italic lowercase r in the existing Rint wordmark.
outline = [(238, 744), (335, 338), (474, 338), (458, 405)]


def curve(start, a, b, end):
    for i in range(1, 65):
        t = i / 64
        outline.append(
            tuple(
                (1 - t) ** 3 * start[j]
                + 3 * (1 - t) ** 2 * t * a[j]
                + 3 * (1 - t) * t * t * b[j]
                + t**3 * end[j]
                for j in range(2)
            )
        )


curve(outline[-1], (502, 354), (552, 323), (617, 323))
outline.extend([(692, 323), (655, 468), (597, 468)])
curve(outline[-1], (515, 468), (458, 509), (433, 602))
outline.extend([(399, 744)])
canvas = Image.new("RGB", (2048, 2048), LIME)
draw = ImageDraw.Draw(canvas)
draw.polygon([(x * 2, y * 2) for x, y in outline], fill=INK)
draw.ellipse((591 * 2, 650 * 2, 689 * 2, 748 * 2), fill=INK)
icon = canvas.resize((1024, 1024), Image.Resampling.LANCZOS)
for target in ("iOS", "Watch"):
    icon.save(
        ROOT / f"apple/{target}/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
    )
for size in (16, 32):
    icon.resize((size, size), Image.Resampling.LANCZOS).save(
        ROOT / f"fittrackee_client/public/img/icons/favicon-{size}x{size}.png"
    )
icon.save(
    ROOT / "fittrackee_client/public/favicon.ico",
    sizes=[(16, 16), (32, 32), (48, 48)],
)
