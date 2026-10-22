"""Durable review overlay. Credentials stay in server environment variables."""
import json
import os
import psycopg

SCHEMA = '''
CREATE TABLE IF NOT EXISTS asi_reviews (
  line TEXT NOT NULL, target TEXT NOT NULL, expression TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('direct','reference','related','rejected')),
  hash TEXT NOT NULL, PRIMARY KEY(line,target)
);
CREATE TABLE IF NOT EXISTS asi_review_history (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  line TEXT NOT NULL, target TEXT NOT NULL, payload JSONB NOT NULL,
  created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

class PostgresReviews:
    def __init__(self,url):
        self.url=url

    def load(self):
        with psycopg.connect(self.url,connect_timeout=8) as db:
            return db.execute('SELECT line,target,expression,kind,hash FROM asi_reviews').fetchall()

    def save(self,payload):
        with psycopg.connect(self.url,connect_timeout=8) as db:
            db.execute('INSERT INTO asi_review_history(line,target,payload) VALUES(%s,%s,%s)',(payload['line'],payload['target'],json.dumps(payload,ensure_ascii=False)))
            db.execute('INSERT INTO asi_reviews VALUES(%s,%s,%s,%s,%s) ON CONFLICT(line,target) DO UPDATE SET expression=EXCLUDED.expression,kind=EXCLUDED.kind,hash=EXCLUDED.hash',tuple(payload[k] for k in ('line','target','expression','kind','hash')))

if __name__=='__main__':
    # Explicit setup; requests never run schema changes.
    with psycopg.connect(os.environ['ASI_REVIEW_DATABASE_URL'],connect_timeout=8) as db:
        db.execute(SCHEMA)
    print('Review schema ready')
