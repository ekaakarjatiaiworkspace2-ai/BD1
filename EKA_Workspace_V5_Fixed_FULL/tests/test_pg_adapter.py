from cloud_database import PgConn

class FakeCursor:
    def __init__(self): self.sql='';self.params=()
    def execute(self,sql,params=()):self.sql=sql;self.params=params
    def fetchone(self):return {'id':42}

class FakeDB:
    def __init__(self):self.cursor_obj=FakeCursor()
    def cursor(self):return self.cursor_obj

def test_query_translation_and_lastrowid():
    fake=FakeDB()
    res=PgConn(fake).execute('INSERT INTO messages(channel,username,body,created_at) VALUES(?,?,?,?)',('umum','angga','halo','2026-10-27'))
    assert 'RETURNING id' in fake.cursor_obj.sql
    assert fake.cursor_obj.sql.count('%s')==4
    assert res.lastrowid==42
    PgConn(fake).execute('INSERT OR REPLACE INTO read_receipts VALUES(?,?,?)',('MTG-1','ahmad','2026-10-27'))
    assert 'ON CONFLICT(meeting_id,username)' in fake.cursor_obj.sql
