"""Raw script ingestion and conservative, evidence-first retrieval. Python 3.11+."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

def aliases(value, lang):
    path = Path(__file__).parent / 'characters.json'
    for character in json.loads(path.read_text(encoding='utf-8')):
        all_names = [character['id']] + character.get('aliases', []) + [n for names in character['names'].values() for n in names]
        if value.casefold() in [n.casefold() for n in all_names]:
            return character['names'].get(lang, [value])
    return [value]



def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS stories(id TEXT PRIMARY KEY, lang TEXT, path TEXT, revision TEXT, source TEXT, raw TEXT);
    CREATE TABLE IF NOT EXISTS snapshots(story TEXT, revision TEXT, raw TEXT, PRIMARY KEY(story,revision));
    CREATE TABLE IF NOT EXISTS lines(id TEXT PRIMARY KEY, story TEXT, ordinal INTEGER, speaker TEXT, text TEXT, branch TEXT, hash TEXT);
    CREATE INDEX IF NOT EXISTS story_path_idx ON stories(path,lang);
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
    report = {'files': 0, 'dialogue_lines': 0, 'unparsed_text_lines': 0}

    for lang, folder in [('ko_KR', 'kr'), ('zh_CN', 'cn')]:
        for f in sorted((root / folder / 'gamedata/story').rglob('*.txt')):
            raw = f.read_text(encoding='utf-8-sig')
            rows = list(parse(raw))
            report['files'] += 1
            report['dialogue_lines'] += len(rows)
            report['unparsed_text_lines'] += sum(bool(x.strip()) and not x.lstrip().startswith(('[','//')) for x in raw.splitlines())
            path = f.relative_to(root / folder / 'gamedata/story').as_posix()
            batch.append((lang, path, raw, rows))
    if not batch or not any(x[0] == 'ko_KR' and x[3] for x in batch):
        raise ValueError('한국어 대사가 없는 입력입니다. 기존 데이터를 유지합니다.')
    old_count = db.execute('SELECT count(*) FROM lines').fetchone()[0]
    if old_count >= 100 and report['dialogue_lines'] < old_count * 0.8:
        raise ValueError('대사 수가 20% 이상 감소했습니다. 기존 데이터를 유지합니다.')
    with db:
        for lang, path, raw, rows in batch:
            sid = f'{lang}:{path}'
            db.execute('INSERT OR REPLACE INTO stories VALUES(?,?,?,?,?,?)', (sid, lang, path, revision, source, raw))
            db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)', (sid, revision, raw))
            db.execute('DELETE FROM lines WHERE story=?', (sid,))
            for n, speaker, text, branch in rows:
                digest = hashlib.sha256(json.dumps([speaker, text, branch], ensure_ascii=False).encode()).hexdigest()
                db.execute('INSERT INTO lines VALUES(?,?,?,?,?,?,?)', (f'{sid}:{n}', sid, n, speaker, text, branch, digest))
        db.execute('CREATE TABLE IF NOT EXISTS import_status(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT)')
        db.execute('INSERT OR REPLACE INTO import_status VALUES(1,?)', (json.dumps({**report, 'revision': revision, 'source': source}),))
    return sum(len(x[3]) for x in batch)


def search(db, speaker='', target='', query='', lang='ko_KR', spoilers=False, offset=0):
    if lang not in ('ko_KR', 'zh_CN'):
        raise ValueError('지원하지 않는 언어')
    clauses = ['s.lang=?']
    args = [lang]
    if speaker:
        names = aliases(speaker, lang)
        clauses.append('l.speaker IN (' + ','.join('?' for _ in names) + ')')
        args.extend(names)
    if query:
        clauses.append('instr(l.text,?)>0')
        args.append(query)
    if not spoilers:
        clauses.append("EXISTS(SELECT 1 FROM stories kr WHERE kr.lang='ko_KR' AND kr.path=s.path)")
    if target:
        names = aliases(target, lang)
        # Review targets may be entered in either supported language.
        review_names = sorted(set(names + aliases(target, 'ko_KR') + aliases(target, 'zh_CN') + [target]))
        placeholders = ','.join('?' for _ in review_names)
        clauses.append('(' + ' OR '.join('instr(l.text,?)>0' for _ in names) + f' OR EXISTS(SELECT 1 FROM reviews r WHERE r.line=l.id AND r.target IN ({placeholders}) AND r.kind!="rejected"))')
        args += names + review_names
        clauses.append(f'NOT EXISTS(SELECT 1 FROM reviews r WHERE r.line=l.id AND r.target IN ({placeholders}) AND r.kind="rejected" AND r.hash=l.hash)')
        args += review_names
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
        item['context'] = [dict(r) for r in db.execute('SELECT speaker,text,branch,ordinal FROM (SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal<? ORDER BY ordinal DESC LIMIT 3) UNION ALL SELECT speaker,text,branch,ordinal FROM (SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal>=? ORDER BY ordinal LIMIT 4) ORDER BY ordinal', (row['story'], row['ordinal'], row['story'], row['ordinal']))]
        item['parallel'] = [dict(r) for r in db.execute('SELECT l.speaker,l.text,s.lang FROM lines l JOIN stories s ON s.id=l.story WHERE s.path=? AND l.ordinal=? AND s.lang!=?', (row['path'], row['ordinal'], lang))]
        results.append(item)
    return {'total': total, 'items': results}


def validate_review(db, payload):
    if not isinstance(payload, dict) or any(not isinstance(payload.get(k), str) for k in ('line','target','expression','kind','hash')):
        raise ValueError('검토 항목은 문자열이어야 합니다.')
    payload = {k: payload[k] for k in ('line','target','expression','kind','hash')}
    payload['target'] = payload['target'].strip()
    if any(len(payload[k]) > 2000 for k in payload):
        raise ValueError('검토 항목이 너무 깁니다.')
    if payload['kind'] in ('direct','reference') and not payload['expression'].strip():
        raise ValueError('직접 호칭과 지칭에는 원문 표현이 필요합니다.')
    story, separator, ordinal = payload['line'].rpartition(':')
    if not separator or not ordinal.isdecimal():
        raise ValueError('잘못된 대사 식별자입니다.')
    line = db.execute('SELECT * FROM lines WHERE story=? AND ordinal=? AND id=?', (story,int(ordinal),payload['line'])).fetchone()
    if not line or line['hash'] != payload['hash']:
        raise ValueError('원문이 변경되었습니다. 새로 검색한 뒤 검토하세요.')
    if payload['kind'] not in ('direct', 'reference', 'related', 'rejected'):
        raise ValueError('잘못된 분류')
    if not payload['target'] or (payload['expression'] and payload['expression'] not in line['text']):
        raise ValueError('대상과 원문에 존재하는 표현을 입력하세요.')
    return payload


def review(db, payload):
    with db:
        db.execute('BEGIN IMMEDIATE')
        payload = validate_review(db,payload)
        db.execute('INSERT INTO history(line,target,payload) VALUES(?,?,?)', (payload['line'],payload['target'],json.dumps(payload,ensure_ascii=False)))
        db.execute('INSERT OR REPLACE INTO reviews VALUES(?,?,?,?,?)', tuple(payload[k] for k in ('line','target','expression','kind','hash')))
