"""Voice fixtures are synthetic and never presented as official dialogue."""
from unittest.mock import patch
import unittest
from app import create_app
from voice_catalog import search_voices


def fixture():
    return {'revision':'test-revision','rows':{
        'line-1': {'identity':['char_test','key-1','voice-1'], 'variants':{
            'ko_KR':{'voiceTitle':'시험 제목','voiceText':'시험 대사 <script>','voiceIndex':1,'lockDescription':'조건'},
            'zh_CN':{'voiceTitle':'测试','voiceText':'你好 fixture','voiceIndex':1}}},
        'line-2': {'identity':['char_other','key-2','voice-2'], 'variants':{
            'zh_CN':{'voiceTitle':'仅测试','voiceText':'你好 second','voiceIndex':2}}}
    }}


class VoiceCatalogTest(unittest.TestCase):
    def test_character_only_and_multilingual_query(self):
        items,total=search_voices(fixture(),'char_test','你好','ko_KR')
        self.assertEqual(total,1)
        self.assertEqual(items[0][2]['voiceText'],'시험 대사 <script>')
        self.assertEqual(search_voices(fixture(),'char_test','','ko_KR')[1],1)
        self.assertEqual(search_voices(fixture(),'unknown','','ko_KR')[1],0)

    def test_pagination_does_not_duplicate_keys(self):
        first,total=search_voices(fixture(),'','你好','ko_KR',0,1)
        second,_=search_voices(fixture(),'','你好','ko_KR',1,1)
        self.assertEqual(total,2)
        self.assertNotEqual(first[0][0],second[0][0])

    def test_pages_escape_text_and_show_missing_language(self):
        with patch('app.load_voice_catalog',return_value=fixture()):
            client=create_app().test_client()
            for language in ('ko','zh','ja','en'):
                response=client.get('/voices',query_string={'ui':language,'q':'你好'})
                self.assertEqual(response.status_code,200)
                self.assertIn('line-1',response.text)
                self.assertIn('line-2',response.text)
                self.assertIn('你好 second',__import__('re').sub(r'<[^>]*>', '', response.text))
            html=client.get('/voices?ui=ko&character=char_test').text
            self.assertIn('&lt;script&gt;',html)
            self.assertIn('voice-search.mjs',html)
            self.assertEqual(client.get('/voices?offset=-1').status_code,400)
            self.assertEqual(client.get('/voices?offset=bad').status_code,400)
            self.assertEqual(client.get('/voices').status_code,200)

    def test_missing_catalog_is_an_explicit_unavailable_state(self):
        with patch('app.load_voice_catalog',side_effect=FileNotFoundError):
            self.assertEqual(create_app().test_client().get('/voices').status_code,503)

    def test_builder_rejects_conflicting_ids_and_does_not_replace_output(self):
        import io,json,tempfile
        from pathlib import Path
        from voice_catalog import build_voice_catalog
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'dataset-source.json').write_text('{"revision":"fixture"}')
            (root/'generated').mkdir();output=root/'generated/voices.json.gz';output.write_bytes(b'previous')
            record={'charId':'char_test','wordKey':'key','voiceId':'voice','voiceText':'synthetic','voiceTitle':'synthetic'}
            sources=[{'charWords':{'same':record}},{'charWords':{'same':{**record,'charId':'different'}}}]
            with patch('voice_catalog.urlopen',side_effect=[io.BytesIO(json.dumps(d).encode()) for d in sources]):
                with self.assertRaises(ValueError):build_voice_catalog(root)
            self.assertEqual(output.read_bytes(),b'previous')


    def test_highlights_preserve_unicode_and_escape_source(self):
        from voice_catalog import voice_highlights
        for text, query in [('Straße <script>', 'STRASSE'), ('İstanbul', 'i'), ('aaaa', 'aa')]:
            parts = voice_highlights(text,query)
            self.assertEqual(''.join(part for part,matched in parts),text)
            self.assertTrue(any(matched for part,matched in parts))
        self.assertEqual(voice_highlights('unchanged',''),[('unchanged',False)])

    def test_registered_alias_completions_and_reset_page(self):
        from voice_catalog import voice_completions
        from catalog import character_id
        data=fixture(); data['rows']['line-1']['identity'][0]=character_id('M3')
        values=dict(voice_completions(data,'ko_KR'))
        self.assertIn('M3',values)
        with patch('app.load_voice_catalog',return_value=data):
            client=create_app().test_client()
            html=client.get('/voices?ui=ko&character=M3&q=fixture&show=zh_CN').text
            self.assertIn('list="voice-character-options"',html)
            self.assertIn('class="query-highlight"',html)
            self.assertIn('class="reset-search voice-reset"',html)
            empty=client.get('/voices?ui=ko&show=zh_CN').text
            self.assertNotIn('class="result-card"',empty)
            self.assertIn('name="q" value=""',empty)
