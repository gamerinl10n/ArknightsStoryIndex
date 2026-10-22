"""Synthetic evidence fixtures, never official dialogue."""

import tempfile
import unittest
from pathlib import Path
from core import connect, ingest, parse, search


class EvidenceTest(unittest.TestCase):
    def test_text_formats_preserve_source_rows_and_unknown_speakers(self):
        raw = "\n".join(
            [
                '[Subtitle(text="자막 [대괄호]와 \\"인용\\"")]',
                "[Narration]<b>서술</b>",
                '[Decision(options="첫째;둘째",values="1;2")]',
                '[multiline(name="A")]한 줄',
                '[multiline(name="A",end=true)]다음 줄',
                '[Sticker(text="글자")]',
                "[Tutorial]안내",
            ]
        )
        rows = list(parse(raw))
        self.assertEqual([r[0] for r in rows], list(range(6)))
        self.assertEqual(rows[0][2], '자막 [대괄호]와 "인용"')
        self.assertEqual(rows[1][2], "서술")
        self.assertEqual(rows[2][2], "첫째\n둘째")
        self.assertEqual([r[1] for r in rows[:3]], ["", "", ""])
        self.assertNotEqual(
            list(parse('[Predicate]\n[name="A"]x\n[Predicate]\n[name="A"]y'))[0][3],
            list(parse('[Predicate]\n[name="A"]x\n[Predicate]\n[name="A"]y'))[1][3],
        )

    def test_global_ranking_pagination_and_branch_barriers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "kr/gamedata/story/test.txt"
            path.parent.mkdir(parents=True)
            # Fifty earlier third-person mentions must not hide a later exchange.
            raw = ['[name="C"]다른 상대']
            for _ in range(55):
                raw.extend(['[name="A"]B 언급', '[name="C"]응답'])
            raw.extend(
                [
                    '[Predicate(references="1")]',
                    '[name="B"]질문',
                    '[name="A"]B 대답',
                    '[name="B"]후속',
                    '[Predicate(references="2")]',
                    '[name="A"]B 분기 밖',
                ]
            )
            path.write_text("\n".join(raw), encoding="utf8")
            db = connect(":memory:")
            self.addCleanup(db.close)
            ingest(db, root, "synthetic", "test")
            first = search(db, "A", "B", include_details=False)
            rest = search(db, "A", "B", offset=50, include_details=False)
            self.assertEqual(first["total"], 57)
            self.assertEqual(first["items"][0]["text"], "B 대답")
            self.assertEqual(first["items"][0]["nearby_turns"], 2)
            self.assertEqual(
                len(set(r["id"] for r in first["items"] + rest["items"])), 57
            )
            boundary = next(r for r in rest["items"] if r["text"] == "B 분기 밖")
            self.assertEqual(boundary["nearby_turns"], 0)
            self.assertEqual(
                search(db, query="B", include_details=False)["items"][0]["ordinal"], 1
            )
