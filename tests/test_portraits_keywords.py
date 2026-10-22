"""Synthetic fixtures only; no official dialogue or network required."""
from contextlib import closing
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from app import create_app
from build_portraits import build_portraits, git_blob_sha
from catalog import character_id
from core import connect, ingest
from portraits import Portraits
from translations import tr


class PortraitKeywordTest(unittest.TestCase):
    def test_build_hash_cache_identity_and_immutable_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = BytesIO()
            Image.new('RGBA', (180, 120), (120, 200, 180, 255)).save(content, format='PNG')
            png = content.getvalue()
            manifest = dict(repository='test/source', revision='a'*40, directory='avatars', size=96, version=1, quality=82, files={'char_003_kalts':git_blob_sha(png)})
            output = root/'portraits'
            index = build_portraits(output, manifest, fetch=lambda url:png)
            filename = index['images']['char_003_kalts']
            with Image.open(output/filename) as image:
                self.assertEqual(image.size, (96,96))
                self.assertEqual(image.format, 'WEBP')
            build_portraits(output, manifest, fetch=lambda url:self.fail('Cached image refetched'))
            for name in ('켈시', '凯尔希', 'ケルシー', "Kal'tsit"):
                self.assertEqual(character_id(name), 'char_003_kalts')
                self.assertEqual(Portraits(output).identity(name)['portrait'], '/portraits/'+filename)
            self.assertEqual(character_id('M3'), 'char_4179_monstr')
            self.assertIsNone(character_id('unknown synthetic name'))
            self.assertIsNone(character_id('Sharp'))
            client = create_app(str(root/'unused.sqlite'), True, portrait_root=output).test_client()
            with client.get('/portraits/'+filename) as response:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'image/webp')
                self.assertIn('immutable', response.headers['Cache-Control'])
            self.assertEqual(client.get('/portraits/not-listed.webp').status_code,404)
            bad = {**manifest, 'files':{'char_002_amiya':'b'*40}}
            before = (output/'index.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                build_portraits(output,bad,fetch=lambda url:png)
            self.assertEqual(before, (output/'index.json').read_bytes())

    def test_fonts_are_original_and_versioned(self):
        root=Path(__file__).resolve().parents[1]
        manifest=json.loads((root/'fonts.source.json').read_text())
        client=create_app(readonly=True).test_client()
        import re
        html=client.get('/').text
        url=re.search(r'href="([^"]+/fonts.css)"',html).group(1)
        for font in manifest['files']:
            self.assertEqual(git_blob_sha((root/'web/fonts'/font['filename']).read_bytes()),font['sha'])
            with client.get(url.rsplit('/',1)[0]+'/fonts/'+font['filename']) as response:
                self.assertEqual(response.status_code,200)
                self.assertIn('immutable',response.headers['Cache-Control'])

    def test_keyword_paging_languages_literal_scope_and_footer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('kr','cn','jp','en'):
                for file, count in [('a',31),('b',47),('c',33)]:
                    path=root/folder/'gamedata/story'/f'{file}.txt'
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('\n'.join(f'[name="{("Mon3tr" if i%2 else "켈시")}"]fixture 켈시 100% _ AbC {file}{i}' for i in range(count)),encoding='utf8')
            future=root/'cn/gamedata/story/future.txt'
            future.write_text('[name="Mon3tr"]fixture 凯尔希',encoding='utf8')
            database=root/'test.sqlite'
            with closing(connect(database)) as db:ingest(db,root,'synthetic','test/source')
            client=create_app(str(database),True,portrait_root=root/'none').test_client()
            for lang in ('ko_KR','zh_CN','ja_JP','en_US'):
                keys=[]
                for offset in (0,50,100,150):
                    result=client.get('/api/search',query_string={'q':'켈시','lang':lang,'offset':offset,'details':'0'}).json
                    self.assertEqual(result['total'],111)
                    keys.extend((r['path'],r['ordinal']) for r in result['items'])
                self.assertEqual(len(keys),111)
                self.assertEqual(len(set(keys)),111)
                self.assertEqual(keys,sorted(keys))
            self.assertEqual(client.get('/api/search?q=100%25+_').json['total'],111)
            self.assertEqual(client.get('/api/search?q=abc').json['total'],0)
            self.assertEqual(client.get('/api/search?q=fixture&lang=zh_CN&spoilers=1').json['total'],112)
            self.assertEqual(client.get('/api/search?q=fixture&story=b.txt').json['total'],47)
            self.assertEqual(client.get('/api/search?target=켈시').json['total'],111)
            self.assertEqual(client.get('/api/search?speaker=+&q=+').status_code,400)
            for ui in ('ko','en','zh','ja'):
                html=client.get('/?ui='+ui).text
                footer=html.split('<footer')[1].split('</footer>')[0]
                for key in ('privacy','terms','license','changelog','feedback'):
                    self.assertIn('>'+tr(ui,key),footer)
                self.assertNotIn('required', html.split('id="speaker"')[1].split('>')[0])
