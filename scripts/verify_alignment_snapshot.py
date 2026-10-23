"""Audit stored correspondences against a read-only archive; never output dialogue."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import character_id
from core import parse
from translation_alignment import METHOD, TARGET_LANGS, verified_pairs


def verify(archive, snapshot):
    archive.row_factory = snapshot.row_factory = sqlite3.Row
    records = {
        (row["path"], row["lang"]): dict(row)
        for row in snapshot.execute("SELECT * FROM translation_alignments")
    }
    seen, issues = set(), []
    counts = {lang: Counter() for lang in TARGET_LANGS}
    samples = {lang: {} for lang in TARGET_LANGS}
    revisions = set()
    for source in archive.execute(
        "SELECT id,path,revision,source,raw FROM stories WHERE lang='zh_CN' ORDER BY path"
    ):
        revisions.add(source["revision"])
        source_rows = None
        source_hash = hashlib.sha256(source["raw"].encode()).hexdigest()
        for lang in TARGET_LANGS:
            stat = counts[lang]
            stat["source_files"] += 1
            target = archive.execute(
                "SELECT id,revision,source,raw FROM stories WHERE path=? AND lang=?",
                (source["path"], lang),
            ).fetchone()
            pairs, status = (
                (None, "unavailable")
                if target is None
                else verified_pairs(source["raw"], target["raw"])
            )
            if target and target["revision"] != source["revision"]:
                pairs, status = None, "revision"
            stat[status + "_files"] += 1
            examples = samples[lang].setdefault(status, [])
            if len(examples) < 3:
                examples.append(source["path"])
            key = (source["path"], lang)
            record = records.get(key)
            if pairs is None:
                if record:
                    issues.append(
                        {"path": key[0], "lang": lang, "reason": "ineligible_map"}
                    )
                continue
            seen.add(key)
            if record is None:
                issues.append({"path": key[0], "lang": lang, "reason": "missing_map"})
                continue
            reasons = []
            if record["method"] != METHOD:
                reasons.append("method")
            if (
                record["cn_story"],
                record["target_story"],
                record["cn_revision"],
                record["target_revision"],
            ) != (source["id"], target["id"], source["revision"], target["revision"]):
                reasons.append("provenance")
            if (
                record["cn_hash"] != source_hash
                or record["target_hash"]
                != hashlib.sha256(target["raw"].encode()).hexdigest()
            ):
                reasons.append("hash")
            try:
                stored = list(
                    struct.iter_unpack("<II", zlib.decompress(record["ordinal_map"]))
                )
            except (ValueError, zlib.error, struct.error):
                stored = []
            if stored != pairs:
                reasons.append("ordinal_map")
            if source_rows is None:
                source_rows = list(parse(source["raw"]))
            target_rows = list(parse(target["raw"]))
            for story_id, expected, expected_lang, expected_source in [
                (source["id"], source_rows, "zh_CN", source["source"]),
                (target["id"], target_rows, lang, target["source"]),
            ]:
                actual = [
                    tuple(row)
                    for row in snapshot.execute(
                        "SELECT ordinal,speaker,text,branch FROM lines WHERE story=? ORDER BY ordinal",
                        (story_id,),
                    )
                ]
                meta = snapshot.execute(
                    "SELECT revision,path,lang,source FROM stories WHERE id=?",
                    (story_id,),
                ).fetchone()
                if (
                    actual != expected
                    or not meta
                    or meta["path"] != source["path"]
                    or meta["revision"] != source["revision"]
                    or meta["lang"] != expected_lang
                    or meta["source"] != expected_source
                ):
                    reasons.append("snapshot_text_or_metadata")
            left, right = {r[0]: r for r in source_rows}, {r[0]: r for r in target_rows}
            for a, b in pairs:
                ids = (character_id(left[a][1]), character_id(right[b][1]))
                category = (
                    "both_known"
                    if all(ids)
                    else "one_known" if any(ids) else "neither_known"
                )
                stat["speaker_" + category + "_rows"] += 1
            stat["matched_rows"] += len(pairs)
            stat["excluded_choice_rows"] += len(source_rows) - len(pairs)
            if reasons:
                issues.append(
                    {"path": key[0], "lang": lang, "reason": sorted(set(reasons))}
                )
    for path, lang in records.keys() - seen:
        if not any(issue["path"] == path and issue["lang"] == lang for issue in issues):
            issues.append({"path": path, "lang": lang, "reason": "unexpected_map"})
    return {
        "source_revisions": sorted(revisions),
        "method": METHOD,
        "scope": "full imported archive and snapshot; structural integrity is not semantic accuracy",
        "stored_file_pairs": len(records),
        "issues": issues,
        "languages": {lang: dict(stat) for lang, stat in counts.items()},
        "samples": samples,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with (
        sqlite3.connect(
            args.archive.resolve().as_uri() + "?mode=ro", uri=True
        ) as archive,
        sqlite3.connect(
            args.snapshot.resolve().as_uri() + "?mode=ro", uri=True
        ) as snapshot,
    ):
        report = verify(archive, snapshot)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf8")
    else:
        print(text)
    if report["issues"]:
        raise SystemExit(1)
