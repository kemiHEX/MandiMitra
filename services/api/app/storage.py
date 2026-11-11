import json
import sqlite3
import time
from pathlib import Path

class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, data TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS rate_limits (bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS decisions_session ON decisions(session_id);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute('PRAGMA journal_mode=WAL')
        return db

    def get(self, sid):
        with self.connect() as db:
            row = db.execute('SELECT data FROM sessions WHERE id=? AND updated>?', (sid, time.time()-30*86400)).fetchone()
        return json.loads(row[0]) if row else {'state': {}, 'messages': [], 'costs': {}, 'comparison': None, 'observations': [], 'notes': []}

    def put(self, sid, data):
        with self.connect() as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,updated=excluded.updated', (sid, json.dumps(data, ensure_ascii=False), time.time()))
            db.execute('DELETE FROM sessions WHERE updated<?', (time.time()-30*86400,))
            db.execute('DELETE FROM decisions WHERE created<?', (time.time()-90*86400,))

    def save_decision(self, sid, decision):
        with self.connect() as db:
            db.execute('INSERT INTO decisions VALUES (?,?,?,?)', (decision['id'], sid, json.dumps(decision, ensure_ascii=False), time.time()))
            db.execute('DELETE FROM decisions WHERE session_id=? AND id NOT IN (SELECT id FROM decisions WHERE session_id=? ORDER BY created DESC LIMIT 50)', (sid,sid))

    def decisions(self, sid):
        with self.connect() as db:
            rows = db.execute('SELECT data FROM decisions WHERE session_id=? AND created>? ORDER BY created DESC LIMIT 50', (sid,time.time()-90*86400)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, sid, everything=False):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE id=?', (sid,))
            if everything: db.execute('DELETE FROM decisions WHERE session_id=?', (sid,))

    def delete_decision(self, sid, did):
        with self.connect() as db: db.execute('DELETE FROM decisions WHERE id=? AND session_id=?', (did,sid))

    def allowed(self, key, limit=30, seconds=60):
        now = time.time()
        bucket = f'{key}:{int(now//seconds)}'
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM rate_limits WHERE expires<?', (now,))
            db.execute('INSERT INTO rate_limits VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1', (bucket,now+seconds))
            count = db.execute('SELECT count FROM rate_limits WHERE bucket=?', (bucket,)).fetchone()[0]
        return count <= limit
