from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from app import create_app
from build import export_snapshot
from core import connect,ingest

class MemoryReviews:
    def __init__(self):self.rows={}
    def load(self):return list(self.rows.values())
    def save(self,p):self.rows[(p['line'],p['target'])]=tuple(p[k] for k in ('line','target','expression','kind','hash'))

class DeploymentTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        path=self.root/'kr/gamedata/story/test.txt';path.parent.mkdir(parents=True)
        path.write_text('[name="Mon3tr"]켈시 선생님.\n[name="켈시"]그래.',encoding='utf8')
        self.source=self.root/'source.sqlite';self.snapshot=self.root/'search.sqlite'
        with closing(connect(self.source)) as db:ingest(db,self.root,'test-revision','test/source')
        export_snapshot(self.source,self.snapshot)
        self.client=create_app(str(self.snapshot),readonly=True).test_client()
    def tearDown(self):self.tmp.cleanup()
    def test_root_assets_and_readonly_search(self):
        before=self.snapshot.read_bytes()
        for url in ('/','/app.js','/style.css','/api/status','/api/speakers'):
            with self.client.get(url) as response:
                self.assertEqual(response.status_code,200,url)
        response=self.client.get('/api/search?speaker=M3&target=켈시')
        self.assertEqual(response.json['total'],1)
        self.assertFalse(self.client.get('/api/status').json['reviews_enabled'])
        self.assertEqual(before,self.snapshot.read_bytes())
    def test_snapshot_excludes_raw_and_review_history(self):
        with closing(sqlite3.connect(self.snapshot)) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn('snapshots',tables);self.assertNotIn('history',tables)
            self.assertNotIn('raw',[r[1] for r in db.execute('PRAGMA table_info(stories)')])
            self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0],0)
    def test_no_ephemeral_review_writes(self):
        self.assertEqual(self.client.post('/api/review',json={}).status_code,401)
        with patch.dict(os.environ,{'ASI_ADMIN_TOKEN':'x'*32}):
            self.assertEqual(self.client.post('/api/review',json={},headers={'Authorization':'Bearer '+'x'*32}).status_code,503)
    def test_durable_overlay_and_new_app_instance(self):
        store=MemoryReviews();app=create_app(str(self.snapshot),True,store);client=app.test_client()
        item=client.get('/api/search?speaker=M3&target=켈시').json['items'][0]
        payload=dict(line=item['id'],hash=item['hash'],target='켈시',expression='선생님',kind='direct')
        with patch.dict(os.environ,{'ASI_ADMIN_TOKEN':'x'*32}):
            r=client.post('/api/review',json=payload,headers={'Authorization':'Bearer '+'x'*32})
        self.assertEqual(r.status_code,200)
        new_client=create_app(str(self.snapshot),True,store).test_client()
        data=new_client.get('/api/search?speaker=M3&target=켈시').json
        self.assertEqual(data['items'][0]['reviews'][0]['status'],'reviewed')
        store.rows.clear()
        self.assertEqual(new_client.get('/api/search?speaker=M3&target=켈시').json['items'][0]['reviews'],[])
    def test_bad_search_and_missing_data(self):
        self.assertEqual(self.client.get('/api/search?speaker=M3&offset=bad').status_code,400)
        self.assertEqual(self.client.get('/api/search').status_code,400)
        client=create_app(str(self.root/'missing.sqlite'),True).test_client()
        self.assertEqual(client.get('/api/status').status_code,503)
        self.assertFalse((self.root/'missing.sqlite').exists())

    def test_store_failure_never_returns_unreviewed_success(self):
        class BrokenStore:
            def load(self):raise RuntimeError('unavailable')
            def save(self,payload):raise RuntimeError('unavailable')
        client=create_app(str(self.snapshot),True,BrokenStore()).test_client()
        self.assertEqual(client.get('/api/search?speaker=M3').status_code,503)
        item=self.client.get('/api/search?speaker=M3').json['items'][0]
        payload=dict(line=item['id'],hash=item['hash'],target='켈시',expression='선생님',kind='direct')
        with patch.dict(os.environ,{'ASI_ADMIN_TOKEN':'x'*32}):
            self.assertEqual(client.post('/api/review',json=payload,headers={'Authorization':'Bearer '+'x'*32}).status_code,503)

    def test_stale_source_cannot_be_saved_to_remote(self):
        store=MemoryReviews();client=create_app(str(self.snapshot),True,store).test_client()
        payload=dict(line='ko_KR:test.txt:0',hash='old',target='켈시',expression='선생님',kind='direct')
        with patch.dict(os.environ,{'ASI_ADMIN_TOKEN':'x'*32}):
            self.assertEqual(client.post('/api/review',json=payload,headers={'Authorization':'Bearer '+'x'*32}).status_code,400)
        self.assertEqual(store.rows,{})
