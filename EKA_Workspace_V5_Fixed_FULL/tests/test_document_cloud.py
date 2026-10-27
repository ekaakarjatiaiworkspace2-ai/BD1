import os,sys,importlib,io
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def setup_client(tmp_path,monkeypatch):
    monkeypatch.setenv('EKA_DATA_DIR',str(tmp_path/'work'))
    for k in ['DATABASE_URL','S3_BUCKET','EKA_DEPLOY_MODE']:
        monkeypatch.delenv(k,raising=False)
    if 'app' in sys.modules:del sys.modules['app']
    app=importlib.import_module('app')
    secret={}
    for line in (tmp_path/'work'/'AKUN_AWAL.txt').read_text().splitlines():
        if ': ' in line:
            user,pw=line.split(': ',1)
            secret[user]=pw
    people={}
    for name in ['ahmad','angga','donny','management']:
        cli=TestClient(app.app)
        res=cli.post('/api/login',json={'username':name,'password':secret[name]})
        assert res.status_code==200
        people[name]=(cli,{'x-csrf-token':res.json()['csrf']})
    return people

def test_batch_upload_versions_and_access(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,f_headers=users['angga']
    lead,l_headers=users['ahmad']
    science,_=users['donny']
    management,_=users['management']
    ref=next(x for x in finance.get('/api/bootstrap').json()['data'] if x['owner']=='angga')['id']
    body={'data_ref':ref,'business_unit':'EKA','fiscal_year':'2025','reporting_period':'tahunan','remarks':'Contoh keuangan internal'}
    documents=[('files',('Laba_Rugi.pdf',b'%PDF-1.4\nLABA RUGI\n','application/pdf')),
               ('files',('Neraca.csv',b'Akun,Nilai\nKas,100\n','text/csv'))]
    result=finance.post('/api/documents/batch',data=body,files=documents,headers=f_headers)
    assert result.status_code==200,result.text
    assert result.json()['count']==2
    assert finance.get('/api/documents?year=2025').json()['total']==2
    assert finance.get('/api/documents?year=2024').json()['total']==0
    assert management.get('/api/documents?year=2025').status_code==403
    assert science.get('/api/documents?year=2025').json()['total']==0
    file_id=result.json()['uploaded'][0]['file_id']
    assert finance.get('/api/files/'+file_id).status_code==200
    assert management.get('/api/files/'+file_id).status_code==403
    assert science.get('/api/files/'+file_id).status_code==403
    original=finance.post('/api/documents/batch',data=body,files=[documents[0]],headers=f_headers)
    assert original.status_code==200 and original.json()['count']==0
    updated=finance.post('/api/documents/batch',data=body,files=[('files',('Laba_Rugi.pdf',b'%PDF-1.4\nREVISI\n','application/pdf'))],headers=f_headers)
    assert updated.status_code==200
    assert updated.json()['uploaded'][0]['version']==2
    assert finance.get('/api/documents?year=2025').json()['total']==3
    obj=next(d for d in finance.get('/api/bootstrap').json()['data'] if d['id']==ref)
    assert obj['status']=='diterima'
    approved=lead.patch('/api/records/data/'+ref,json={'status':'siap','validation':'valid'},headers=l_headers)
    assert approved.status_code==200,approved.text

def test_rejected_and_role_isolation(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,h=people['angga'];science,sh=people['donny']
    ref=next(x for x in finance.get('/api/bootstrap').json()['data'] if x['owner']=='angga')['id']
    body={'data_ref':ref,'business_unit':'EKA','fiscal_year':'2025','reporting_period':'tahunan'}
    assert science.post('/api/documents/batch',data=body,files=[('files',('test.pdf',b'%PDF-1.4\nOK','application/pdf'))],headers=sh).status_code==403
    too_big_year={**body,'fiscal_year':'1999'}
    assert finance.post('/api/documents/batch',data=too_big_year,files=[('files',('test.pdf',b'%PDF-1.4\nOK','application/pdf'))],headers=h).status_code==400
    bad=finance.post('/api/documents/batch',data=body,files=[('files',('fake.pdf',b'NOT PDF','application/pdf'))],headers=h)
    assert bad.status_code==400
    assert finance.get('/api/documents').json()['total']==0


def test_excel_pdf_grouping_across_years(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,headers=users['angga']
    record=next(row for row in finance.get('/api/bootstrap').json()['data'] if row['category']=='Laporan Keuangan')
    body={'data_ref':record['id'],'business_unit':'EKA','fiscal_year':'2023','reporting_period':'tahunan','remarks':'Laporan 2023'}
    files=[('files',('Neraca.xlsx',b'PK\x03\x04EXCEL FIXTURE','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
           ('files',('Laporan.pdf',b'%PDF-1.4\nLaporan 2023','application/pdf'))]
    result=finance.post('/api/documents/batch',data=body,files=files,headers=headers)
    assert result.status_code==200,result.text
    assert result.json()['count']==2
    listing=finance.get('/api/documents',params={'year':2023,'category':'Laporan Keuangan','unit':'EKA'}).json()
    assert listing['total']==2
    assert all(row['fiscal_year']==2023 and row['category']=='Laporan Keuangan' and row['data_ref']==record['id'] for row in listing['items'])
    assert finance.get('/api/documents',params={'year':2023,'category':'Riset Pasar'}).json()['total']==0
    assert finance.get('/api/documents',params={'year':2023,'unit':'HOTEL'}).json()['total']==0
    other_year=finance.post('/api/documents/batch',data={**body,'fiscal_year':'2024'},files=files,headers=headers)
    assert other_year.json()['count']==2
    assert all(row['version']==1 for row in other_year.json()['uploaded'])
    assert finance.get('/api/documents?year=2023').json()['total']==2
    assert finance.get('/api/documents?year=2024').json()['total']==2
    for document in listing['items']:
        assert finance.get('/api/files/'+document['file_id']).content==next(file[1][1] for file in files if file[1][0]==document['original_name'])


def test_validation_failure_does_not_save_partial_batch(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,headers=users['angga']
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':'2023'}
    result=finance.post('/api/documents/batch',data=body,files=[
        ('files',('Valid.pdf',b'%PDF-1.4\nOK','application/pdf')),
        ('files',('Invalid.pdf',b'NOT PDF','application/pdf')),
    ],headers=headers)
    assert result.status_code==400
    assert finance.get('/api/documents').json()['total']==0
    assert finance.get('/api/bootstrap').json()['files']==[]
    assert not any(path.is_file() for path in (tmp_path/'work'/'uploads').rglob('*'))


def test_storage_failure_rolls_back_batch(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,headers=users['angga']
    api=sys.modules['app']
    original_put=api.STORE.put
    calls=[]
    def failing_put(stream,key):
        original_put(stream,key)
        calls.append(key)
        if len(calls)==2:raise OSError('Simulated storage failure')
    monkeypatch.setattr(api.STORE,'put',failing_put)
    client=TestClient(api.app,raise_server_exceptions=False)
    client.cookies.update(finance.cookies)
    before=finance.get('/api/bootstrap').json()['data'][0]
    result=client.post('/api/documents/batch',data={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2023,'coverage_mode':'bulanan'},files=[
        ('files',('One.pdf',b'%PDF-1.4\nOne','application/pdf')),
        ('files',('Two.pdf',b'%PDF-1.4\nTwo','application/pdf')),
    ],headers=headers)
    assert result.status_code==500
    assert finance.get('/api/documents').json()['total']==0
    assert finance.get('/api/bootstrap').json()['files']==[]
    assert finance.get('/api/bootstrap').json()['data'][0]==before
    assert finance.get('/api/documents/coverage?ref_id=DATA-001&year=2023').json()['current']['mode']=='fleksibel'
    assert not any(path.is_file() for path in api.UPLOADS.rglob('*'))


def test_batch_limits_duplicates_and_csrf(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,headers=users['angga']
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':'2023'}
    file=('files',('Same.pdf',b'%PDF-1.4\nOK','application/pdf'))
    assert finance.post('/api/documents/batch',data=body,files=[file],headers={}).status_code==403
    assert finance.post('/api/documents/batch',data=body,files=[file]*21,headers=headers).status_code==400
    assert finance.post('/api/documents/batch',data=body,files=[('files',('Empty.pdf',b'','application/pdf'))],headers=headers).status_code==400
    monkeypatch.setattr(sys.modules['app'],'MAX_UPLOAD',8)
    assert finance.post('/api/documents/batch',data=body,files=[file],headers=headers).status_code==413
    monkeypatch.setattr(sys.modules['app'],'MAX_UPLOAD',25*1024*1024)
    result=finance.post('/api/documents/batch',data=body,files=[file,file],headers=headers)
    assert result.json()['count']==1 and len(result.json()['skipped'])==1


def test_existing_v5_accounts_and_attachments_survive_setup(tmp_path,monkeypatch):
    users=setup_client(tmp_path,monkeypatch)
    finance,headers=users['angga']
    api=sys.modules['app']
    blob='legacy-report.csv'
    (api.UPLOADS/blob).write_bytes(b'year,value\n2023,100\n')
    with api.db() as connection:
        hashes=[tuple(row) for row in connection.execute('SELECT username,password_hash FROM accounts ORDER BY username')]
        connection.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?)',('legacy','data','DATA-001','Report.csv',blob,'angga',api.now(),20))
        connection.execute('DROP TABLE document_index')
    api.setup()
    with api.db() as connection:
        assert hashes==[tuple(row) for row in connection.execute('SELECT username,password_hash FROM accounts ORDER BY username')]
        assert connection.execute('SELECT COUNT(*) n FROM document_index').fetchone()['n']==0
    assert finance.get('/api/bootstrap').status_code==200
    assert finance.get('/api/files/legacy').content==b'year,value\n2023,100\n'
