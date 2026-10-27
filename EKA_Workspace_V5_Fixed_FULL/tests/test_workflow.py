import os,sys,importlib
from pathlib import Path
from fastapi.testclient import TestClient

def connect(tmp_path,monkeypatch):
    monkeypatch.setenv('EKA_DATA_DIR',str(tmp_path/'datastore'))
    root=str(Path(__file__).resolve().parents[1]);sys.path.insert(0,root)
    if 'app' in sys.modules:del sys.modules['app']
    api=importlib.import_module('app')
    passwords=dict(x.split(': ',1) for x in (tmp_path/'datastore'/'AKUN_AWAL.txt').read_text().strip().splitlines())
    result={}
    for u,pwd in passwords.items():
        c=TestClient(api.app);r=c.post('/api/login',json={'username':u,'password':pwd})
        assert r.status_code==200
        result[u]=(c,{'X-CSRF-Token':r.json()['csrf']})
    return result

def test_roles_data_and_review(tmp_path,monkeypatch):
    x=connect(tmp_path,monkeypatch)
    a,ah=x['ahmad'];d,dh=x['donny'];f,fh=x['angga'];m,mh=x['management']
    aa=a.get('/api/bootstrap').json();dd=d.get('/api/bootstrap').json();ff=f.get('/api/bootstrap').json();mm=m.get('/api/bootstrap').json()
    assert len(aa['tasks'])==77 and len(aa['data'])==120
    assert len([v for v in dd['tasks'] if v['level']=='macro'])==4
    assert len([v for v in ff['tasks'] if v['level']=='macro'])==3 and len(ff['data'])==120
    assert len(mm['data'])==len(mm['tools'])==len(mm['files'])==0
    assert len(mm['summary']['macros'])==13
    assert m.patch('/api/records/tasks/ST-FIN-01-01',headers=mh,json={'status':'selesai'}).status_code==403
    assert d.patch('/api/records/tasks/ST-FIN-01-01',headers=dh,json={'status':'dikerjakan'}).status_code==403
    assert f.patch('/api/records/tasks/ST-DS-01-01',headers=fh,json={'status':'dikerjakan'}).status_code==403
    assert m.post('/api/chat',headers=mh,json={'channel':'umum','body':'test'}).status_code==403
    assert m.post('/api/chat',headers=mh,json={'channel':'meeting','body':'Info meeting'}).status_code==200
    assert d.patch('/api/records/tasks/ST-DS-01-01',json={'status':'selesai'},headers=dh).status_code==403
    assert a.patch('/api/records/tasks/ST-DS-01-01',json={'status':'selesai'},headers=ah).status_code==400
    t=next(t for t in dd['tasks'] if t['id']=='ST-DS-01-01')
    assert d.patch('/api/records/tasks/ST-DS-01-01',json={'status':'menunggu_review','actual_result':'Hasil percobaan','completed_checks':t['checklist']},headers=dh).status_code==200
    assert a.get('/api/bootstrap').json()['summary']['overall']==0
    assert a.patch('/api/records/tasks/ST-DS-01-01',json={'status':'selesai'},headers=ah).status_code==200
    assert a.get('/api/bootstrap').json()['summary']['overall']>0
    assert a.patch('/api/records/tasks/FIN-01',json={'due':'2026-11-05'},headers=ah).status_code==400
    assert a.patch('/api/records/tasks/FIN-01',json={'due':'2026-11-05','schedule_reason':'Dokumen menunggu pihak hotel'},headers=ah).status_code==200
    assert next(t for t in a.get('/api/bootstrap').json()['tasks'] if t['id']=='FIN-01')['baseline_due']=='2026-10-27'
    assert f.patch('/api/records/data/DATA-001',json={'status':'diterima','source_link':'https://intranet.test/finance'},headers=fh).status_code==200
    assert a.patch('/api/records/data/DATA-001',json={'status':'siap','validation':'valid'},headers=ah).status_code==200
    assert a.get('/api/bootstrap').json()['summary']['data_ready']==1
    assert len(m.get('/api/bootstrap').json()['data'])==0
    assert m.get('/api/files/nonexistent').status_code==404
    # management review works after submission
    mt=next(t for t in mm['tasks'] if t['id']=='ST-MGT-01-01')
    assert m.patch('/api/records/tasks/ST-MGT-01-01',json={'status':'menunggu_review','actual_result':'Sudah ditinjau','completed_checks':mt['checklist']},headers=mh).status_code==200
    assert m.patch('/api/records/tasks/ST-MGT-01-01',json={'status':'selesai'},headers=mh).status_code==200
    # Lead can't approve management
    assert a.patch('/api/records/tasks/ST-MGT-01-02',json={'status':'selesai'},headers=ah).status_code==403

def test_upload_password_and_pwa(tmp_path,monkeypatch):
    x=connect(tmp_path,monkeypatch)
    a,ah=x['ahmad'];f,fh=x['angga'];d,dh=x['donny']
    r=f.post('/api/upload',headers=fh,data={'kind':'data','ref_id':'DATA-001'},files={'file':('test.csv',b'year,value\n2025,100\n','text/csv')})
    assert r.status_code==200,r.text
    fid=r.json()['file_id']
    assert f.get('/api/files/'+fid).status_code==200
    assert d.get('/api/files/'+fid).status_code==403
    assert a.patch('/api/records/data/DATA-001',json={'status':'siap','validation':'valid'},headers=ah).status_code==400
    assert f.patch('/api/records/data/DATA-001',json={'status':'diterima'},headers=fh).status_code==200
    assert a.patch('/api/records/data/DATA-001',json={'status':'siap','validation':'valid'},headers=ah).status_code==200
    assert d.get('/api/files/'+fid).status_code==200
    assert a.get('/manifest.webmanifest').status_code==200
    assert a.get('/sw.js').status_code==200
    assert a.post('/api/change-password',headers=ah,json={'old':'wrong','new':'validpassword123'}).status_code==400
    assert a.post('/api/change-password',headers=ah,json={'old':'wrong','new':'small'}).status_code==400
