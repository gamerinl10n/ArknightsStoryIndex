"""Build an immutable search-only snapshot. Raw archives never enter the Function."""

import argparse
import gzip
import shutil
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from build_portraits import build_portraits


def build_suggestion_counts(db):
    """Aggregate only public character counts; no queries or user data."""
    db.executescript(
        """
    CREATE TABLE suggestion_counts(lang TEXT,spoilers INTEGER,speaker TEXT,count INTEGER,PRIMARY KEY(lang,spoilers,speaker)) WITHOUT ROWID;
    INSERT INTO suggestion_counts
    SELECT s.lang,1,l.speaker,count(*) FROM lines l JOIN stories s ON s.id=l.story
    WHERE l.speaker!='' GROUP BY s.lang,l.speaker;
    INSERT INTO suggestion_counts
    SELECT s.lang,0,l.speaker,count(*) FROM lines l JOIN stories s ON s.id=l.story
    WHERE l.speaker!='' AND EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)
    GROUP BY s.lang,l.speaker;
    ANALYZE;
    """
    )


def export_snapshot(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError("Source and output must differ")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".sqlite.tmp")
    temporary.unlink(missing_ok=True)
    try:
        with (
            closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src,
            closing(sqlite3.connect(temporary)) as dst,
        ):
            # Retain exact schema/indices used by core.search, but not raw archives.
            dst.executescript(
                """
            CREATE TABLE stories(id TEXT PRIMARY KEY,lang TEXT,path TEXT,revision TEXT,source TEXT);
            CREATE TABLE lines(id TEXT GENERATED ALWAYS AS (story || ':' || ordinal) VIRTUAL,story TEXT,ordinal INTEGER,speaker TEXT,text TEXT,branch TEXT,hash TEXT);
            CREATE TABLE import_status(id INTEGER PRIMARY KEY,payload TEXT);
            """
            )
            dst.executemany(
                "INSERT INTO stories VALUES(?,?,?,?,?)",
                src.execute("SELECT id,lang,path,revision,source FROM stories"),
            )
            dst.executemany(
                "INSERT INTO lines(story,ordinal,speaker,text,branch,hash) VALUES(?,?,?,?,?,?)",
                src.execute("SELECT story,ordinal,speaker,text,branch,hash FROM lines"),
            )
            dst.executemany(
                "INSERT INTO import_status VALUES(?,?)",
                src.execute("SELECT * FROM import_status"),
            )
            dst.executescript(
                """
            CREATE INDEX story_path_idx ON stories(path,lang);
            CREATE INDEX speaker_idx ON lines(speaker);
            CREATE INDEX story_idx ON lines(story,ordinal);
            """
            )
            build_suggestion_counts(dst)
            dst.commit()
            count = dst.execute("SELECT count(*) FROM lines").fetchone()[0]
            if not count or dst.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Invalid search snapshot")
        size = temporary.stat().st_size
        if size > 450 * 1024 * 1024:
            raise ValueError(
                "Search snapshot exceeds 450 MiB budget; split the corpus before deployment"
            )
        temporary.replace(output)
        print(f"Search snapshot: {count:,} lines, {size/1024**2:.1f} MiB")
    finally:
        temporary.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source-db", help="Reuse an already imported DB for local verification"
    )
    p.add_argument("--output", default="generated/search.sqlite")
    a = p.parse_args()
    source = a.source_db
    if not source:
        source = "data/build.sqlite"
        subprocess.run(
            [
                sys.executable,
                "sync.py",
                "--database",
                source,
                "--ephemeral",
                "--ref",
                os.environ.get("ASI_SOURCE_REF", "master"),
            ],
            check=True,
        )
    build_portraits()
    export_snapshot(source, a.output)
    compressed = Path(a.output).with_suffix(".sqlite.gz")
    with (
        open(a.output, "rb") as src,
        gzip.open(compressed, "wb", compresslevel=6) as dst,
    ):
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    print(f"Bundled snapshot: {compressed.stat().st_size/1024**2:.1f} MiB gzip")


if __name__ == "__main__":
    main()
