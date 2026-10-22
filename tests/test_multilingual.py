from contextlib import closing
from pathlib import Path
import tempfile
import unittest
from app import create_app
from core import connect, ingest, aliases

class MultilingualTest(unittest.TestCase):
    def test_four_languages_aliases_context_and_ui(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('kr','cn','jp','en'):
                p=root/folder/'gamedata/story/test.txt';p.parent.mkdir(parents=True)
                p.write_text('\n'.join('[name="Mon3tr"]test '+str(n) for n in range(240)),encoding='utf-8')
            path=root/'test.sqlite'
            with closing(connect(path)) as db: ingest(db,root,'fixture','test')
            client=create_app(str(path),readonly=True).test_client()
            for code in ('ko_KR','zh_CN','ja_JP','en_US'):
                result=client.get('/api/search',query_string={'speaker':'M3','lang':code}).json
                self.assertEqual(result['total'],240)
                item=result['items'][0]
                result=client.get('/api/context',query_string={'story':item['story'],'ordinal':120,'radius':999}).json
                self.assertEqual(len(result['items']),201)
            self.assertEqual(client.get('/api/context?story=missing').status_code,400)
            for ui in ('ko','zh','ja','en'):
                for page in ('','search','help','privacy','terms','license','changelog'):
                    r=client.get('/'+page+'?ui='+ui,follow_redirects=True)
                    self.assertEqual(r.status_code,200)
                    self.assertIn(f'<html lang="{ui}">',r.text)
                    self.assertIn('https://tally.so/r/lb2Lxo',r.text)
            for page in ('privacy','terms','license','changelog'):
                response=client.get('/'+page+'?ui=zh')
                self.assertIn('class="document-language" lang="ko"',response.text)
                self.assertIn('class="document-language" lang="en"',response.text)
                self.assertNotIn('class="segmented language-switch"',response.text)
            self.assertEqual(client.get('/version.json').status_code,200)
            self.assertIn('version',client.get('/version.json').json)
    def test_official_id_names(self):
        self.assertIn('ケルシー',aliases('켈시','ja_JP'))
        self.assertIn("Kal'tsit",aliases('凯尔希','en_US'))
        self.assertEqual(aliases('M3','ja_JP'),['Mon3tr'])

    def test_localized_suggestions_accept_other_language_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder,name in [('kr','아미야'),('en','Amiya'),('jp','アーミヤ'),('cn','阿米娅')]:
                p=root/folder/'gamedata/story/test.txt';p.parent.mkdir(parents=True)
                p.write_text(f'[name="{name}"]Synthetic fixture',encoding='utf8')
            database=root/'test.sqlite'
            with closing(connect(database)) as db:ingest(db,root,'synthetic','test/source')
            client=create_app(str(database),True).test_client()
            for lang,name in [('ko_KR','아미야'),('en_US','Amiya'),('ja_JP','アーミヤ'),('zh_CN','阿米娅')]:
                rows=client.get('/api/suggestions',query_string={'lang':lang}).json
                self.assertEqual([row['value'] for row in rows],[name])
                self.assertIn('아미야',rows[0]['lookup'])
                self.assertEqual(client.get('/api/search',query_string={'speaker':'아미야','lang':lang,'details':'0'}).json['items'][0]['speaker'],name)
