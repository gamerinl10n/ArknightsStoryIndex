"""Build an immutable search-only snapshot. Raw archives never enter the Function."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def export_snapshot(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Source and output must differ')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary = output.with_suffix('.sqlite.tmp')
    temporary.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(temporary)) as dst:
            # Retain exact schema/indices used by core.search, but not raw archives.
            dst.executescript('''
            CREATE TABLE stories(id TEXT PRIMARY KEY,lang TEXT,path TEXT,revision TEXT,source TEXT);
            CREATE TABLE lines(id TEXT PRIMARY KEY,story TEXT,ordinal INTEGER,speaker TEXT,text TEXT,branch TEXT,hash TEXT);
            CREATE TABLE reviews(line TEXT,target TEXT,expression TEXT,kind TEXT,hash TEXT,PRIMARY KEY(line,target));
            CREATE TABLE import_status(id INTEGER PRIMARY KEY,payload TEXT);
            ''')
            dst.executemany('INSERT INTO stories VALUES(?,?,?,?,?)',src.execute('SELECT id,lang,path,revision,source FROM stories'))
            dst.executemany('INSERT INTO lines VALUES(?,?,?,?,?,?,?)',src.execute('SELECT * FROM lines'))
            dst.executemany('INSERT INTO import_status VALUES(?,?)',src.execute('SELECT * FROM import_status'))
            dst.executescript('''
            CREATE INDEX story_path_idx ON stories(path,lang);
            CREATE INDEX speaker_idx ON lines(speaker);
            CREATE INDEX story_idx ON lines(story,ordinal);
            ''')
            dst.commit()
            count=dst.execute('SELECT count(*) FROM lines').fetchone()[0]
            if not count or dst.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise ValueError('Invalid search snapshot')
        size=temporary.stat().st_size
        if size > 400*1024*1024:
            raise ValueError('Search snapshot exceeds 400 MiB budget; split the corpus before deployment')
        temporary.replace(output)
        print(f'Search snapshot: {count:,} lines, {size/1024**2:.1f} MiB')
    finally:
        temporary.unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-db',help='Reuse an already imported DB for local verification')
    p.add_argument('--output',default='generated/search.sqlite')
    a=p.parse_args()
    source=a.source_db
    if not source:
        source='data/build.sqlite'
        subprocess.run([sys.executable,'sync.py','--database',source,'--ref',os.environ.get('ASI_SOURCE_REF','master')],check=True)
    export_snapshot(source,a.output)

if __name__=='__main__':
    main()
