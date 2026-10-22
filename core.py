"""Raw script ingestion and conservative, evidence-first retrieval. Python 3.11+."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

LANGUAGES = {'ko_KR':'kr', 'zh_CN':'cn', 'ja_JP':'jp', 'en_US':'en'}

def aliases(value, lang):
    path = Path(__file__).parent / 'characters.json'
    result=[]
    for character in json.loads(path.read_text(encoding='utf-8')):
        all_names=[character['id']]+character.get('aliases',[])+[n for names in character['names'].values() for n in names]
        if value.casefold() in [n.casefold() for n in all_names]:
            result.extend(character['names'].get(lang,[]))
    return list(dict.fromkeys(result)) or [value]




def connect(path, ephemeral=False):
    db = sqlite3.connect(path)
    if ephemeral:
        db.execute("PRAGMA journal_mode=MEMORY")
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS stories(id TEXT PRIMARY KEY, lang TEXT, path TEXT, revision TEXT, source TEXT, raw TEXT);
    CREATE TABLE IF NOT EXISTS snapshots(story TEXT, revision TEXT, raw TEXT, PRIMARY KEY(story,revision));
    CREATE TABLE IF NOT EXISTS lines(id TEXT PRIMARY KEY, story TEXT, ordinal INTEGER, speaker TEXT, text TEXT, branch TEXT, hash TEXT);
    CREATE INDEX IF NOT EXISTS story_path_idx ON stories(path,lang);
    CREATE INDEX IF NOT EXISTS speaker_idx ON lines(speaker);
    CREATE INDEX IF NOT EXISTS story_idx ON lines(story,ordinal);
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

    for lang, folder in LANGUAGES.items():
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


def search(db, speaker='', target='', query='', lang='ko_KR', spoilers=False, offset=0, story=''):
    if lang not in LANGUAGES:
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
        clauses.append('(' + ' OR '.join('instr(l.text,?)>0' for _ in names) + ')')
        args += names
    where = ' AND '.join(clauses)
    facets = [dict(row) for row in db.execute(f'SELECT s.path,count(*) AS count FROM lines l JOIN stories s ON s.id=l.story WHERE {where} GROUP BY s.path ORDER BY s.path',args)]
    if story:
        where += ' AND s.path=?'
        args.append(story)
    total = db.execute(f'SELECT count(*) FROM lines l JOIN stories s ON s.id=l.story WHERE {where}', args).fetchone()[0]
    rows = db.execute(f'SELECT l.*,s.lang,s.path,s.revision,s.source FROM lines l JOIN stories s ON s.id=l.story WHERE {where} ORDER BY s.path,l.ordinal LIMIT 50 OFFSET ?', args+[offset]).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        # Physical neighbours are explicitly not inferred conversation partners.
        item['context'] = [dict(r) for r in db.execute('SELECT speaker,text,branch,ordinal FROM (SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal<? ORDER BY ordinal DESC LIMIT 3) UNION ALL SELECT speaker,text,branch,ordinal FROM (SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal>=? ORDER BY ordinal LIMIT 4) ORDER BY ordinal', (row['story'], row['ordinal'], row['story'], row['ordinal']))]
        item['parallel'] = [dict(r) for r in db.execute('SELECT l.speaker,l.text,s.lang FROM lines l JOIN stories s ON s.id=l.story WHERE s.path=? AND l.ordinal=? AND s.lang!=?', (row['path'], row['ordinal'], lang))]
        results.append(item)
    return {'total': total, 'items': results, 'stories':facets}


def context_window(db, story, ordinal, radius=15):
    row = db.execute('SELECT * FROM stories WHERE id=?', (story,)).fetchone()
    if not row:
        raise ValueError('Story not found')
    radius = max(3, min(100, radius))
    before = db.execute('SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal<? ORDER BY ordinal DESC LIMIT ?', (story,ordinal,radius)).fetchall()
    after = db.execute('SELECT speaker,text,branch,ordinal FROM lines WHERE story=? AND ordinal>=? ORDER BY ordinal LIMIT ?', (story,ordinal,radius+1)).fetchall()
    rows = list(reversed(before)) + list(after)
    return {'items':[dict(r) for r in rows], 'has_more':len(before)==radius or len(after)==radius+1}
