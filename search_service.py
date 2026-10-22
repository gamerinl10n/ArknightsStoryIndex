"""Database lifecycle and public-data caches, scoped to one app/snapshot."""

from contextlib import closing
from functools import lru_cache
import json
import sqlite3
from catalog import characters
from core import connect
from runtime_snapshot import materialize


class SearchService:
    def __init__(self, database, readonly):
        self.database = database
        self.readonly = readonly
        # Cache public suggestions only. Search terms and results are never cached here.
        self._cached_suggestions = lru_cache(maxsize=8)(self._suggestions)

    def open_db(self):
        if not self.readonly:
            return connect(self.database)
        path = materialize(self.database)
        db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
        db.row_factory = sqlite3.Row
        return db

    def suggestions(self, lang, spoilers):
        return (
            self._cached_suggestions(lang, spoilers)
            if self.readonly
            else self._suggestions(lang, spoilers)
        )

    def _suggestions(self, lang, spoilers):
        with closing(self.open_db()) as db:
            indexed = db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='suggestion_counts'"
            ).fetchone()
            if indexed:
                counts = dict(
                    db.execute(
                        "SELECT speaker,count FROM suggestion_counts WHERE lang=? AND spoilers=?",
                        (lang, int(spoilers)),
                    )
                )
            else:
                # Compatibility with older snapshots and mutable local archives.
                counts = dict(
                    db.execute(
                        "SELECT l.speaker,count(*) FROM lines l JOIN stories s ON s.id=l.story WHERE s.lang=? AND l.speaker!='' AND (? OR EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)) GROUP BY l.speaker",
                        (lang, spoilers),
                    )
                )
        result = {
            name: {"value": name, "label": name, "count": count}
            for name, count in counts.items()
        }
        for character in characters():
            names = character["names"].get(lang, [])
            count = sum(counts.get(name, 0) for name in names)
            if not count:
                continue
            alternate = character.get("aliases", []) + [
                name for group in character["names"].values() for name in group
            ]
            for alias in alternate:
                if alias not in result:
                    result[alias] = {
                        "value": alias,
                        "label": " / ".join(names),
                        "count": count,
                    }
        return sorted(result.values(), key=lambda row: row["value"])

    def status(self):
        with closing(self.open_db()) as db:
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='import_status'"
            ).fetchone()
            row = (
                db.execute("SELECT payload FROM import_status WHERE id=1").fetchone()
                if exists
                else None
            )
        result = json.loads(row[0]) if row else {"dialogue_lines": 0}
        return {**result, "readonly": self.readonly}
