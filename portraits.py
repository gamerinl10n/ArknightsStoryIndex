"""Character identities and immutable, self-hosted portrait URLs."""

import json
from pathlib import Path
import re
from catalog import character_id


class Portraits:
    def __init__(self, root):
        self.root = Path(root)
        index = self.root / "index.json"
        images = (
            json.loads(index.read_text(encoding="utf-8")).get("images", {})
            if index.exists()
            else {}
        )
        pattern = re.compile(r"char_[a-zA-Z0-9_]+-[a-f0-9]{16}-\d+-v\d+\.webp")
        self.images = {
            cid: name
            for cid, name in images.items()
            if pattern.fullmatch(name) and (self.root / name).is_file()
        }

    def identity(self, name):
        cid = character_id(name)
        filename = self.images.get(cid)
        return {
            "character_id": cid,
            "portrait": "/portraits/" + filename if filename else None,
        }

    def annotate(self, rows):
        for row in rows:
            row.update(self.identity(row.get("speaker", row.get("value", ""))))
        return rows
