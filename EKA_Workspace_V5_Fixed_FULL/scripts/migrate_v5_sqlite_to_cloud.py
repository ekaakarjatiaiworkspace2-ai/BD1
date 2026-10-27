# Run once after backing up V5 data and new Postgres database.
import os,sys,json,sqlite3,argparse,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser()
parser.add_argument('--source',required=True,help='V5 data directory, containing project.sqlite3 and uploads')
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
data_dir=Path(args.source).resolve()
dbfile=data_dir/'project.sqlite3'
if not dbfile.exists():raise SystemExit('Database tidak ditemukan: '+str(dbfile))
old=sqlite3.connect(dbfile);old.row_factory=sqlite3.Row
tables=['accounts','records','files','messages','audit','read_receipts']
counts={table:old.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in tables}
print('RINGKASAN SUMBER:',counts)
if not args.apply:
 print('DRY RUN: Tidak ada data diubah. Gunakan --apply setelah membuat backup.')
 raise SystemExit(0)
if os.getenv('EKA_IMPORT_CONFIRM')!='I_HAVE_A_BACKUP':
 raise SystemExit('Set EKA_IMPORT_CONFIRM=I_HAVE_A_BACKUP setelah melakukan backup.')
if not (os.getenv('DATABASE_URL') and os.getenv('S3_BUCKET')):
 raise SystemExit('DATABASE_URL dan S3_BUCKET wajib tersedia.')
from cloud_database import pg_db
from cloud_storage import FileStore
store=FileStore(data_dir/'_unused')
with pg_db(os.environ['DATABASE_URL']) as c:
 c.execute('CREATE TABLE IF NOT EXISTS cloud_import_log(name TEXT PRIMARY KEY,imported_at TEXT NOT NULL)')
 if c.execute("SELECT 1 FROM cloud_import_log WHERE name='v5'").fetchone():
  raise SystemExit('Migrasi V5 pernah dijalankan pada database ini.')
 if c.execute('SELECT COUNT(*) AS n FROM files').fetchone()['n'] or c.execute('SELECT COUNT(*) AS n FROM messages').fetchone()['n']:
  raise SystemExit('Target telah digunakan. Migrasi dibatalkan agar data lama tidak tertimpa.')
 for r in old.execute('SELECT username,full_name,role,password_hash FROM accounts'):
  c.execute('INSERT INTO accounts VALUES(?,?,?,?) ON CONFLICT(username) DO UPDATE SET full_name=EXCLUDED.full_name,role=EXCLUDED.role,password_hash=EXCLUDED.password_hash',tuple(r))
 for r in old.execute('SELECT kind,id,body,updated_at FROM records'):
  c.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=EXCLUDED.body,updated_at=EXCLUDED.updated_at',tuple(r))
 for r in old.execute('SELECT channel,username,body,created_at FROM messages ORDER BY id'):
  c.execute('INSERT INTO messages(channel,username,body,created_at) VALUES(?,?,?,?)',(r['channel'],r['username'],r['body'],r['created_at']))
 for r in old.execute('SELECT ts,username,action,kind,item_id,detail FROM audit ORDER BY id'):
  c.execute('INSERT INTO audit(ts,username,action,kind,item_id,detail) VALUES(?,?,?,?,?,?)',tuple(r))
 for r in old.execute('SELECT meeting_id,username,read_at FROM read_receipts'):
  c.execute('INSERT INTO read_receipts VALUES(?,?,?) ON CONFLICT(meeting_id,username) DO UPDATE SET read_at=EXCLUDED.read_at',tuple(r))
 for r in old.execute('SELECT * FROM files'):
  f=data_dir/'uploads'/r['blob_name']
  if not f.is_file():raise SystemExit('Dokumen sumber tidak ditemukan: '+r['name'])
  key=f"eka/migrasi-v5/{r['id']}{Path(r['name']).suffix.lower()}"
  with f.open('rb') as stream:store.put(stream,key)
  c.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING',
    (r['id'],r['kind'],r['ref_id'],r['name'],key,r['uploaded_by'],r['uploaded_at'],r['size']))
  if r['kind']=='data':
   row=old.execute("SELECT body FROM records WHERE kind='data' AND id=?",(r['ref_id'],)).fetchone()
   category=json.loads(row['body']).get('category','Legacy') if row else 'Legacy'
   match=re.search(r'(?<!\d)(20\d{2})(?!\d)',r['name'])
   year=int(match.group(1)) if match else int(r['uploaded_at'][:4])
   with f.open('rb') as input_file:sha=hashlib.file_digest(input_file,'sha256').hexdigest()
   c.execute('INSERT INTO document_index VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(file_id) DO NOTHING',
     (r['id'],r['ref_id'],'EKA',year,'tahunan',category,r['name'],1,sha,key,store.mode,
     'Migrasi V5: tahun dan sumber harap diverifikasi',r['uploaded_at']))
 c.execute('INSERT INTO cloud_import_log VALUES(?,?)',('v5',datetime.now(timezone.utc).isoformat()))
print('Selesai. Periksa hasil dan password akun sebelum membuka akses publik.')
