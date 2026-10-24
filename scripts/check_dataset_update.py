"""Compare immutable snapshots before proposing an upstream update; no dialogue output."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

LANGUAGES = ("ko_KR", "zh_CN", "ja_JP", "en_US")


def inventory(path):
    with closing(
        sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    ) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("Invalid snapshot")
        return {
            language: {
                path: (revision, count)
                for path, revision, count in db.execute(
                    "SELECT s.path,s.revision,count(l.story) FROM stories s "
                    "LEFT JOIN lines l ON l.story=s.id WHERE s.lang=? GROUP BY s.id",
                    (language,),
                )
            }
            for language in LANGUAGES
        }


def compare(previous, candidate, revision):
    report = {"revision": revision, "languages": {}, "issues": []}
    for language in LANGUAGES:
        before, after = previous[language], candidate[language]
        old_count = sum(row[1] for row in before.values())
        new_count = sum(row[1] for row in after.values())
        removed = sorted(before.keys() - after.keys())
        empty = sorted(
            path
            for path in before.keys() & after.keys()
            if before[path][1] and not after[path][1]
        )
        report["languages"][language] = {
            "previous_lines": old_count,
            "candidate_lines": new_count,
            "added_files": len(after.keys() - before.keys()),
            "removed_files": removed,
            "newly_empty_files": empty,
        }
        if not old_count or not new_count:
            report["issues"].append(language + ": missing language")
        if old_count and new_count < old_count * 0.8:
            report["issues"].append(
                language + ": line count decreased by more than 20%"
            )
        if removed or empty:
            report["issues"].append(
                language + ": removed or newly empty files require investigation"
            )
        if any(row[0] != revision for row in after.values()):
            report["issues"].append(language + ": unexpected source revision")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(inventory(args.previous), inventory(args.candidate), args.revision)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if report["issues"]:
        raise SystemExit(1)
