"""Immutable, process-local character catalog shared by search and suggestions."""

from functools import lru_cache
import json
from pathlib import Path


@lru_cache(maxsize=1)
def characters():
    return json.loads(
        (Path(__file__).parent / "characters.json").read_text(encoding="utf-8")
    )


@lru_cache(maxsize=1)
def alias_index():
    index = {}
    for character in characters():
        names = [
            character["id"],
            *character.get("aliases", []),
            *(name for group in character["names"].values() for name in group),
        ]
        for lang, localized in character["names"].items():
            for name in names:
                index.setdefault((lang, name.casefold()), []).extend(localized)
    return {key: tuple(dict.fromkeys(values)) for key, values in index.items()}


def aliases(value, lang):
    # Return a fresh list: callers cannot mutate the shared catalog index.
    return list(alias_index().get((lang, value.casefold()), (value,)))


@lru_cache(maxsize=1)
def identity_index():
    index = {}
    for character in characters():
        # Include exact multilingual names and explicit aliases, never fuzzy similarity.
        for value in [
            character["id"],
            *character.get("aliases", []),
            *(name for group in character["names"].values() for name in group),
        ]:
            index.setdefault(value.casefold(), set()).add(character["id"])
    return {key: next(iter(ids)) for key, ids in index.items() if len(ids) == 1}


def character_id(value):
    return identity_index().get(value.casefold())
