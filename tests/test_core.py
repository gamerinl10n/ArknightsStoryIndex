import tempfile
import unittest
from pathlib import Path
from core import connect, ingest, parse, search, review

class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.path=self.root/'kr/gamedata/story/test.txt'
        self.path.parent.mkdir(parents=True)
        self.path.write_text('[name="시험 화자"]시험 대상 선생님.\n[predicate(references="1")]\n[name="시험 화자"]다음 대사',encoding='utf8')
        self.db=connect(':memory:')
        ingest(self.db,self.root,'v1','test/source')
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def test_search_review_and_change(self):
        item=search(self.db,'시험 화자','시험 대상')['items'][0]
        review(self.db,dict(line=item['id'],target='시험 대상',expression='선생님',kind='direct',hash=item['hash']))
        self.assertEqual(search(self.db,target='시험 대상')['items'][0]['reviews'][0]['status'],'reviewed')
        self.path.write_text('[name="시험 화자"]시험 대상 님.',encoding='utf8')
        ingest(self.db,self.root,'v2','test/source')
        self.assertEqual(search(self.db,target='시험 대상')['items'][0]['reviews'][0]['status'],'needs_review')
        with self.assertRaises(ValueError):review(self.db,dict(line=item['id'],target='시험 대상',expression='',kind='direct',hash=item['hash']))
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
        rows=list(parse(self.path.read_text()))
        self.assertNotEqual(rows[0][3],rows[1][3])

if __name__=='__main__':unittest.main()
