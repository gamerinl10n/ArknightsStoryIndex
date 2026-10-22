"""Flask entrypoint shared by local development and Vercel Functions."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
from flask import Flask, jsonify, request, send_file, render_template, abort
from core import connect, ingest, search, LANGUAGES, context_window
from pages import PAGES
from translations import STRINGS, UI_LANGS, tr
from localized_pages import get_page
import hashlib
from runtime_snapshot import materialize

ROOT = Path(__file__).resolve().parent


def create_app(database=None, readonly=None):
    app = Flask(__name__, static_folder=None, template_folder=str(ROOT / "web"))
    app.config['MAX_CONTENT_LENGTH'] = 16384
    readonly = bool(os.environ.get('VERCEL')) if readonly is None else readonly
    database = database or os.environ.get('ASI_DB') or str(ROOT / ('generated/search.sqlite.gz' if readonly else 'data/index.sqlite'))
    def open_db():
        if readonly:
            path = materialize(database)
            db = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
            db.row_factory = sqlite3.Row
        else:
            db = connect(database)
        return db

    version = os.environ.get('VERCEL_DEPLOYMENT_ID') or os.environ.get('VERCEL_URL') or os.environ.get('VERCEL_GIT_COMMIT_SHA') or hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'web').glob('*')) if p.is_file())).hexdigest()[:16]
    @app.context_processor
    def template_context():
        ui = request.args.get('ui', 'ko')
        if ui not in UI_LANGS: ui = 'ko'
        return dict(ui=ui, t=lambda key:tr(ui,key), ui_languages=UI_LANGS, corpus_languages={'ko_KR':'한국어', 'zh_CN':'中文', 'ja_JP':'日本語', 'en_US':'English'}, deployment_version=version)

    @app.route('/version.json')
    def version_json():
        return jsonify(version=version)

    @app.route('/i18n.js')
    def ui_copy():
        ui = request.args.get('ui','ko')
        if ui not in UI_LANGS: ui='ko'
        return app.response_class('window.ASI = '+json.dumps({'ui':ui,'strings':STRINGS[ui]},ensure_ascii=False)+';', mimetype='text/javascript')

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'"
        return response

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(sqlite3.OperationalError)
    def unavailable(error):
        app.logger.error('Search database unavailable: %s', type(error).__name__)
        return jsonify(error='검색 데이터가 준비되지 않았습니다. 배포 빌드와 데이터 생성을 확인하세요.'), 503

    @app.route('/')
    def home():
        return render_template('index.html',title=tr(request.args.get('ui') if request.args.get('ui') in UI_LANGS else 'ko','search'))

    @app.route('/app.js')
    def javascript():
        return send_file(ROOT / 'web/app.js', mimetype='text/javascript')

    @app.route('/style.css')
    def stylesheet():
        return send_file(ROOT / 'web/style.css', mimetype='text/css')

    @app.route('/update-monitor.mjs')
    @app.route('/update-banner.mjs')
    @app.route('/update-banner.css')
    @app.route('/theme.js')
    @app.route('/chrome.js')
    @app.route('/theme-control.css')
    def shared_assets():
        filename = request.path.lstrip('/')
        return send_file(ROOT / 'web' / filename, mimetype='text/css' if filename.endswith('.css') else 'text/javascript')

    @app.route('/<page>')
    def document(page):
        if page not in PAGES:
            abort(404)
        ui = request.args.get('ui','ko')
        data = get_page(page,ui if ui in UI_LANGS else 'ko')
        return render_template('document.html',title=data['title'],page=data)

    @app.route('/api/search')
    def find():
        q = request.args
        # A character-scoped search prevents accidentally scanning the whole corpus.
        if not q.get('speaker', '').strip():
            raise ValueError('말하는 인물을 선택하세요.')
        if any(len(q.get(key, '')) > 300 for key in ('speaker', 'target', 'q')):
            raise ValueError('검색어가 너무 깁니다.')
        with closing(open_db()) as db:
            result = search(db, q.get('speaker','').strip(), q.get('target','').strip(), q.get('q',''), q.get('lang','ko_KR'), q.get('spoilers')=='1', max(0,int(q.get('offset',0))))
        return jsonify(result)

    @app.route('/api/context')
    def context():
        with closing(open_db()) as db:
            result = context_window(db, request.args.get('story',''), int(request.args.get('ordinal',0)), int(request.args.get('radius',15)))
        return jsonify(result)

    @app.route('/api/status')
    def status():
        with closing(open_db()) as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='import_status'").fetchone()
            row = db.execute('SELECT payload FROM import_status WHERE id=1').fetchone() if exists else None
        result = json.loads(row[0]) if row else {'dialogue_lines':0}
        result['readonly'] = readonly
        return jsonify(result)

    @app.route('/api/speakers')
    def speakers():
        lang = request.args.get('lang', 'ko_KR')
        if lang not in LANGUAGES:
            raise ValueError('지원하지 않는 언어')
        spoilers = request.args.get('spoilers') == '1'
        with closing(open_db()) as db:
            names = [r[0] for r in db.execute("SELECT DISTINCT l.speaker FROM lines l JOIN stories s ON s.id=l.story WHERE s.lang=? AND l.speaker!='' AND (? OR EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)) ORDER BY l.speaker", (lang, spoilers))]
        return jsonify(names)

    @app.route('/api/suggestions')
    def suggestions():
        lang = request.args.get('lang', 'ko_KR')
        if lang not in LANGUAGES:
            raise ValueError('지원하지 않는 언어')
        spoilers = request.args.get('spoilers') == '1'
        with closing(open_db()) as db:
            counts = dict(db.execute("SELECT l.speaker,count(*) FROM lines l JOIN stories s ON s.id=l.story WHERE s.lang=? AND l.speaker!='' AND (? OR EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)) GROUP BY l.speaker",(lang,spoilers)))
        result = {name: {'value':name, 'label':name, 'count':count} for name,count in counts.items()}
        for character in json.loads((ROOT/'characters.json').read_text(encoding='utf-8')):
            names = character['names'].get(lang, [])
            count = sum(counts.get(name,0) for name in names)
            if not count:
                continue
            alternate = character.get('aliases', []) + [n for group in character['names'].values() for n in group]
            for alias in alternate:
                if alias not in result:
                    result[alias] = {'value':alias,'label':' / '.join(names),'count':count}
        return jsonify(sorted(result.values(),key=lambda r:r['value']))

    return app


app = create_app()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--import-root')
    p.add_argument('--revision')
    p.add_argument('--source',default='ArknightsAssets/ArknightsGamedata')
    p.add_argument('--port',type=int,default=8000)
    p.add_argument('--host',default='127.0.0.1')
    a = p.parse_args()
    database = os.environ.get('ASI_DB',str(ROOT/'data/index.sqlite'))
    if not os.environ.get('VERCEL'):
        Path(database).parent.mkdir(parents=True,exist_ok=True)
        with closing(connect(database)) as db:
            if a.import_root:
                if not a.revision:
                    p.error('--revision is required for provenance')
                print(ingest(db,a.import_root,a.revision,a.source),'lines imported')
                raise SystemExit
    app.run(host=a.host,port=a.port)
