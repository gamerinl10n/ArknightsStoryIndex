"""Synthetic dialogue only; shifted rows and changed branches must stay distinct."""

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from app import create_app
from build import export_snapshot
from core import connect, ingest
from search_queries import search
from translation_alignment import attach_comparisons, verified_pairs


class TranslationAlignmentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        scripts = {
            "cn": {
                "matched.txt": '[name="凯尔希"]合成测试甲\n[name="阿米娅"]合成测试乙',
                "branch.txt": '[predicate(references="1")]\n[name="凯尔希"]合成分支',
                "missing.txt": '[name="凯尔希"]合成未公开',
                "speaker.txt": '[name="凯尔希"]合成角色',
            },
            "kr": {
                "matched.txt": '// synthetic comment shifts physical rows\n\n[name="켈시"]합성 예문 갑\n[name="아미야"]합성 예문 을',
                "branch.txt": '[predicate(references="2")]\n[name="켈시"]합성 분기',
                "speaker.txt": '[name="아미야"]합성 인물',
            },
        }
        for lang, files in scripts.items():
            base = self.root / lang / "gamedata/story"
            base.mkdir(parents=True)
            for name, raw in files.items():
                (base / name).write_text(raw, encoding="utf8")
        self.source, self.snapshot = (
            self.root / "archive.sqlite",
            self.root / "search.sqlite",
        )
        with closing(connect(self.source)) as db:
            ingest(db, self.root, "synthetic-revision", "synthetic/source")
        export_snapshot(self.source, self.snapshot)
        self.client = create_app(str(self.snapshot), readonly=True).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def query(self, **params):
        args = dict(
            q="合成", lang="zh_CN", compare="1", translation_lang="ko_KR", details="0"
        )
        args.update(params)
        return self.client.get("/api/search", query_string=args)

    def test_shifted_lines_are_mapped_by_structure_in_both_directions(self):
        rows = self.query().json["items"]
        item = next(row for row in rows if row["path"] == "matched.txt")
        other = item["comparison"]["items"][0]
        self.assertEqual(item["ordinal"], 0)
        self.assertEqual(other["ordinal"], 2)
        self.assertEqual(other["speaker"], "켈시")
        self.assertEqual(other["text"], "합성 예문 갑")
        self.assertEqual(other["lang"], "ko_KR")
        reverse = self.query(q="합성 예문 갑", lang="ko_KR").json["items"][0]
        self.assertEqual(reverse["comparison"]["items"][0]["ordinal"], 0)
        self.assertEqual(reverse["comparison"]["lang"], "zh_CN")

    def test_unverified_and_unavailable_are_separate_and_never_filled(self):
        rows = {r["path"]: r for r in self.query(spoilers="1").json["items"]}
        for path in ("branch.txt", "speaker.txt"):
            self.assertEqual(rows[path]["comparison"]["status"], "unverified")
            self.assertEqual(rows[path]["comparison"]["items"], [])
        self.assertEqual(rows["missing.txt"]["comparison"]["status"], "unavailable")
        self.assertNotIn("missing.txt", {r["path"] for r in self.query().json["items"]})

    def test_context_compares_only_on_request_and_preserves_provenance(self):
        params = dict(story="zh_CN:matched.txt", ordinal=0, radius=3)
        ordinary = self.client.get("/api/context", query_string=params).json
        self.assertNotIn("comparison", ordinary["items"][0])
        paired = self.client.get(
            "/api/context",
            query_string={**params, "compare": "1", "translation_lang": "ko_KR"},
        ).json
        row = paired["items"][0]["comparison"]["items"][0]
        self.assertEqual(row["path"], "matched.txt")
        self.assertEqual(row["revision"], "synthetic-revision")
        self.assertEqual(row["source"], "synthetic/source")
        self.assertEqual(row["ordinal"], 2)

    def test_normal_search_is_unchanged_and_comparisons_are_batched(self):
        with closing(sqlite3.connect(self.snapshot)) as db:
            db.row_factory = sqlite3.Row
            trace = []
            db.set_trace_callback(trace.append)
            result = search(db, query="合成", lang="zh_CN", include_details=False)
            self.assertFalse(any("translation_alignments" in sql for sql in trace))
            self.assertTrue(all("comparison" not in x for x in result["items"]))
            trace.clear()
            attach_comparisons(db, result["items"] * 10, "zh_CN", "ko_KR")
            self.assertEqual(len(trace), 3)

    def test_stale_revision_and_old_snapshot_cannot_claim_a_match(self):
        with closing(sqlite3.connect(self.snapshot)) as db:
            db.execute(
                "UPDATE stories SET revision='changed' WHERE id='ko_KR:matched.txt'"
            )
            db.commit()
        row = next(x for x in self.query().json["items"] if x["path"] == "matched.txt")
        self.assertEqual(row["comparison"]["status"], "unverified")
        with closing(sqlite3.connect(self.snapshot)) as db:
            db.execute("DROP TABLE translation_alignments")
            db.commit()
        self.assertEqual(
            self.query().json["items"][0]["comparison"]["status"], "unsupported"
        )

    def test_alignment_rejects_insertions_and_unknown_empty_speaker(self):
        a = '[name="Synthetic NPC"]Synthetic line'
        self.assertIsNone(verified_pairs(a, '[name=""]Synthetic translation')[0])
        self.assertIsNone(verified_pairs(a, a + '\n[name="Synthetic NPC"]Extra')[0])
        self.assertEqual(self.query(translation_lang="zh_CN").status_code, 400)
        self.assertIsNone(
            verified_pairs(
                '[sticker(name="scene_a", text="Synthetic")]',
                '[sticker(name="scene_b", text="Translation")]',
            )[0]
        )

    def test_equal_counts_cannot_hide_shifted_empty_commands(self):
        source = '[name="Synthetic NPC"]One\n[name="Synthetic NPC"]\n[name="Synthetic NPC"]Three'
        target = '[name="Synthetic NPC"]\n[name="Synthetic NPC"]Two\n[name="Synthetic NPC"]Three'
        self.assertEqual(verified_pairs(source, target), (None, "text_slots"))

    def test_ambiguous_decision_is_omitted_without_shifting_later_lines(self):
        source = '[name="Synthetic NPC"]Before\n[decision(options="One;Two",values="1;2")]\n[name="Synthetic NPC"]After'
        target = '[name="Synthetic NPC"]Before\n[decision(options="One;ambiguous;Two",values="1;2")]\n[name="Synthetic NPC"]After'
        self.assertEqual(verified_pairs(source, target), ([(0, 0), (2, 2)], "partial"))
        self.assertEqual(
            verified_pairs(source.splitlines()[1], target.splitlines()[1]),
            (None, "decision_options"),
        )

    def test_snapshot_audit_detects_map_and_text_corruption(self):
        from scripts.verify_alignment_snapshot import verify
        import struct
        import zlib

        with (
            closing(sqlite3.connect(self.source)) as archive,
            closing(sqlite3.connect(self.snapshot)) as snapshot,
        ):
            self.assertEqual(verify(archive, snapshot)["issues"], [])
            snapshot.execute(
                "UPDATE translation_alignments SET ordinal_map=?",
                (zlib.compress(struct.pack("<II", 0, 999)),),
            )
            snapshot.execute(
                "UPDATE lines SET text='synthetic corruption' WHERE story='ko_KR:matched.txt' AND ordinal=2"
            )
            snapshot.commit()
            result = verify(archive, snapshot)
            self.assertIn("ordinal_map", result["issues"][0]["reason"])
            self.assertIn("snapshot_text_or_metadata", result["issues"][0]["reason"])

    def test_partial_choice_map_keeps_neighboring_dialogue_available(self):
        cn = self.root / "cn/gamedata/story/partial.txt"
        kr = self.root / "kr/gamedata/story/partial.txt"
        cn.write_text(
            '[name="Synthetic NPC"]Before\n[decision(options="One;Two",values="1;2")]\n[name="Synthetic NPC"]After',
            encoding="utf8",
        )
        kr.write_text(
            '[name="Synthetic NPC"]Before\n[decision(options="One;extra;Two",values="1;2")]\n[name="Synthetic NPC"]After',
            encoding="utf8",
        )
        with closing(connect(self.source)) as db:
            ingest(db, self.root, "synthetic-revision", "synthetic/source")
        export_snapshot(self.source, self.snapshot)
        client = create_app(str(self.snapshot), readonly=True).test_client()
        result = client.get(
            "/api/context",
            query_string={
                "story": "zh_CN:partial.txt",
                "ordinal": 1,
                "radius": 3,
                "compare": "1",
                "translation_lang": "ko_KR",
            },
        ).json
        self.assertEqual(
            [r["comparison"]["status"] for r in result["items"]],
            ["matched", "unverified", "matched"],
        )

    def test_v1_maps_do_not_claim_v2_guarantees(self):
        with closing(sqlite3.connect(self.snapshot)) as db:
            db.execute(
                "UPDATE translation_alignments SET method='strict-command-structure-v1'"
            )
            db.commit()
        row = next(r for r in self.query().json["items"] if r["path"] == "matched.txt")
        self.assertEqual(row["comparison"]["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
