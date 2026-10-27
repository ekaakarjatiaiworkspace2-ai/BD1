"""Small psycopg adapter for V5 SQL statements. PostgreSQL is used when DATABASE_URL is set."""
import re
from contextlib import contextmanager

class Result:
    def __init__(self, cursor, lastrowid=None):
        self.cursor=cursor
        self.lastrowid=lastrowid
    def fetchone(self):return self.cursor.fetchone()
    def fetchall(self):return self.cursor.fetchall()
    def __iter__(self):return iter(self.cursor)

class PgConn:
    def __init__(self,conn):self.conn=conn
    def execute(self,query,params=()):
        statement=query.strip()
        if statement.upper().startswith("PRAGMA "):
            return Result(self.conn.cursor())
        statement=statement.replace('?','%s')
        if re.match(r'^INSERT OR REPLACE INTO read_receipts VALUES',statement,re.I):
            statement="INSERT INTO read_receipts(meeting_id,username,read_at) VALUES(%s,%s,%s) ON CONFLICT(meeting_id,username) DO UPDATE SET read_at=EXCLUDED.read_at"
        get_id=bool(re.match(r'^INSERT INTO messages\b',statement,re.I))
        if get_id:statement+=" RETURNING id"
        c=self.conn.cursor();c.execute(statement,params)
        lastrowid=c.fetchone()['id'] if get_id else None
        return Result(c,lastrowid)
    def executescript(self,sql):
        sql=sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT","BIGSERIAL PRIMARY KEY")
        for statement in sql.split(';'):
            if statement.strip():self.execute(statement)
    def commit(self):self.conn.commit()
    def rollback(self):self.conn.rollback()
    def close(self):self.conn.close()

@contextmanager
def pg_db(url):
    import psycopg
    from psycopg.rows import dict_row
    conn=psycopg.connect(url,row_factory=dict_row,connect_timeout=10)
    wrapper=PgConn(conn)
    try:
        yield wrapper
        wrapper.commit()
    except Exception:
        wrapper.rollback()
        raise
    finally:wrapper.close()
