"""EKA Workspace V6: arsip tahunan, unggah batch, dan dukungan cloud.
Jangan deploy publik tanpa HTTPS, backup, dan security review.
"""
import os,json,sqlite3,secrets,hashlib,hmac,uuid,mimetypes,re,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI,Request,HTTPException,UploadFile,File,Form,Response
from fastapi.responses import FileResponse,JSONResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from seed import records
from cloud_database import pg_db
from cloud_storage import FileStore
from document_coverage import validate_requirement,save_requirement,scope_coverage,coverage_history
from document_links import google_drive_reference

ROOT=Path(__file__).resolve().parent
DATA=Path(os.getenv('EKA_DATA_DIR',str(ROOT/'data'))).resolve()
DATA.mkdir(parents=True,exist_ok=True)
UPLOADS=DATA/'uploads';UPLOADS.mkdir(exist_ok=True)
DB=DATA/'project.sqlite3'
DATABASE_URL=os.getenv('DATABASE_URL','').strip()
CLOUD=os.getenv('EKA_DEPLOY_MODE','local')=='cloud'
if CLOUD:
    required=['DATABASE_URL','S3_BUCKET','S3_ACCESS_KEY_ID','S3_SECRET_ACCESS_KEY','EKA_SECURE_COOKIE']
    missing=[x for x in required if not os.getenv(x)]
    if missing:raise RuntimeError('Mode cloud membutuhkan variabel: '+', '.join(missing))
    if os.environ['EKA_SECURE_COOKIE']!='1':raise RuntimeError('Mode cloud mewajibkan HTTPS cookies')
STORE=FileStore(UPLOADS)
NAMES={'ahmad':('Ahmad Fernanda','lead'),'donny':('Donny Setya','science'),'angga':('Angga Trisna','finance'),'management':('Management','manager')}
COLLECTIONS={'tasks','data','tools','meetings','decisions'}
MAX_UPLOAD=25*1024*1024
MAX_BATCH=20
ALLOWED_EXT={'.pdf','.xlsx','.xls','.csv','.docx','.png','.jpg','.jpeg','.webp','.txt'}
now=lambda:datetime.now(timezone.utc).isoformat(timespec='seconds')

@contextmanager
def db():
    if DATABASE_URL:
        with pg_db(DATABASE_URL) as conn:yield conn
        return
    c=sqlite3.connect(DB,timeout=15)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try:yield c;c.commit()
    except Exception:c.rollback();raise
    finally:c.close()

def hashpw(pwd,salt=None):
    salt=salt or secrets.token_hex(16)
    dk=hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(salt),260000)
    return salt+':'+dk.hex()
def verifypw(password,stored):
    try:salt,digest=stored.split(':',1);return hmac.compare_digest(hashpw(password,salt).split(':')[1],digest)
    except Exception:return False

def audit(c,user,action,kind,item,detail=None):
    c.execute('INSERT INTO audit(ts,username,action,kind,item_id,detail) VALUES(?,?,?,?,?,?)',(now(),user,action,kind,item,json.dumps(detail or {},ensure_ascii=False)))

def audit_coverage_transition(c,username,before,after):
    if before['done']==after['done']:return
    audit(c,username,'document_collection_done' if after['done'] else 'document_collection_reopened','data',after['data_ref'],
        {'year':after['fiscal_year'],'unit':after['business_unit'],'mode':after['mode'],
         'required_periods':after['required_periods'],'available_periods':after['available_periods']})

def insert(c,kind,item,user='system'):
    rid=item['id'];c.execute('INSERT INTO records(kind,id,body,updated_at) VALUES(?,?,?,?)',(kind,rid,json.dumps(item,ensure_ascii=False),now()))
    audit(c,user,'created',kind,rid)
    return item

def find(c,kind,rid):
    r=c.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,rid)).fetchone()
    if not r:raise HTTPException(404,'Data tidak ditemukan')
    return json.loads(r['body'])

def allrows(c,kind):
    return [json.loads(r['body']) for r in c.execute('SELECT body FROM records WHERE kind=? ORDER BY id',(kind,))]

def save(c,kind,item,user,old=None):
    c.execute('UPDATE records SET body=?,updated_at=? WHERE kind=? AND id=?',(json.dumps(item,ensure_ascii=False),now(),kind,item['id']))
    diff={k:[(old or {}).get(k),v] for k,v in item.items() if old is not None and old.get(k)!=v}
    audit(c,user,'updated',kind,item['id'],diff)

def setup():
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS accounts(username TEXT PRIMARY KEY, full_name TEXT, role TEXT, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,username TEXT,csrf TEXT,expires TEXT);
        CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,body TEXT,updated_at TEXT,PRIMARY KEY(kind,id));
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,ts TEXT,username TEXT,action TEXT,kind TEXT,item_id TEXT,detail TEXT);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,channel TEXT,username TEXT,body TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,kind TEXT,ref_id TEXT,name TEXT,blob_name TEXT,uploaded_by TEXT,uploaded_at TEXT,size INTEGER);
        CREATE TABLE IF NOT EXISTS read_receipts(meeting_id TEXT,username TEXT,read_at TEXT,PRIMARY KEY(meeting_id,username));
        CREATE TABLE IF NOT EXISTS document_index(
          file_id TEXT PRIMARY KEY,
          data_ref TEXT NOT NULL,
          business_unit TEXT NOT NULL,
          fiscal_year INTEGER NOT NULL,
          reporting_period TEXT NOT NULL,
          category TEXT NOT NULL,
          original_name TEXT NOT NULL,
          version_num INTEGER NOT NULL,
          sha256 TEXT NOT NULL,
          storage_key TEXT NOT NULL,
          storage_backend TEXT NOT NULL,
          remarks TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(file_id) REFERENCES files(id)
        );
        CREATE INDEX IF NOT EXISTS idx_doc_year ON document_index(fiscal_year,business_unit,category);
        CREATE INDEX IF NOT EXISTS idx_doc_ref ON document_index(data_ref,fiscal_year);
        CREATE TABLE IF NOT EXISTS document_requirements(
          data_ref TEXT NOT NULL,
          business_unit TEXT NOT NULL,
          fiscal_year INTEGER NOT NULL,
          mode TEXT NOT NULL,
          required_periods TEXT NOT NULL,
          note TEXT NOT NULL,
          updated_by TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY(data_ref,business_unit,fiscal_year)
        );''')
        if not c.execute('SELECT 1 FROM accounts LIMIT 1').fetchone():
            creds=[]
            for username,(full,role) in NAMES.items():
                if CLOUD:
                    pw=os.getenv('EKA_PASSWORD_'+username.upper(),'')
                    if len(pw)<12:raise RuntimeError('Set EKA_PASSWORD_'+username.upper()+' minimal 12 karakter')
                else:pw=secrets.token_urlsafe(18)
                c.execute('INSERT INTO accounts VALUES(?,?,?,?)',(username,full,role,hashpw(pw)))
                if not CLOUD:creds.append(f'{username}: {pw}')
            if not CLOUD:
                fp=DATA/'AKUN_AWAL.txt';fp.write_text('\n'.join(creds)+'\n',encoding='utf-8')
                try:fp.chmod(0o600)
                except Exception:pass
        for kind,rs in records().items():
            if not c.execute('SELECT 1 FROM records WHERE kind=? LIMIT 1',(kind,)).fetchone():
                for row in rs:insert(c,kind,row)
setup()
app=FastAPI(title='EKA Workspace Cloud',version='6.3.0',docs_url=None,redoc_url=None)
@app.middleware('http')
async def hardened_headers(request:Request, call_next):
    resp=await call_next(request)
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    resp.headers['X-Frame-Options']='DENY'
    if CLOUD:resp.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    if request.url.path.startswith('/api/'):resp.headers['Cache-Control']='no-store'
    return resp
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

class Credentials(BaseModel):
    username:str
    password:str
class ChangePassword(BaseModel):
    old:str
    new:str
class ChatInput(BaseModel):
    channel:str
    body:str=Field(min_length=1,max_length=4000)

class DocumentRequirement(BaseModel):
    data_ref:str
    business_unit:str
    fiscal_year:int
    mode:str='fleksibel'
    required_periods:list[str]=Field(default_factory=list)
    note:str=''

def who(request:Request,mutation=False):
    token=request.cookies.get('eka_session')
    if not token:raise HTTPException(401,'Silakan login')
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with db() as c:
        row=c.execute('''SELECT a.username,a.full_name,a.role,s.csrf,s.expires FROM sessions s
            JOIN accounts a ON a.username=s.username WHERE s.token_hash=?''',(token_hash,)).fetchone()
    if not row or row['expires']<now():raise HTTPException(401,'Sesi telah habis. Silakan login ulang')
    if mutation and not hmac.compare_digest(request.headers.get('x-csrf-token',''),row['csrf']):raise HTTPException(403,'Sesi tidak sesuai. Silakan masuk kembali')
    return dict(row)

def safe_unit(value):
    v=(value or '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9_-]{2,32}',v):raise HTTPException(400,'Kode unit bisnis hanya huruf, angka, - atau _')
    return v

def check_year(y):
    if y<2000 or y>datetime.now().year+3:raise HTTPException(400,'Tahun laporan tidak sesuai')
    return y

def safe_filename(upload):
    name=Path((upload.filename or '').replace(chr(92),'/')).name.strip()
    if not name or Path(name).suffix.lower() not in ALLOWED_EXT:raise HTTPException(400,'Hanya PDF, Excel, Word, CSV dan gambar yang diperbolehkan')
    if len(name)>160:raise HTTPException(400,'Nama berkas maksimal 160 karakter')
    return name

async def staged_file(upload):
    name=safe_filename(upload)
    temp=tempfile.SpooledTemporaryFile(max_size=4*1024*1024,mode='w+b')
    digest=hashlib.sha256();size=0
    while True:
        b=await upload.read(1024*1024)
        if not b:break
        size+=len(b)
        if size>MAX_UPLOAD:
            temp.close()
            raise HTTPException(413,'Satu berkas maksimal 25 MB')
        digest.update(b);temp.write(b)
    if not size:temp.close();raise HTTPException(400,'Berkas kosong tidak diizinkan')
    temp.seek(0)
    sig=temp.read(8);temp.seek(0)
    ext=Path(name).suffix.lower()
    if ext=='.pdf' and not sig.startswith(b'%PDF-'):
        temp.close();raise HTTPException(400,'Isi file bukan PDF valid')
    if ext in {'.xlsx','.docx'} and not sig.startswith(b'PK'):
        temp.close();raise HTTPException(400,'Format Office tidak cocok dengan ekstensi')
    return name,temp,size,digest.hexdigest()

def channels(role):
    return {'lead':['umum','data','tools','riset','meeting'], 'science':['umum','tools','meeting'],
            'finance':['umum','data','meeting'],'manager':['meeting']}[role]

def cansee(user,kind,item):
    role=user['role'];name=user['username']
    if role=='lead':return True
    if kind=='tasks':return item.get('owner')==name
    if kind=='data':return role=='finance' or role=='science' and (item.get('status')=='siap' or item.get('category') in ('Laporan Keuangan','Kas dan Modal Kerja','Pembiayaan dan Agunan','Konstruksi Hotel','Sumber dan Penggunaan Dana','Riset Pasar','Operasional dan Pendapatan','Risiko dan Skenario','Sinergi dan Ekspansi','Target Manajemen dan Governance'))
    if kind=='tools':return role=='science' and item.get('owner')==name
    if kind=='meetings':return item.get('status') in ('dibagikan','selesai')
    if kind=='decisions':return role=='manager'
    return False

def progress(tasks):
    subs={}
    for t in tasks:
        if t.get('level')=='subtask':subs.setdefault(t['parent'],[]).append(t)
    out=[]
    for m in (t for t in tasks if t.get('level')=='macro'):
        arr=subs.get(m['id'],[]);wt=sum(float(x.get('weight') or 1) for x in arr)
        accepted=sum(float(x.get('weight') or 1) for x in arr if x['status']=='selesai' and not x.get('needs_recheck'))
        p=round(100*accepted/wt) if wt else 0
        st=('selesai' if p==100 and arr else 'tertahan' if any(x['status']=='tertahan' for x in arr)
            else 'menunggu_review' if any(x['status']=='menunggu_review' for x in arr)
            else 'dikerjakan' if any(x['status'] not in ('belum_mulai','dibatalkan') for x in arr) else 'belum_mulai')
        out.append({**m,'percent':p,'done':sum(x['status']=='selesai' and not x.get('needs_recheck') for x in arr),'total':len(arr),'status':st})
    return out

def summary(c):
    ts=allrows(c,'tasks');ms=progress(ts);ds=allrows(c,'data');tools=allrows(c,'tools')
    fns=[]
    for fun,title in [('BD','Pengembangan Bisnis'),('RND','Riset & Pengembangan'),('FIN','Keuangan'),('DS','Data Science')]:
        arr=[x for x in ms if x['function']==fun]
        sub=[x for x in ts if x.get('level')=='subtask' and x['function']==fun]
        done=sum(x.get('weight',1) for x in sub if x['status']=='selesai' and not x.get('needs_recheck'))
        total=sum(x.get('weight',1) for x in sub)
        fns.append({'function':fun,'name':title,'macros':len(arr),'done':sum(x['status']=='selesai' for x in arr),'percent':round(100*done/total) if total else 0})
    op=[x for x in ms if x['function']!='MGMT']
    subs=[x for x in ts if x.get('level')=='subtask' and x['function']!='MGMT']
    return {'overall':round(100*sum(x['status']=='selesai' and not x.get('needs_recheck') for x in subs)/len(subs)) if subs else 0,
     'done_macros':sum(x['status']=='selesai' for x in op),'total_macros':len(op),
     'data_ready':sum(x['status']=='siap' for x in ds),'data_total':len(ds),
     'tools_ready':sum(x['status']=='siap_dipakai' for x in tools),'tools_total':len(tools),
     'functions':fns,
     'macros':[{k:m.get(k) for k in ('id','title','function','owner','start','due','baseline_due','status','percent','total','done')} for m in ms],
     'attention':[{k:m.get(k) for k in ('id','title','owner','function','status')} for m in ms if m['status'] in ('tertahan','menunggu_review')],
     'snapshot_at':now()}

def exposed_data(role,d):
    if role=='science' and d['status']!='siap':
        return {k:v for k,v in d.items() if k not in ('source_link','received_at','note','validation')}
    return d

@app.get('/')
def index():return FileResponse(ROOT/'static'/'index.html',headers={'Cache-Control':'no-cache'})
@app.get('/manifest.webmanifest')
def manifest():return FileResponse(ROOT/'static'/'manifest.webmanifest',media_type='application/manifest+json')
@app.get('/sw.js')
def sw():return FileResponse(ROOT/'static'/'sw.js',media_type='text/javascript',headers={'Service-Worker-Allowed':'/','Cache-Control':'no-cache'})
@app.get('/api/health')
def health():return {'status':'ok','version':'6.3.0','db':'postgres' if DATABASE_URL else 'sqlite','storage':STORE.mode,'deploy':'cloud' if CLOUD else 'local'}

@app.post('/api/login')
def login(body:Credentials,response:Response):
    with db() as c:
        row=c.execute('SELECT * FROM accounts WHERE username=?',(body.username.lower().strip(),)).fetchone()
        if not row or not verifypw(body.password,row['password_hash']):raise HTTPException(401,'Nama pengguna atau kata sandi salah')
        token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(24)
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['username'],csrf,(datetime.now(timezone.utc)+timedelta(hours=10)).isoformat()))
        audit(c,row['username'],'login','sessions','-')
    response.set_cookie('eka_session',token,httponly=True,samesite='lax',secure=os.getenv('EKA_SECURE_COOKIE','0')=='1',max_age=36000,path='/')
    return {'name':row['full_name'],'username':row['username'],'role':row['role'],'csrf':csrf}

@app.post('/api/logout')
def logout(request:Request,response:Response):
    u=who(request,True);token=request.cookies.get('eka_session','')
    with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),));audit(c,u['username'],'logout','sessions','-')
    response.delete_cookie('eka_session');return {'ok':True}

@app.post('/api/change-password')
def change_password(request:Request,body:ChangePassword):
    u=who(request,True)
    if len(body.new)<12:raise HTTPException(400,'Kata sandi baru minimal 12 karakter')
    with db() as c:
        r=c.execute('SELECT password_hash FROM accounts WHERE username=?',(u['username'],)).fetchone()
        if not verifypw(body.old,r['password_hash']):raise HTTPException(400,'Kata sandi lama tidak cocok')
        c.execute('UPDATE accounts SET password_hash=? WHERE username=?',(hashpw(body.new),u['username']))
        audit(c,u['username'],'password_changed','accounts',u['username'])
    return {'ok':True}

@app.get('/api/bootstrap')
def bootstrap(request:Request):
    u=who(request)
    with db() as c:
        ts=allrows(c,'tasks');dat=allrows(c,'data');tl=allrows(c,'tools');meets=allrows(c,'meetings');dec=allrows(c,'decisions')
        tasks=[x for x in ts if cansee(u,'tasks',x)]
        data=[exposed_data(u['role'],x) for x in dat if cansee(u,'data',x)]
        tools=[x for x in tl if cansee(u,'tools',x)]
        meetings=[x for x in meets if cansee(u,'meetings',x)]
        decisions=[x for x in dec if cansee(u,'decisions',x)]
        files=[]
        for f in c.execute('SELECT id,kind,ref_id,name,uploaded_by,uploaded_at,size FROM files ORDER BY uploaded_at DESC LIMIT 500'):
            obj=next((v for v in {'tasks':ts,'data':dat,'tools':tl,'meetings':meets,'decisions':dec}.get(f['kind'],[]) if v['id']==f['ref_id']),None)
            if obj and cansee(u,f['kind'],obj) and (f['kind']!='data' or u['role']!='science' or obj['status']=='siap'):files.append(dict(f))
        msgs=[dict(m) for m in c.execute('SELECT id,channel,username,body,created_at FROM messages ORDER BY id DESC LIMIT 300') if m['channel'] in channels(u['role'])]
        sm=summary(c) if u['role'] in ('lead','manager') else None
    return {'user':{'username':u['username'],'name':u['full_name'],'role':u['role'],'csrf':u['csrf']},'tasks':tasks,'data':data,'tools':tools,'meetings':meetings,'decisions':decisions,'files':files,'messages':msgs[::-1],'summary':sm,'roles':{x:{'name':v[0],'role':v[1]} for x,v in NAMES.items()}}

@app.patch('/api/records/{kind}/{rid}')
async def patch(kind:str,rid:str,request:Request):
    u=who(request,True)
    if kind not in COLLECTIONS:raise HTTPException(400,'Jenis tidak dikenali')
    change=await request.json()
    if not isinstance(change,dict):raise HTTPException(400,'Format harus objek')
    with db() as c:
        old=find(c,kind,rid)
        if kind=='tasks':
            if old['level']=='macro':
                if u['role']!='lead' or set(change)-{'start','due','schedule_reason','queue','purpose','deliverable'}:raise HTTPException(403,'Hanya Ahmad boleh mengatur tugas besar')
            else:
                if u['role']=='lead':
                    if old['function']=='MGMT' and change.get('status')=='selesai':raise HTTPException(403,'Keputusan manajemen adalah kewenangan Management')
                    if set(change)&{'level','parent','owner','function','baseline_due','id'}:raise HTTPException(403,'Struktur subtask tidak boleh diubah di sini')
                elif u['role']=='manager' and old['function']=='MGMT':
                    allowed={'status','completed_checks','actual_result','block_reason','queue'}
                    if set(change)-allowed:raise HTTPException(403,'Hanya boleh mengubah tugas review manajemen')
                elif u['username']==old['owner']:
                    allowed={'status','completed_checks','actual_result','block_reason','queue'}
                    if set(change)-allowed or change.get('status')=='selesai':raise HTTPException(403,'Anda tidak bisa menyetujui hasil sendiri')
                else:raise HTTPException(403,'Bukan tugas Anda')
                if 'completed_checks' in change:
                    if not isinstance(change['completed_checks'],list) or not set(change['completed_checks']).issubset(set(old.get('checklist',[]))):raise HTTPException(400,'Checklist tidak sesuai')
                ns=change.get('status',old.get('status'))
                if ns=='menunggu_review' and old.get('status')!='menunggu_review':
                    evidence=change.get('actual_result',old.get('actual_result',''))
                    file_count=c.execute("SELECT count(*) n FROM files WHERE kind='tasks' AND ref_id=?",(rid,)).fetchone()['n']
                    if not evidence and not file_count:raise HTTPException(400,'Isi hasil atau unggah bukti dahulu')
                if ns=='selesai' and old.get('status')!='selesai':
                    if not (u['role']=='lead' and old['function']!='MGMT' or u['role']=='manager' and old['function']=='MGMT'):raise HTTPException(403,'Hanya reviewer yang dapat menerima hasil')
                    if old.get('status')!='menunggu_review':raise HTTPException(400,'Hasil harus dikirim untuk review lebih dulu')
                    checks=old.get('completed_checks',[])
                    if not set(old.get('checklist',[])).issubset(set(checks)):raise HTTPException(400,'Checklist belum tuntas')
                    change['approved_by']=u['username'];change['approved_at']=now();change['needs_recheck']=False
            if 'start' in change or 'due' in change:
                if u['role']!='lead':raise HTTPException(403,'Tanggal hanya diubah Ahmad')
                start=change.get('start',old.get('start'));due=change.get('due',old.get('due'))
                try:
                    sd=datetime.strptime(start,'%Y-%m-%d');dd=datetime.strptime(due,'%Y-%m-%d')
                    if sd>dd:raise ValueError()
                except Exception:raise HTTPException(400,'Tanggal mulai harus lebih awal dari tenggat')
                if (start!=old.get('start') or due!=old.get('due')) and not str(change.get('schedule_reason','')).strip():raise HTTPException(400,'Tuliskan alasan perubahan tanggal')
        elif kind=='data':
            if u['role']=='lead':
                if change.get('status')=='siap':
                    validation=change.get('validation',old.get('validation'))
                    nfiles=c.execute("SELECT COUNT(*) n FROM files WHERE kind='data' AND ref_id=?",(rid,)).fetchone()['n']
                    source=change.get('source_link',old.get('source_link'))
                    if validation!='valid' or not (old.get('received_at') or change.get('received_at')) or not (source or nfiles):raise HTTPException(400,'Data harus diterima, memiliki bukti, dan diperiksa sebelum siap')
            elif u['role']=='finance' and old['owner']==u['username']:
                if set(change)-{'status','note','source_link','validation'} or change.get('status')=='siap':raise HTTPException(403,'Hanya reviewer boleh menyatakan data siap')
            else:raise HTTPException(403,'Tidak diizinkan')
            if change.get('status')=='diterima':change['received_at']=old.get('received_at') or now()
        elif kind=='tools':
            if u['role']=='science' and old['owner']==u['username']:
                if set(change)-{'status','test_result','link','version','deliverable','note'} or change.get('status')=='siap_dipakai':raise HTTPException(403,'Hanya Ahmad dapat menerima tools')
            elif u['role']=='lead':
                if change.get('status')=='siap_dipakai' and not (change.get('test_result',old.get('test_result')) and change.get('link',old.get('link'))):raise HTTPException(400,'Cantumkan hasil uji dan tautan alat')
            else:raise HTTPException(403,'Tidak diizinkan')
        elif kind=='meetings':
            if u['role']!='lead':raise HTTPException(403,'Hanya Ahmad mengatur meeting')
        elif kind=='decisions':
            if u['role'] not in ('lead','manager'):raise HTTPException(403,'Tidak diizinkan')
        result={**old,**change};save(c,kind,result,u['username'],old)
        if kind=='data' and old!=result:
            for t in allrows(c,'tasks'):
                if t.get('level')=='subtask' and t.get('status')=='selesai' and t['function'] in ('DS','FIN'):
                    before=t.copy();t['needs_recheck']=True;save(c,'tasks',t,'system',before)
    return result

@app.post('/api/records/{kind}')
async def create(kind:str,request:Request):
    u=who(request,True);body=await request.json()
    if kind not in COLLECTIONS or not isinstance(body,dict):raise HTTPException(400,'Jenis data tidak dikenali')
    with db() as c:
        if kind=='tasks':
            if u['role']!='lead':raise HTTPException(403,'Hanya Ahmad menambah tugas')
            parent=find(c,'tasks',body.get('parent',''))
            if parent.get('level')!='macro':raise HTTPException(400,'Pilih tugas besar')
            item={**body,'id':'ST-'+uuid.uuid4().hex[:10].upper(),'level':'subtask','parent':parent['id'],'owner':parent['owner'],'function':parent['function'],
             'status':'belum_mulai','weight':1,'start':parent['start'],'due':body.get('due',parent['due']),'baseline_due':body.get('due',parent['due']),
             'completed_checks':[],'checklist':body.get('checklist',[]),'actual_result':''}
        elif kind=='data':
            if u['role']!='lead':raise HTTPException(403,'Hanya Ahmad menentukan permintaan data baru')
            title=str(body.get('title','')).strip()
            category=str(body.get('category','')).strip()
            purpose=str(body.get('purpose','')).strip()
            if not title or not category or not purpose or any(len(x)>250 for x in (title,category,purpose)):
                raise HTTPException(400,'Isi nama data, kelompok dan tujuan secara singkat')
            item={'id':'DATA-'+uuid.uuid4().hex[:10].upper(),'title':title,'category':category,
               'purpose':purpose,'owner':'angga','source_owner':str(body.get('source_owner','Pemilik dokumen terkait'))[:200],
               'priority':'normal','status':'belum_diminta','validation':'belum_diperiksa',
               'note':'','source_link':'','received_at':None}
        elif kind=='tools':
            if u['role'] not in ('lead','science'):raise HTTPException(403,'Tidak diizinkan')
            item={**body,'id':'TOOL-'+uuid.uuid4().hex[:8].upper(),'owner':'donny','status':'direncanakan'}
        elif kind in ('meetings','decisions'):
            if u['role']!='lead' and not (kind=='decisions' and u['role']=='manager'):raise HTTPException(403,'Tidak diizinkan')
            item={**body,'id':('MTG-' if kind=='meetings' else 'DEC-')+uuid.uuid4().hex[:8].upper(),
                  'status':'rencana' if kind=='meetings' else 'diusulkan','created_by':u['username']}
        else:raise HTTPException(403,'Permintaan data baru harus ditetapkan Ahmad melalui pengelolaan kebutuhan')
        insert(c,kind,item,u['username'])
    return item

@app.post('/api/chat')
def send_chat(body:ChatInput,request:Request):
    u=who(request,True)
    if body.channel not in channels(u['role']):raise HTTPException(403,'Tidak ada akses ruang pesan')
    with db() as c:
        cur=c.execute('INSERT INTO messages(channel,username,body,created_at) VALUES(?,?,?,?)',(body.channel,u['username'],body.body.strip(),now()))
        audit(c,u['username'],'message','chat',str(cur.lastrowid))
    return {'ok':True}

@app.post('/api/meetings/{rid}/publish')
def publish(rid:str,request:Request):
    u=who(request,True)
    if u['role']!='lead':raise HTTPException(403,'Hanya Ahmad dapat membagikan meeting')
    with db() as c:
        m=find(c,'meetings',rid);old=m.copy();m['status']='dibagikan';m['snapshot']=summary(c);save(c,'meetings',m,u['username'],old)
    return {'ok':True}
@app.post('/api/meetings/{rid}/read')
def read_meeting(rid:str,request:Request):
    u=who(request,True)
    with db() as c:
        m=find(c,'meetings',rid)
        if not cansee(u,'meetings',m):raise HTTPException(403,'Bahan rapat belum dibagikan')
        c.execute('INSERT OR REPLACE INTO read_receipts VALUES(?,?,?)',(rid,u['username'],now()))
    return {'ok':True}

@app.post('/api/upload')
async def upload(request:Request,kind:str=Form(...),ref_id:str=Form(...),file:UploadFile=File(...)):
    u=who(request,True)
    if kind not in COLLECTIONS:raise HTTPException(400,'Jenis tidak didukung')
    with db() as c:
        record=find(c,kind,ref_id)
        allowed=u['role']=='lead' or u['role']=='finance' and kind=='data' and record.get('owner')==u['username'] or u['role']=='science' and kind in ('tasks','tools') and record.get('owner')==u['username']
        if not allowed:raise HTTPException(403,'Tidak dapat mengunggah ke item ini')
    name,stream,size,checksum=await staged_file(file)
    fid=uuid.uuid4().hex
    blob='attachments/'+kind+'/'+ref_id+'/'+fid+Path(name).suffix.lower()
    try:
        STORE.put(stream,blob)
        with db() as c:
            c.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?)',(fid,kind,ref_id,name,blob,u['username'],now(),size))
            audit(c,u['username'],'uploaded',kind,ref_id,{'file_id':fid,'name':name,'sha256':checksum})
    except Exception:
        STORE.delete(blob)
        raise
    finally:stream.close()
    return {'ok':True,'file_id':fid}

@app.get('/api/documents')
def list_documents(request:Request,year:int|None=None,unit:str|None=None,ref_id:str|None=None,category:str|None=None,page:int=1,page_size:int=50):
    u=who(request)
    if u['role']=='manager':raise HTTPException(403,'Manajemen hanya dapat melihat ringkasan')
    if year is not None:check_year(year)
    if unit:unit=safe_unit(unit)
    if not 1<=page_size<=100 or page<1:raise HTTPException(400,'Pagination tidak valid')
    with db() as c:
        allowed_refs=[x['id'] for x in allrows(c,'data') if cansee(u,'data',x) and (u['role']!='science' or x.get('status')=='siap')]
        if not allowed_refs:return {'total':0,'page':page,'page_size':page_size,'items':[]}
        conditions=['d.data_ref IN ('+','.join('?'*len(allowed_refs))+')']
        args=list(allowed_refs)
        if year is not None:conditions.append('d.fiscal_year=?');args.append(year)
        if unit:conditions.append('d.business_unit=?');args.append(unit)
        if ref_id:conditions.append('d.data_ref=?');args.append(ref_id)
        if category:conditions.append('d.category=?');args.append(category)
        where=' AND '.join(conditions)
        total=c.execute('SELECT COUNT(*) AS n FROM document_index d WHERE '+where,args).fetchone()['n']
        rows=c.execute('''SELECT d.file_id,d.data_ref,d.business_unit,d.fiscal_year,d.reporting_period,
            d.category,d.original_name,d.version_num,d.remarks,d.created_at,
            f.size,f.uploaded_by,
            CASE WHEN d.storage_backend='google_drive' THEN 'google_drive' ELSE 'file' END AS source_type
            FROM document_index d JOIN files f ON d.file_id=f.id WHERE '''+
            where+' ORDER BY d.fiscal_year DESC,d.created_at DESC,d.file_id DESC LIMIT ? OFFSET ?',args+[page_size,(page-1)*page_size]).fetchall()
    return {'total':total,'page':page,'page_size':page_size,'items':[dict(x) for x in rows]}

@app.get('/api/documents/coverage')
def document_coverage(request:Request,ref_id:str,year:int,unit:str='EKA'):
    u=who(request);year=check_year(year);unit=safe_unit(unit)
    with db() as c:
        record=find(c,'data',ref_id)
        if not cansee(u,'data',record) or (u['role']=='science' and record.get('status')!='siap'):
            raise HTTPException(403,'Kelengkapan data ini tidak dapat dilihat')
        return {'current':scope_coverage(c,ref_id,unit,year),'history':coverage_history(c,ref_id,unit,year),
            'title':record['title'],'category':record['category'],'validation':record.get('validation','belum_diperiksa')}

@app.post('/api/documents/requirements')
def document_requirements(body:DocumentRequirement,request:Request):
    u=who(request,True)
    if u['role'] not in ('lead','finance'):raise HTTPException(403,'Hanya Angga atau Ahmad yang dapat mengatur kelengkapan')
    year=check_year(body.fiscal_year);unit=safe_unit(body.business_unit)
    try:mode,periods,note=validate_requirement(body.mode,body.required_periods,body.note)
    except ValueError as error:raise HTTPException(400,str(error))
    with db() as c:
        record=find(c,'data',body.data_ref)
        if u['role']=='finance' and record.get('owner')!=u['username']:raise HTTPException(403,'Data di luar kewenangan Anda')
        before=scope_coverage(c,body.data_ref,unit,year)
        save_requirement(c,body.data_ref,unit,year,mode,periods,note,u['username'],now())
        audit(c,u['username'],'document_requirement_updated','data',body.data_ref,{'year':year,'unit':unit,'mode':mode,'periods':periods,'note':note})
        after=scope_coverage(c,body.data_ref,unit,year)
        audit_coverage_transition(c,u['username'],before,after)
        return {'ok':True,'coverage':after}

@app.post('/api/documents/batch')
async def document_batch(request:Request,data_ref:str=Form(...),business_unit:str=Form(...),
 fiscal_year:int=Form(...),reporting_period:str=Form('tahunan'),remarks:str=Form(''),
 coverage_mode:str|None=Form(None),required_periods:str=Form(''),coverage_note:str=Form(''),
 files:list[UploadFile]|None=File(None),gdrive_url:str=Form(''),link_title:str=Form('')):
    u=who(request,True)
    if u['role'] not in ('finance','lead'):raise HTTPException(403,'Hanya koordinator data atau Ahmad yang dapat mengunggah')
    files=files or []
    reference=None
    if gdrive_url.strip():
        try:reference=google_drive_reference(gdrive_url)
        except ValueError as error:raise HTTPException(400,str(error))
    if not 1<=len(files)+bool(reference)<=MAX_BATCH:raise HTTPException(400,'Pilih file atau isi tautan Google Drive; maksimal 20 dokumen per pengiriman')
    link_title=link_title.strip()
    if len(link_title)>160 or any(ord(char)<32 for char in link_title):raise HTTPException(400,'Nama dokumen tautan maksimal 160 karakter, tanpa baris baru')
    if reporting_period not in ('tahunan','q1','q2','q3','q4','jan','feb','mar','apr','mei','jun','jul','agu','sep','okt','nov','des'):
        raise HTTPException(400,'Periode tidak dikenal')
    fiscal_year=check_year(fiscal_year);business_unit=safe_unit(business_unit)
    if len(remarks)>500:raise HTTPException(400,'Catatan maksimal 500 karakter')
    requirement=None
    if coverage_mode is not None:
        try:requirement=validate_requirement(coverage_mode,required_periods.split(',') if required_periods else [],coverage_note)
        except ValueError as error:raise HTTPException(400,str(error))
    with db() as c:
        record=find(c,'data',data_ref)
        if u['role']=='finance' and record.get('owner')!=u['username']:raise HTTPException(403,'Data di luar kewenangan Anda')
    added=[];skipped=[];staged=[];stored_keys=[]
    try:
        # Validate every file before saving any document from this batch.
        for file in files:staged.append(await staged_file(file))
        with db() as c:
            # Serialize batches for a data requirement so version numbers stay ordered.
            if DATABASE_URL:
                c.execute("SELECT id FROM records WHERE kind='data' AND id=? FOR UPDATE",(data_ref,))
            else:c.execute('BEGIN IMMEDIATE')
            record=find(c,'data',data_ref)
            before_coverage=scope_coverage(c,data_ref,business_unit,fiscal_year)
            if requirement:
                save_requirement(c,data_ref,business_unit,fiscal_year,*requirement,u['username'],now())
                audit(c,u['username'],'document_requirement_updated','data',data_ref,{'year':fiscal_year,'unit':business_unit,'mode':requirement[0],'periods':requirement[1],'note':requirement[2]})
            for name,stream,size,checksum in staged:
                previous=c.execute('''SELECT d.file_id,d.version_num,d.sha256 FROM document_index d
                  WHERE d.data_ref=? AND d.business_unit=? AND d.fiscal_year=?
                  AND d.reporting_period=? AND d.original_name=? ORDER BY d.version_num DESC''',
                  (data_ref,business_unit,fiscal_year,reporting_period,name)).fetchall()
                if any(x['sha256']==checksum for x in previous):
                    skipped.append({'name':name,'reason':'File identik sudah disimpan'});continue
                version=max((x['version_num'] for x in previous),default=0)+1
                fid=uuid.uuid4().hex
                key=f"eka/{business_unit}/{fiscal_year}/{data_ref}/{reporting_period}/v{version:03d}/{fid}{Path(name).suffix.lower()}"
                stored_keys.append(key)
                STORE.put(stream,key)
                c.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?)',(fid,'data',data_ref,name,key,u['username'],now(),size))
                c.execute('''INSERT INTO document_index(file_id,data_ref,business_unit,fiscal_year,reporting_period,
                    category,original_name,version_num,sha256,storage_key,storage_backend,remarks,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (fid,data_ref,business_unit,fiscal_year,reporting_period,record.get('category','Lainnya'),name,version,checksum,key,STORE.mode,remarks,now()))
                audit(c,u['username'],'annual_document_uploaded','data',data_ref,
                    {'id':fid,'year':fiscal_year,'unit':business_unit,'version':version,'sha256':checksum,'file':name})
                added.append({'file_id':fid,'name':name,'year':fiscal_year,'category':record.get('category','Lainnya'),'version':version,'size':size,'source_type':'file'})
            if reference:
                checksum=hashlib.sha256(('google-drive:'+reference['identifier']).encode()).hexdigest()
                existing=c.execute('''SELECT file_id FROM document_index WHERE data_ref=? AND business_unit=?
                    AND fiscal_year=? AND reporting_period=? AND storage_backend='google_drive' AND sha256=?''',
                    (data_ref,business_unit,fiscal_year,reporting_period,checksum)).fetchone()
                name=link_title or ('Folder' if reference['kind']=='folder' else 'Dokumen')+' Google Drive '+reference['identifier'][-8:]
                if existing:skipped.append({'name':name,'reason':'Tautan Google Drive yang sama sudah dicatat'})
                else:
                    previous=c.execute('''SELECT MAX(version_num) AS n FROM document_index WHERE data_ref=?
                        AND business_unit=? AND fiscal_year=? AND reporting_period=? AND original_name=? AND storage_backend='google_drive' ''',
                        (data_ref,business_unit,fiscal_year,reporting_period,name)).fetchone()
                    version=(previous['n'] or 0)+1;fid=uuid.uuid4().hex;created=now()
                    c.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?)',(fid,'data',data_ref,name,reference['url'],u['username'],created,0))
                    c.execute('''INSERT INTO document_index(file_id,data_ref,business_unit,fiscal_year,reporting_period,
                        category,original_name,version_num,sha256,storage_key,storage_backend,remarks,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (fid,data_ref,business_unit,fiscal_year,reporting_period,record.get('category','Lainnya'),name,version,checksum,reference['url'],'google_drive',remarks,created))
                    audit(c,u['username'],'google_drive_document_added','data',data_ref,{'id':fid,'year':fiscal_year,'unit':business_unit,'period':reporting_period,'url':reference['url'],'name':name})
                    added.append({'file_id':fid,'name':name,'year':fiscal_year,'category':record.get('category','Lainnya'),'version':version,'size':0,'source_type':'google_drive'})
            if added:
                changed={**record,'status':'diterima','received_at':record.get('received_at') or now(),'validation':'belum_diperiksa'}
                save(c,'data',changed,u['username'],record)
                if record.get('status')=='siap':
                    for task in allrows(c,'tasks'):
                        if task.get('level')=='subtask' and task.get('status')=='selesai' and (data_ref in task.get('linked_data_ids',[]) or data_ref in task.get('required_data_ids',[])):
                            original=task.copy();task['needs_recheck']=True;save(c,'tasks',task,'system',original)
            coverage=scope_coverage(c,data_ref,business_unit,fiscal_year)
            audit_coverage_transition(c,u['username'],before_coverage,coverage)
    except Exception:
        for key in stored_keys:
            try:STORE.delete(key)
            except Exception:pass
        raise
    finally:
        for _,stream,_,_ in staged:stream.close()
    return {'ok':True,'uploaded':added,'skipped':skipped,'count':len(added),'coverage':coverage}

@app.get('/api/files/{fid}')
def download(fid:str,request:Request):
    u=who(request)
    with db() as c:
        f=c.execute('SELECT * FROM files WHERE id=?',(fid,)).fetchone()
        if not f:raise HTTPException(404,'Berkas tidak ditemukan')
        record=find(c,f['kind'],f['ref_id'])
        if not cansee(u,f['kind'],record) or f['kind']=='data' and u['role']=='science' and record.get('status')!='siap':
            raise HTTPException(403,'Berkas tidak dapat dibuka')
        external=c.execute("SELECT storage_key FROM document_index WHERE file_id=? AND storage_backend='google_drive'",(fid,)).fetchone()
        if external:
            try:reference=google_drive_reference(external['storage_key'])
            except ValueError:raise HTTPException(400,'Tautan Google Drive tersimpan tidak valid')
            return RedirectResponse(reference['url'],status_code=303,headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})
    return STORE.response(f['blob_name'],f['name'])

if __name__=='__main__':
    import uvicorn
    host=os.getenv('EKA_HOST','127.0.0.1');port=int(os.getenv('EKA_PORT','8000'))
    print(f'\nEKA Workspace siap: http://{host}:{port} (jaringan mobile butuh alamat IP server dan koneksi yang aman)\n',flush=True)
    uvicorn.run(app,host=host,port=port)
