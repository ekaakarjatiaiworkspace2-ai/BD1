import sys
import pytest
from fastapi.testclient import TestClient
from test_document_cloud import setup_client
from document_links import google_drive_reference

DRIVE='https://drive.google.com/file/d/test-report-2021/view?usp=sharing'


def send(client,headers,**extra):
    return client.post('/api/documents/batch',data={
        'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':'2021','reporting_period':'tahunan',
        'gdrive_url':DRIVE,'link_title':'Laporan Keuangan 2021',**extra,
    },headers=headers)


@pytest.mark.parametrize('url',[
    'http://drive.google.com/file/d/test-report-2021/view',
    'https://drive.google.com.evil.test/file/d/test-report-2021/view',
    'https://drive.google.com@evil.test/file/d/test-report-2021/view',
    'https://user:password@drive.google.com/file/d/test-report-2021/view',
    'https://drive.google.com:1234/file/d/test-report-2021/view',
    'javascript:alert(1)','https://example.com/report.pdf','https://drive.google.com/',
    'https://drive.google.com/redirect?url=https://evil.test',
    'https://docs.google.com/document/d/tiny/edit',
    'https://drive.google.com/open?id=bad%2Fpath',
    'https://drive.google.com/file/d/test-report-2021/view\nLocation:evil',
])
def test_reject_invalid_or_untrusted_links(url):
    with pytest.raises(ValueError):google_drive_reference(url)


@pytest.mark.parametrize('url',[
    DRIVE,'https://drive.google.com/drive/folders/folder-finance-2021',
    'https://drive.google.com/drive/u/0/folders/folder-finance-2021',
    'https://drive.google.com/open?id=test-report-2021',
    'https://docs.google.com/spreadsheets/d/sheet-finance-2021/edit#gid=0',
    'https://docs.google.com/document/d/doc-finance-2021/edit',
])
def test_supported_drive_references(url):
    reference=google_drive_reference(url)
    assert reference['url'].startswith('https://') and reference['identifier']


def test_link_only_archive_coverage_and_access(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga'];lead,lead_headers=people['ahmad'];science,_=people['donny'];manager,_=people['management']
    result=send(finance,headers)
    assert result.status_code==200,result.text
    assert result.json()['count']==1
    coverage=result.json()['coverage']
    assert coverage['done'] and coverage['link_count']==1 and coverage['file_count']==0
    listing=finance.get('/api/documents?year=2021').json()
    assert listing['total']==1 and listing['items'][0]['source_type']=='google_drive'
    fid=result.json()['uploaded'][0]['file_id']
    response=finance.get('/api/files/'+fid,follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='https://drive.google.com/file/d/test-report-2021/view'
    assert science.get('/api/files/'+fid,follow_redirects=False).status_code==403
    assert manager.get('/api/files/'+fid,follow_redirects=False).status_code==403
    assert lead.patch('/api/records/data/DATA-001',headers=lead_headers,json={'status':'siap','validation':'valid'}).status_code==200
    assert science.get('/api/files/'+fid,follow_redirects=False).status_code==303
    assert not any(path.is_file() for path in (tmp_path/'work'/'uploads').rglob('*'))


def test_duplicate_links_versions_scope_and_resource_key(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    first=send(finance,headers,gdrive_url=DRIVE+'&resourcekey=key_123')
    assert first.status_code==200
    fid=first.json()['uploaded'][0]['file_id']
    assert 'resourcekey=key_123' in finance.get('/api/files/'+fid,follow_redirects=False).headers['location']
    duplicate=send(finance,headers,gdrive_url='https://drive.google.com/open?id=test-report-2021',link_title='Nama baru')
    assert duplicate.json()['count']==0 and len(duplicate.json()['skipped'])==1
    assert send(finance,headers,fiscal_year='2022').json()['count']==1
    revised=send(finance,headers,gdrive_url='https://drive.google.com/file/d/revised-report-2021/view')
    assert revised.json()['uploaded'][0]['version']==2
    assert finance.get('/api/documents?year=2021').json()['total']==2


def test_files_and_link_can_be_sent_together_and_validate_atomically(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':'2021','gdrive_url':'https://evil.test/data'}
    files=[('files',('Report.pdf',b'%PDF-1.4\nLocal report','application/pdf'))]
    assert finance.post('/api/documents/batch',data=body,files=files,headers=headers).status_code==400
    assert finance.get('/api/documents').json()['total']==0
    result=finance.post('/api/documents/batch',data={**body,'gdrive_url':DRIVE},files=files,headers=headers)
    assert result.status_code==200,result.text
    assert result.json()['count']==2
    assert result.json()['coverage']['file_count']==1 and result.json()['coverage']['link_count']==1
    assert result.json()['coverage']['completed_periods']==1
    assert send(finance,{},fiscal_year=2023).status_code==403
    assert send(*people['donny']).status_code==403
    assert send(finance,headers,gdrive_url='').status_code==400


def test_mixed_batch_database_failure_rolls_back_files_and_link(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga'];api=sys.modules['app'];original=api.audit
    def fail_link_audit(connection,user,action,*args,**kwargs):
        if action=='google_drive_document_added':raise RuntimeError('Simulated database failure')
        return original(connection,user,action,*args,**kwargs)
    monkeypatch.setattr(api,'audit',fail_link_audit)
    client=TestClient(api.app,raise_server_exceptions=False);client.cookies.update(finance.cookies)
    result=client.post('/api/documents/batch',data={
        'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':'2021','gdrive_url':DRIVE,'coverage_mode':'tahunan',
    },files=[('files',('Report.pdf',b'%PDF-1.4\nTest','application/pdf'))],headers=headers)
    assert result.status_code==500
    assert finance.get('/api/documents').json()['total']==0
    assert finance.get('/api/bootstrap').json()['files']==[]
    assert not any(path.is_file() for path in api.UPLOADS.rglob('*'))
    with api.db() as connection:assert connection.execute('SELECT COUNT(*) AS n FROM document_requirements').fetchone()['n']==0
