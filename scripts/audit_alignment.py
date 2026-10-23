"""Read-only structural feasibility audit; never writes or prints game dialogue.

This is not a production aligner and its eligibility rate is not translation accuracy.
Input: a snapshot checkout, or language directories of selected story samples.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import TEXT_TAGS, command_parts, parse
from catalog import character_id

LOCALIZED = {"name", "options", "content", "text"}


def structure(raw):
    commands = []
    attributes = Counter()
    for line in raw.splitlines():
        command = command_parts(line)
        if not command:
            continue
        tag, _, pairs, _ = command
        if tag in TEXT_TAGS:
            attributes.update(pairs.keys())
        commands.append(
            (
                tag,
                tuple(
                    sorted(
                        (k, v)
                        for k, v in pairs.items()
                        if not (tag in TEXT_TAGS and k in LOCALIZED)
                    )
                ),
            )
        )
    return commands, attributes


def audit(root, paths, revision):
    def file(lang, path):
        full = root / lang / "gamedata/story" / path
        return full if full.exists() else root / lang / path

    rows = []
    for path in paths:
        source = file("cn", path)
        if not source.exists():
            raise ValueError(f"Missing Chinese sample: {path}")
        raw = source.read_text(encoding="utf-8-sig")
        tape, attributes = structure(raw)
        lines = list(parse(raw))
        row = {
            "path": path,
            "source_text_rows": len(lines),
            "source_commands": len(tape),
            "text_attribute_keys": sorted(attributes),
            "sha256": {"cn": hashlib.sha256(source.read_bytes()).hexdigest()},
            "targets": {},
        }
        for lang in ("kr", "jp", "en"):
            target = file(lang, path)
            if not target.exists():
                row["targets"][lang] = {"available": False}
                continue
            translated = target.read_text(encoding="utf-8-sig")
            target_tape, _ = structure(translated)
            target_lines = list(parse(translated))
            same_tape = tape == target_tape
            comparable = len(lines) == len(target_lines)
            known = mismatches = 0
            if same_tape and comparable:
                for a, b in zip(lines, target_lines, strict=True):
                    left, right = character_id(a[1]), character_id(b[1])
                    if left and right:
                        known += 1
                        mismatches += left != right
            row["sha256"][lang] = hashlib.sha256(target.read_bytes()).hexdigest()
            row["targets"][lang] = {
                "available": True,
                "text_rows": len(target_lines),
                "exact_command_structure": same_tape,
                "same_text_row_count": comparable,
                "same_physical_ordinal_pairs": sum(
                    a[0] == b[0] for a, b in zip(lines, target_lines)
                ),
                "known_speaker_pairs": known,
                "known_speaker_mismatches": mismatches,
                "strict_structure_eligible": same_tape
                and comparable
                and not mismatches,
            }
        rows.append(row)
    return {
        "source_revision": revision,
        "sample_files": len(rows),
        "source_text_rows": sum(row["source_text_rows"] for row in rows),
        "scope": "selected samples only; structural eligibility is not semantic accuracy",
        "summary": {
            lang: {
                "available_files": sum(
                    row["targets"][lang]["available"] for row in rows
                ),
                "eligible_files": sum(
                    row["targets"][lang].get("strict_structure_eligible", False)
                    for row in rows
                ),
                "known_speaker_pairs": sum(
                    row["targets"][lang].get("known_speaker_pairs", 0) for row in rows
                ),
                "known_speaker_mismatches": sum(
                    row["targets"][lang].get("known_speaker_mismatches", 0)
                    for row in rows
                ),
            }
            for lang in ("kr", "jp", "en")
        },
        "files": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--paths", type=Path, help="JSON array of relative story paths")
    args = parser.parse_args()
    if args.paths:
        paths = json.loads(args.paths.read_text())
    else:
        base = args.root / "cn/gamedata/story"
        if not base.exists():
            base = args.root / "cn"
        paths = sorted(p.relative_to(base).as_posix() for p in base.rglob("*.txt"))
    print(
        json.dumps(audit(args.root, paths, args.revision), ensure_ascii=False, indent=2)
    )
