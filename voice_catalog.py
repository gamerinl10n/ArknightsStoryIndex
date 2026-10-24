"""Build-time voice text catalog and bounded, ID-based search. No audio or runtime fetches."""

from functools import lru_cache
import gzip
import json
from pathlib import Path
from urllib.request import urlopen
from catalog import character_id, characters

ROOT = Path(__file__).resolve().parent
LANGUAGES = {"cn": "zh_CN", "kr": "ko_KR", "jp": "ja_JP", "en": "en_US"}


def build_voice_catalog(root=ROOT):
    revision = json.loads((root / "dataset-source.json").read_text())["revision"]
    rows = {}
    for folder, lang in LANGUAGES.items():
        url = f"https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/{revision}/{folder}/gamedata/excel/charword_table.json"
        with urlopen(url, timeout=60) as response:
            source = json.load(response)["charWords"]
        if not source:
            raise ValueError("Empty voice catalog: " + lang)
        for key, record in source.items():
            identity = [record["charId"], record["wordKey"], record["voiceId"]]
            group = rows.setdefault(key, {"identity": identity, "variants": {}})
            if group["identity"] != identity:
                raise ValueError("Voice key identity mismatch: " + key)
            group["variants"][lang] = {
                field: record.get(field)
                for field in (
                    "voiceTitle",
                    "voiceText",
                    "voiceIndex",
                    "unlockType",
                    "unlockParam",
                    "lockDescription",
                )
            }
    output = root / "generated/voices.json.gz"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    try:
        with gzip.open(temporary, "wt", encoding="utf8") as stream:
            json.dump(
                {"revision": revision, "rows": rows},
                stream,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(
        f"Voice text catalog: {len(rows):,} keys; {output.stat().st_size / 1024**2:.1f} MiB gzip"
    )


@lru_cache(maxsize=1)
def load_voice_catalog():
    with gzip.open(ROOT / "generated/voices.json.gz", "rt", encoding="utf8") as stream:
        data = json.load(stream)
    if (
        data["revision"]
        != json.loads((ROOT / "dataset-source.json").read_text())["revision"]
    ):
        raise ValueError("Voice catalog revision mismatch")
    return data


def search_voices(data, character, query, lang, offset=0, limit=50):
    identity = (
        (
            character
            if any(row["identity"][0] == character for row in data["rows"].values())
            else character_id(character)
        )
        if character
        else None
    )
    if character and identity is None:
        return [], 0
    matches = []
    needle = query.casefold()
    for key, row in data["rows"].items():
        if identity and row["identity"][0] != identity:
            continue
        if query and not any(
            needle in (v["voiceText"] or "").casefold()
            or needle in (v["voiceTitle"] or "").casefold()
            for v in row["variants"].values()
        ):
            continue
        primary = (
            row["variants"].get(lang)
            or row["variants"].get("zh_CN")
            or next(iter(row["variants"].values()))
        )
        matches.append((key, row, primary))
    matches.sort(key=lambda x: (x[1]["identity"][0], x[2].get("voiceIndex") or 0, x[0]))
    return matches[offset : offset + limit], len(matches)


def voice_characters(data, lang):
    available = {row["identity"][0] for row in data["rows"].values()}
    result = []
    for char in characters():
        if char["id"] in available:
            names = (
                char["names"].get(lang) or char["names"].get("zh_CN") or [char["id"]]
            )
            result.append((char["id"], names[0]))
            available.remove(char["id"])
    result.extend((key, key) for key in available)
    return sorted(result, key=lambda row: row[1].casefold())


if __name__ == "__main__":
    build_voice_catalog()


def voice_completions(data, lang):
    """Native completion values use only registered names/aliases and stable IDs."""
    labels = dict(voice_characters(data, lang))
    values = {key: label for key, label in labels.items()}
    for character in characters():
        if character["id"] not in labels:
            continue
        for value in [
            *character.get("aliases", []),
            *(name for names in character["names"].values() for name in names),
        ]:
            # Ambiguous names must not silently select a different character.
            if character_id(value) == character["id"]:
                values[value] = labels[character["id"]]
    return sorted(
        values.items(), key=lambda row: (row[1].casefold(), row[0].casefold())
    )


def voice_highlights(text, query):
    """Casefold matches mapped back to original Unicode characters; never emit HTML."""
    text = text or ""
    needle = query.casefold()
    if not needle:
        return [(text, False)]
    folded, positions = "", []
    for index, character in enumerate(text):
        part = character.casefold()
        folded += part
        positions.extend([index] * len(part))
    matched = set()
    start = folded.find(needle)
    while start != -1:
        matched.update(positions[start : start + len(needle)])
        start = folded.find(needle, start + 1)
    parts = []
    for index, character in enumerate(text):
        active = index in matched
        if parts and parts[-1][1] == active:
            parts[-1] = (parts[-1][0] + character, active)
        else:
            parts.append((character, active))
    return parts
