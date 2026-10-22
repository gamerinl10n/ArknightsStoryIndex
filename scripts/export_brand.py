"""Export requested sizes from approved transparent masters; no regeneration."""

import base64
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 24, 32, 48, 64, 96, 128, 180, 192, 256, 512, 1024)


def main():
    output = ROOT / "web/brand"
    output.mkdir(exist_ok=True)
    for name in ("tower", "operator"):
        with Image.open(ROOT / f"brand/masters/{name}.png") as original:
            original = original.convert("RGBA")
            for size in SIZES:
                original.resize((size, size), Image.Resampling.LANCZOS).save(
                    output / f"{name}-{size}.png", optimize=True
                )
            # Multi-resolution Windows/browser icon, with genuine alpha.
            if name == "tower":
                original.save(
                    output / "favicon.ico",
                    sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
                )

    encoded = base64.b64encode((output / "tower-64.png").read_bytes()).decode()
    # A self-contained SVG wrapper lets browser favicons follow the browser theme.
    (output / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<style>@media(prefers-color-scheme:dark){image{filter:brightness(0) invert(1)}}</style>"
        f'<image width="64" height="64" href="data:image/png;base64,{encoded}"/></svg>'
    )


if __name__ == "__main__":
    main()
