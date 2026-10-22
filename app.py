"""Flask entrypoint shared by local development and Vercel Functions."""
import argparse
from contextlib import closing
import hmac
import json
import os
from pathlib import Path
import sqlite3
from flask import Flask, jsonify, request, send_file
from core import connect, ingest, search, review, validate_review
from review_store import PostgresReviews

ROOT = Path(__file__).resolve().parent


def create_app(database=None, readonly=None, store=None):
    app = Flask(__name__, static_folder=None)
    app.config['MAX_CONTENT_LENGTH'] = 16384
    readonly = bool(os.environ.get('VERCEL')) if readonly is None else readonly
    database = database or os.environ.get('ASI_DB') or str(ROOT / ('generated/search.sqlite' if readonly else 'data/index.sqlite'))
    remote_url = os.environ.get('ASI_REVIEW_DATABASE_URL')
    store = store or (PostgresReviews(remote_url) if remote_url else None)

    def open_db(with_reviews=False):
        if readonly:
            path = Path(database).resolve()
            db = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
            db.row_factory = sqlite3.Row
        else:
            db = connect(database)
        if with_reviews and store:
            try:
                db.execute('CREATE TEMP TABLE reviews(line TEXT, target TEXT, expression TEXT, kind TEXT, hash TEXT, PRIMARY KEY(line,target))')
                rows = store.load()
                db.executemany('INSERT INTO temp.reviews VALUES(?,?,?,?,?)', rows)
                db.commit()
            except Exception:
                db.close()
                raise
        return db

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
        return send_file(ROOT / 'web/index.html')

    @app.route('/app.js')
    def javascript():
        return send_file(ROOT / 'web/app.js', mimetype='text/javascript')

    @app.route('/style.css')
    def stylesheet():
        return send_file(ROOT / 'web/style.css', mimetype='text/css')

    @app.route('/api/search')
    def find():
        q = request.args
        # A character-scoped search prevents accidentally scanning the whole corpus.
        if not q.get('speaker', '').strip():
            raise ValueError('말하는 인물을 선택하세요.')
        if any(len(q.get(key, '')) > 300 for key in ('speaker', 'target', 'q')):
            raise ValueError('검색어가 너무 깁니다.')
        try:
            with closing(open_db(with_reviews=True)) as db:
                result = search(db, q.get('speaker','').strip(), q.get('target','').strip(), q.get('q',''), q.get('lang','ko_KR'), q.get('spoilers')=='1', max(0,int(q.get('offset',0))))
            return jsonify(result)
        except sqlite3.OperationalError:
            raise
        except ValueError:
            raise
        except Exception:
            app.logger.exception('Persistent review retrieval failed')
            return jsonify(error='검토 기록을 불러오지 못했습니다. 잠시 후 다시 시도하세요.'), 503

    @app.route('/api/status')
    def status():
        with closing(open_db()) as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='import_status'").fetchone()
            row = db.execute('SELECT payload FROM import_status WHERE id=1').fetchone() if exists else None
        result = json.loads(row[0]) if row else {'dialogue_lines':0}
        result['reviews_enabled'] = bool(not readonly or store)
        result['readonly'] = readonly
        return jsonify(result)

    @app.route('/api/speakers')
    def speakers():
        lang = request.args.get('lang', 'ko_KR')
        if lang not in ('ko_KR','zh_CN'):
            raise ValueError('지원하지 않는 언어')
        spoilers = request.args.get('spoilers') == '1'
        with closing(open_db()) as db:
            names = [r[0] for r in db.execute("SELECT DISTINCT l.speaker FROM lines l JOIN stories s ON s.id=l.story WHERE s.lang=? AND l.speaker!='' AND (? OR EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)) ORDER BY l.speaker", (lang, spoilers))]
        return jsonify(names)

    @app.route('/api/review', methods=['POST'])
    def save_review():
        token = os.environ.get('ASI_ADMIN_TOKEN','')
        if len(token) < 32 or not hmac.compare_digest(request.headers.get('Authorization','').encode(), ('Bearer '+token).encode()):
            return jsonify(error='관리자 인증이 필요합니다.'), 401
        if readonly and not store:
            return jsonify(error='검토 기록의 영구 저장소가 연결되지 않았습니다.'), 503
        payload = request.get_json(silent=True)
        with closing(open_db()) as db:
            if store:
                payload = validate_review(db,payload)
                try:
                    store.save(payload)
                except Exception:
                    app.logger.exception('Persistent review save failed')
                    return jsonify(error='검토 기록을 저장하지 못했습니다.'), 503
            else:
                review(db,payload)
        return jsonify(ok=True)

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
