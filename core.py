"""Raw script ingestion and conservative, evidence-first retrieval. Python 3.11+."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS stories(id TEXT PRIMARY KEY, lang TEXT, path TEXT, revision TEXT, source TEXT, raw TEXT);
    CREATE TABLE IF NOT EXISTS snapshots(story TEXT, revision TEXT, raw TEXT, PRIMARY KEY(story,revision));
    CREATE TABLE IF NOT EXISTS lines(id TEXT PRIMARY KEY, story TEXT, ordinal INTEGER, speaker TEXT, text TEXT, branch TEXT, hash TEXT);
    CREATE INDEX IF NOT EXISTS speaker_idx ON lines(speaker);
    CREATE INDEX IF NOT EXISTS story_idx ON lines(story,ordinal);
    CREATE TABLE IF NOT EXISTS reviews(line TEXT, target TEXT, expression TEXT, kind TEXT, hash TEXT, PRIMARY KEY(line,target));
    CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, line TEXT, target TEXT, payload TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    return db


def parse(raw):
    branch = 'main'
    for n, line in enumerate(raw.splitlines()):
        command = re.match(r'^\[(\w+)(.*?)\](.*)$', line.strip())
        if not command:
            continue
        prop, attrs, text = command.groups()
        prop = prop.lower()
        if prop == 'name' and attrs.lstrip().startswith('='):
            attrs = 'name' + attrs
        pairs = dict((m[0], m[1] if m[1] else m[2]) for m in re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|([^,\s]+))', attrs))
        if prop in ('predicate', 'decision', 'label', 'gotolabel'):
            branch = f'{prop}:{attrs.strip()}'
        if prop not in ('name', 'multiline'):
            continue
        speaker = pairs.get('name', '')
        text = text or pairs.get('content', '')
        if text.strip():
            yield n, speaker, re.sub(r'<[^>]+>', '', text).replace('\\n', '\n'), branch


def ingest(db, root, revision, source):
    """Validate entire batch before transactional replacement; raw snapshots stay in SQLite."""
    root = Path(root)
    batch = []
    for lang, folder in [('ko_KR', 'kr'), ('zh_CN', 'cn')]:
        for f in sorted((root / folder / 'gamedata/story').rglob('*.txt')):
            raw = f.read_text(encoding='utf-8-sig')
            rows = list(parse(raw))
            if not rows:
                continue
            path = f.relative_to(root / folder / 'gamedata/story').as_posix()
            batch.append((lang, path, raw, rows))
    if not batch or not any(x[0] == 'ko_KR' for x in batch):
        raise ValueError('한국어 대사가 없는 입력입니다. 기존 데이터를 유지합니다.')
    with db:
        for lang, path, raw, rows in batch:
            sid = f'{lang}:{path}'
            db.execute('INSERT OR REPLACE INTO stories VALUES(?,?,?,?,?,?)', (sid, lang, path, revision, source, raw))
            db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)', (sid, revision, raw))
            db.execute('DELETE FROM lines WHERE story=?', (sid,))
            for n, speaker, text, branch in rows:
                digest = hashlib.sha256(json.dumps([speaker, text, branch], ensure_ascii=False).encode()).hexdigest()
                db.execute('INSERT INTO lines VALUES(?,?,?,?,?,?,?)', (f'{sid}:{n}', sid, n, speaker, text, branch, digest))
    return sum(len(x[3]) for x in batch)


def search(db, speaker='', target='', query='', lang='ko_KR', spoilers=False, offset=0):
    if lang not in ('ko_KR', 'zh_CN'):
        raise ValueError('지원하지 않는 언어')
    clauses = ['s.lang=?']
    args = [lang]
    for col, val in [('l.speaker', speaker), ('l.text', query)]:
        if val:
            clauses.append(f'instr({col},?)>0')
            args.append(val)
    if not spoilers:
        clauses.append("EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)")
    if target:
        clauses.append('(instr(l.text,?)>0 OR EXISTS(SELECT 1 FROM reviews r WHERE r.line=l.id AND r.target=?))')
        args += [target, target]
    where = ' AND '.join(clauses)
    total = db.execute(f'SELECT count(*) FROM lines l JOIN stories s ON s.id=l.story WHERE {where}', args).fetchone()[0]
    rows = db.execute(f'SELECT l.*,s.lang,s.path,s.revision,s.source FROM lines l JOIN stories s ON s.id=l.story WHERE {where} ORDER BY s.path,l.ordinal LIMIT 50 OFFSET ?', args+[offset]).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        reviews = [dict(r) for r in db.execute('SELECT * FROM reviews WHERE line=?', (row['id'],))]
        for r in reviews:
            r['status'] = 'reviewed' if r['hash'] == row['hash'] else 'needs_review'
        item['reviews'] = reviews
        # Physical neighbours are explicitly not inferred conversation partners.
        item['context'] = [dict(r) for r in db.execute('SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal BETWEEN ? AND ? ORDER BY ordinal', (row['story'], row['ordinal']-8, row['ordinal']+8))]
        item['parallel'] = [dict(r) for r in db.execute('SELECT l.speaker,l.text,s.lang FROM lines l JOIN stories s ON s.id=l.story WHERE s.path=? AND l.ordinal=? AND s.lang!=?', (row['path'], row['ordinal'], lang))]
        results.append(item)
    return {'total': total, 'items': results}


def review(db, payload):
    line = db.execute('SELECT * FROM lines WHERE id=?', (payload['line'],)).fetchone()
    if not line or line['hash'] != payload['hash']:
        raise ValueError('원문이 변경되었습니다. 새로 검색한 뒤 검토하세요.')
    if payload['kind'] not in ('direct', 'reference', 'related', 'rejected'):
        raise ValueError('잘못된 분류')
    if not payload['target'].strip() or (payload['expression'] and payload['expression'] not in line['text']):
        raise ValueError('대상과 원문에 존재하는 표현을 입력하세요.')
    with db:
        db.execute('INSERT INTO history(line,target,payload) VALUES(?,?,?)', (line['id'],payload['target'],json.dumps(payload,ensure_ascii=False)))
        db.execute('INSERT OR REPLACE INTO reviews VALUES(?,?,?,?,?)', (payload['line'],payload['target'],payload['expression'],payload['kind'],payload['hash']))
