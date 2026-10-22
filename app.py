import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from core import connect, ingest, search, review

DB = os.environ.get('ASI_DB', 'data/index.sqlite')

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json; charset=utf-8'):
        content = json.dumps(data, ensure_ascii=False).encode() if mime.startswith('application/json') else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        u = urlsplit(self.path)
        q = {k:v[0] for k,v in parse_qs(u.query).items()}
        try:
            if u.path == '/api/search':
                with connect(DB) as db:
                    data = search(db, q.get('speaker',''),q.get('target',''),q.get('q',''),q.get('lang','ko_KR'),q.get('spoilers')=='1',max(0,int(q.get('offset',0))))
                return self.reply(200,data)
            if u.path == '/api/speakers':
                with connect(DB) as db:
                    data = [r[0] for r in db.execute("SELECT DISTINCT speaker FROM lines WHERE speaker!='' ORDER BY speaker")]
                return self.reply(200,data)
            files = {'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
            if u.path in files:
                file = Path(__file__).parent/'web'/files[u.path]
                return self.reply(200,file.read_bytes(),{'html':'text/html','js':'text/javascript','css':'text/css'}[file.suffix[1:]]+'; charset=utf-8')
            self.reply(404,{'error':'찾을 수 없습니다.'})
        except (ValueError,KeyError) as e:
            self.reply(400,{'error':str(e)})

    def do_POST(self):
        if self.path != '/api/review':
            return self.reply(404,{'error':'찾을 수 없습니다.'})
        token = os.environ.get('ASI_ADMIN_TOKEN','')
        if len(token)<32 or not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+token):
            return self.reply(401,{'error':'관리자 인증이 필요합니다.'})
        try:
            size = int(self.headers.get('Content-Length',0))
            if not 0<size<=16384:
                raise ValueError('잘못된 요청 크기')
            payload = json.loads(self.rfile.read(size))
            with connect(DB) as db:
                review(db,payload)
            self.reply(200,{'ok':True})
        except (ValueError,KeyError,TypeError) as e:
            self.reply(400,{'error':str(e)})

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--import-root')
    p.add_argument('--revision')
    p.add_argument('--source',default='ArknightsAssets/ArknightsGamedata')
    p.add_argument('--port',type=int,default=8000)
    p.add_argument('--host',default='127.0.0.1')
    a = p.parse_args()
    Path(DB).parent.mkdir(parents=True,exist_ok=True)
    with connect(DB) as db:
        if a.import_root:
            if not a.revision:
                p.error('--revision is required for provenance')
            print(ingest(db,a.import_root,a.revision,a.source),'lines imported')
            raise SystemExit
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
