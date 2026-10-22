"""Pin, verify and resize default avatars at build time; never fetch at request time."""

from concurrent.futures import ThreadPoolExecutor
import time
import tempfile
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def build_portraits(output=None, manifest=None, fetch=None):
    output = Path(output or ROOT / "generated/portraits")
    manifest = manifest or json.loads((ROOT / "portraits.source.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    size = manifest["size"]

    def download(url):
        with urlopen(
            Request(url, headers={"User-Agent": "Arknights-Index-build"}), timeout=30
        ) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("Portrait exceeds input budget")
        return data

    fetch = fetch or download

    def convert(pair):
        cid, sha = pair
        if not re.fullmatch(r"char_[a-zA-Z0-9_]+", cid) or not re.fullmatch(
            r"[0-9a-f]{40}", sha
        ):
            raise ValueError("Invalid portrait manifest")
        filename = f"{cid}-{sha[:16]}-{size}-v{manifest['version']}.webp"
        path = output / filename
        if path.exists():
            try:
                with Image.open(path) as image:
                    if image.format == "WEBP" and image.size == (size, size):
                        image.verify()
                        return cid, filename
            except (OSError, ValueError):
                pass
        url = f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['revision']}/{manifest['directory']}/{cid}.png"
        for attempt in range(3):
            try:
                data = fetch(url)
                break
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
        if git_blob_sha(data) != sha:
            raise ValueError(f"Portrait source hash mismatch: {cid}")
        with tempfile.NamedTemporaryFile(
            dir=output, suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
        try:
            with Image.open(BytesIO(data)) as original:
                image = ImageOps.fit(
                    original.convert("RGBA"),
                    (size, size),
                    method=Image.Resampling.LANCZOS,
                )
                image.save(
                    temporary, format="WEBP", quality=manifest["quality"], method=6
                )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return cid, filename

    images = {}
    pairs = list(manifest["files"].items())
    with ThreadPoolExecutor(max_workers=6) as executor:
        for start in range(0, len(pairs), 6):
            images.update(executor.map(convert, pairs[start : start + 6]))
            if start % 60 == 0:
                print(f"Portraits: verified {len(images)}/{len(pairs)}", flush=True)
    index = {
        "source": manifest["repository"],
        "revision": manifest["revision"],
        "images": images,
    }
    temporary = output / "index.tmp"
    temporary.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(output / "index.json")
    keep = set(images.values())
    for path in output.glob("*.webp"):
        if path.name not in keep:
            path.unlink()
    print(
        f"Portraits: {len(images)} avatars, {sum((output/name).stat().st_size for name in images.values())/1024**2:.2f} MiB"
    )
    return index


if __name__ == "__main__":
    build_portraits()
