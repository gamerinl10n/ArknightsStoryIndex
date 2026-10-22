"""Raw script ingestion and conservative, evidence-first retrieval. Python 3.11+."""

import hashlib
import json
import re
import sqlite3
from pathlib import Path


from catalog import aliases
from search_queries import search, context_window, LANGUAGES


def connect(path, ephemeral=False):
    db = sqlite3.connect(path)
    if ephemeral:
        db.execute("PRAGMA journal_mode=MEMORY")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
    CREATE TABLE IF NOT EXISTS stories(id TEXT PRIMARY KEY, lang TEXT, path TEXT, revision TEXT, source TEXT, raw TEXT);
    CREATE TABLE IF NOT EXISTS snapshots(story TEXT, revision TEXT, raw TEXT, PRIMARY KEY(story,revision));
    CREATE TABLE IF NOT EXISTS lines(id TEXT PRIMARY KEY, story TEXT, ordinal INTEGER, speaker TEXT, text TEXT, branch TEXT, hash TEXT);
    CREATE INDEX IF NOT EXISTS story_path_idx ON stories(path,lang);
    CREATE INDEX IF NOT EXISTS speaker_idx ON lines(speaker);
    CREATE INDEX IF NOT EXISTS story_idx ON lines(story,ordinal);
    """
    )
    return db


def parse(raw):
    branch = "main"
    for n, line in enumerate(raw.splitlines()):
        command = re.match(r"^\[(\w+)(.*?)\](.*)$", line.strip())
        if not command:
            continue
        prop, attrs, text = command.groups()
        prop = prop.lower()
        if prop == "name" and attrs.lstrip().startswith("="):
            attrs = "name" + attrs
        pairs = dict(
            (m[0], m[1] if m[1] else m[2])
            for m in re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|([^,\s]+))', attrs)
        )
        if prop in ("predicate", "decision", "label", "gotolabel"):
            branch = f"{prop}:{attrs.strip()}"
        if prop not in ("name", "multiline"):
            continue
        speaker = pairs.get("name", "")
        text = text or pairs.get("content", "")
        if text.strip():
            yield n, speaker, re.sub(r"<[^>]+>", "", text).replace("\\n", "\n"), branch


def ingest(db, root, revision, source):
    """Validate entire batch before transactional replacement; raw snapshots stay in SQLite."""
    root = Path(root)
    batch = []
    report = {"files": 0, "dialogue_lines": 0, "unparsed_text_lines": 0}

    for lang, folder in LANGUAGES.items():
        for f in sorted((root / folder / "gamedata/story").rglob("*.txt")):
            raw = f.read_text(encoding="utf-8-sig")
            rows = list(parse(raw))
            report["files"] += 1
            report["dialogue_lines"] += len(rows)
            report["unparsed_text_lines"] += sum(
                bool(x.strip()) and not x.lstrip().startswith(("[", "//"))
                for x in raw.splitlines()
            )
            path = f.relative_to(root / folder / "gamedata/story").as_posix()
            batch.append((lang, path, raw, rows))
    if not batch or not any(x[0] == "ko_KR" and x[3] for x in batch):
        raise ValueError("한국어 대사가 없는 입력입니다. 기존 데이터를 유지합니다.")
    old_count = db.execute("SELECT count(*) FROM lines").fetchone()[0]
    if old_count >= 100 and report["dialogue_lines"] < old_count * 0.8:
        raise ValueError("대사 수가 20% 이상 감소했습니다. 기존 데이터를 유지합니다.")
    with db:
        for lang, path, raw, rows in batch:
            sid = f"{lang}:{path}"
            db.execute(
                "INSERT OR REPLACE INTO stories VALUES(?,?,?,?,?,?)",
                (sid, lang, path, revision, source, raw),
            )
            db.execute(
                "INSERT OR IGNORE INTO snapshots VALUES(?,?,?)", (sid, revision, raw)
            )
            db.execute("DELETE FROM lines WHERE story=?", (sid,))
            for n, speaker, text, branch in rows:
                digest = hashlib.sha256(
                    json.dumps([speaker, text, branch], ensure_ascii=False).encode()
                ).hexdigest()
                db.execute(
                    "INSERT INTO lines VALUES(?,?,?,?,?,?,?)",
                    (f"{sid}:{n}", sid, n, speaker, text, branch, digest),
                )
        db.execute(
            "CREATE TABLE IF NOT EXISTS import_status(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT)"
        )
        db.execute(
            "INSERT OR REPLACE INTO import_status VALUES(1,?)",
            (json.dumps({**report, "revision": revision, "source": source}),),
        )
    return sum(len(x[3]) for x in batch)
