import sys
from test_document_cloud import setup_client


def upload(client,headers,year,period='tahunan',ref='DATA-001',unit='EKA',**extra):
    result=client.post('/api/documents/batch',data={
        'data_ref':ref,'business_unit':unit,'fiscal_year':year,'reporting_period':period,**extra,
    },files=[('files',(period+'.pdf',b'%PDF-1.4\nTest report','application/pdf'))],headers=headers)
    assert result.status_code==200,result.text
    return result.json()


def get_coverage(client,year,ref='DATA-001',unit='EKA'):
    result=client.get('/api/documents/coverage',params={'ref_id':ref,'year':year,'unit':unit})
    assert result.status_code==200,result.text
    return result.json()


def test_annual_only_is_done_and_years_are_independent(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    result=upload(finance,headers,2021)
    assert result['coverage']['done'] is True
    assert result['coverage']['required_periods']==['tahunan']
    assert result['coverage']['missing_periods']==[]
    assert result['coverage']['progress']==100
    upload(finance,headers,2022,'jan')
    history=get_coverage(finance,2023)['history']
    by_year={row['fiscal_year']:row for row in history}
    assert by_year[2021]['status']=='done'
    assert by_year[2022]['status']=='sebagian'
    assert by_year[2023]['status']=='belum_ada'
    assert get_coverage(finance,2021,unit='HOTEL')['current']['done'] is False
    assert get_coverage(finance,2021,ref='DATA-002')['current']['done'] is False
    # Collection completeness does not silently approve data or accept work results.
    record=next(row for row in finance.get('/api/bootstrap').json()['data'] if row['id']=='DATA-001')
    assert record['status']=='diterima' and record['validation']=='belum_diperiksa'
    assert people['ahmad'][0].get('/api/bootstrap').json()['summary']['overall']==0


def test_monthly_and_quarterly_require_only_selected_cadence(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    annual=upload(finance,headers,2021,coverage_mode='tahunan',coverage_note='Hanya ada tahunan')
    assert annual['coverage']['done'] is True
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2022,'mode':'bulanan'}
    assert finance.post('/api/documents/requirements',json=body,headers=headers).status_code==200
    # An annual file cannot satisfy an explicitly requested monthly plan.
    assert upload(finance,headers,2022)['coverage']['done'] is False
    for index,month in enumerate(['jan','feb','mar','apr','mei','jun','jul','agu','sep','okt','nov','des']):
        result=upload(finance,headers,2022,month)['coverage']
        assert result['completed_periods']==index+1
        assert result['done']==(index==11)
    assert get_coverage(finance,2021)['current']['mode']=='tahunan'
    for index,quarter in enumerate(['q1','q2','q3','q4']):
        result=upload(finance,headers,2023,quarter)['coverage']
        assert result['done']==(index==3)
    assert result['basis']=='kuartalan'


def test_custom_periods_need_reason_and_persist(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2021,'mode':'khusus','required_periods':['jan','mar']}
    assert finance.post('/api/documents/requirements',json=body,headers=headers).status_code==400
    body['note']='Hanya Januari dan Maret yang dibutuhkan untuk kajian ini'
    response=finance.post('/api/documents/requirements',json=body,headers=headers)
    assert response.status_code==200,response.text
    assert response.json()['coverage']['done'] is False
    assert upload(finance,headers,2021,'jan')['coverage']['missing_periods']==['mar']
    assert upload(finance,headers,2021,'mar')['coverage']['done'] is True
    sys.modules['app'].setup()
    saved=get_coverage(finance,2021)['current']
    assert saved['configured_periods']==['jan','mar'] and saved['note']==body['note'] and saved['done'] is True
    assert finance.post('/api/documents/requirements',json={**body,'required_periods':['invalid']},headers=headers).status_code==400


def test_requirement_access_and_failed_batch_preserve_previous_plan(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    science,science_headers=people['donny']
    manager,manager_headers=people['management']
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2021,'mode':'tahunan'}
    assert finance.post('/api/documents/requirements',json=body).status_code==403
    for client,h in [(science,science_headers),(manager,manager_headers)]:
        assert client.post('/api/documents/requirements',json=body,headers=h).status_code==403
        assert client.get('/api/documents/coverage?ref_id=DATA-001&year=2021').status_code==403
    assert finance.post('/api/documents/requirements',json=body,headers=headers).status_code==200
    result=finance.post('/api/documents/batch',data={
        'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2021,'coverage_mode':'bulanan',
    },files=[('files',('Good.pdf',b'%PDF-1.4\nOK','application/pdf')),('files',('Bad.pdf',b'Not PDF','application/pdf'))],headers=headers)
    assert result.status_code==400
    assert get_coverage(finance,2021)['current']['mode']=='tahunan'
    assert get_coverage(finance,2021)['current']['document_count']==0


def test_existing_v6_annual_uploads_become_done_without_reupload(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    upload(finance,headers,2021)
    api=sys.modules['app']
    with api.db() as connection:connection.execute('DROP TABLE document_requirements')
    api.setup()
    assert get_coverage(finance,2021)['current']['done'] is True


def test_done_transitions_are_audited_without_duplicate_events(tmp_path,monkeypatch):
    people=setup_client(tmp_path,monkeypatch)
    finance,headers=people['angga']
    upload(finance,headers,2021)
    upload(finance,headers,2021)
    api=sys.modules['app']
    with api.db() as connection:
        assert connection.execute("SELECT COUNT(*) n FROM audit WHERE action='document_collection_done'").fetchone()['n']==1
    body={'data_ref':'DATA-001','business_unit':'EKA','fiscal_year':2021,'mode':'bulanan'}
    assert finance.post('/api/documents/requirements',json=body,headers=headers).status_code==200
    assert finance.post('/api/documents/requirements',json={**body,'mode':'tahunan'},headers=headers).status_code==200
    with api.db() as connection:
        assert connection.execute("SELECT COUNT(*) n FROM audit WHERE action='document_collection_done'").fetchone()['n']==2
        assert connection.execute("SELECT COUNT(*) n FROM audit WHERE action='document_collection_reopened'").fetchone()['n']==1
