import tempfile
import unittest
from pathlib import Path
from core import connect, ingest, parse, search

class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.path=self.root/'kr/gamedata/story/test.txt';self.path.parent.mkdir(parents=True)
        self.path.write_text('[name="시험 화자"]시험 대상 선생님.\n[predicate(references="1")]\n[name="시험 화자"]다음 대사',encoding='utf8')
        self.db=connect(':memory:');ingest(self.db,self.root,'v1','test/source')
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def test_target_and_context(self):
        result=search(self.db,'시험 화자','시험 대상')
        self.assertEqual(result['total'],1)
        self.assertEqual(len(result['items'][0]['context']),2)
        self.assertNotIn('reviews',result['items'][0])
    def test_failed_import_preserves_data(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(ValueError):ingest(self.db,empty,'bad','test')
        self.assertEqual(search(self.db)['total'],2)
    def test_spoiler_filter(self):
        p=self.root/'cn/gamedata/story/future.txt';p.parent.mkdir(parents=True);p.write_text('[name="甲"]你好',encoding='utf8')
        ingest(self.db,self.root,'v2','test/source')
        self.assertEqual(search(self.db,lang='zh_CN')['total'],0)
        self.assertEqual(search(self.db,lang='zh_CN',spoilers=True)['total'],1)
    def test_branch_kept(self):
        rows=list(parse(self.path.read_text()));self.assertNotEqual(rows[0][3],rows[1][3])
    def test_speaker_is_exact(self):
        self.assertEqual(search(self.db,speaker='시험')['total'],0)
    def test_bilingual_alias(self):
        self.path.write_text('[name="켈시"]시험 대사\n[name="다른 사람"]켈시 선생님.',encoding='utf8')
        ingest(self.db,self.root,'v2','test/source')
        self.assertEqual(search(self.db,speaker='凯尔希')['total'],1)
        self.assertEqual(search(self.db,target='凯尔希')['total'],1)
    def test_shrink_does_not_destroy_active_data(self):
        self.path.write_text('\n'.join('[name="시험 화자"]대사' for _ in range(100)),encoding='utf8')
        ingest(self.db,self.root,'v2','test/source')
        self.path.write_text('[name="시험 화자"]하나',encoding='utf8')
        with self.assertRaises(ValueError):ingest(self.db,self.root,'v3','test/source')
        self.assertEqual(search(self.db)['total'],100)
    def test_legacy_annotations_cannot_hide_or_add_results(self):
        # Existing local DBs can retain old tables, but search must ignore them.
        self.db.execute('CREATE TABLE reviews(line TEXT,target TEXT,kind TEXT,hash TEXT)')
        item=search(self.db,target='시험 대상')['items'][0]
        self.db.execute('INSERT INTO reviews VALUES(?,?,?,?)',(item['id'],'시험 대상','rejected',item['hash']))
        self.db.commit()
        self.assertEqual(search(self.db,target='시험 대상')['total'],1)
        self.assertEqual(search(self.db,target='없는 인물')['total'],0)

if __name__=='__main__':unittest.main()
