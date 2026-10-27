"""Collection completeness per requirement, business unit and fiscal year."""
import json

MONTHS=['jan','feb','mar','apr','mei','jun','jul','agu','sep','okt','nov','des']
QUARTERS=['q1','q2','q3','q4']
PERIODS=['tahunan',*QUARTERS,*MONTHS]
MODES={'fleksibel','tahunan','kuartalan','bulanan','khusus'}


def validate_requirement(mode,periods,note):
    if mode not in MODES:raise ValueError('Pola kelengkapan tidak dikenal')
    if not isinstance(periods,list) or any(period not in PERIODS for period in periods):
        raise ValueError('Daftar periode tidak valid')
    note=note.strip()
    if len(note)>500:raise ValueError('Catatan kelengkapan maksimal 500 karakter')
    if mode=='khusus' and (not periods or not note):
        raise ValueError('Pola khusus memerlukan periode yang dipilih dan alasan kebutuhan')
    return mode,[period for period in PERIODS if period in periods] if mode=='khusus' else [],note


def save_requirement(c,ref,unit,year,mode,periods,note,username,updated_at):
    c.execute('''INSERT INTO document_requirements(data_ref,business_unit,fiscal_year,mode,required_periods,note,updated_by,updated_at)
        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(data_ref,business_unit,fiscal_year) DO UPDATE SET
        mode=excluded.mode,required_periods=excluded.required_periods,note=excluded.note,
        updated_by=excluded.updated_by,updated_at=excluded.updated_at''',
        (ref,unit,year,mode,json.dumps(periods),note,username,updated_at))


def scope_coverage(c,ref,unit,year):
    row=c.execute('''SELECT mode,required_periods,note FROM document_requirements
        WHERE data_ref=? AND business_unit=? AND fiscal_year=?''',(ref,unit,year)).fetchone()
    mode=row['mode'] if row else 'fleksibel'
    configured=json.loads(row['required_periods']) if row else []
    counts=c.execute('''SELECT reporting_period,COUNT(*) AS n,
        SUM(CASE WHEN storage_backend='google_drive' THEN 1 ELSE 0 END) AS links FROM document_index
        WHERE data_ref=? AND business_unit=? AND fiscal_year=? GROUP BY reporting_period''',(ref,unit,year)).fetchall()
    available={item['reporting_period'] for item in counts}
    paths={'tahunan':['tahunan'],'kuartalan':QUARTERS,'bulanan':MONTHS,'khusus':configured}
    if mode=='fleksibel':
        # Annual alone is sufficient; otherwise use the most complete periodic path.
        basis,required=max(((key,paths[key]) for key in ('tahunan','kuartalan','bulanan')),
            key=lambda item:sum(period in available for period in item[1])/len(item[1]))
    else:basis,required=mode,paths[mode]
    present=[period for period in required if period in available]
    missing=[period for period in required if period not in available]
    done=bool(required) and not missing
    return {'data_ref':ref,'business_unit':unit,'fiscal_year':year,'mode':mode,
        'configured_periods':configured,'note':row['note'] if row else '',
        'available_periods':[period for period in PERIODS if period in available],
        'required_periods':required,'missing_periods':missing,'basis':basis,
        'done':done,'status':'done' if done else 'sebagian' if available else 'belum_ada',
        'completed_periods':len(present),'total_periods':len(required),
        'progress':round(100*len(present)/len(required)) if required else 0,
        'document_count':sum(item['n'] for item in counts),
        'link_count':sum(item['links'] for item in counts),
        'file_count':sum(item['n']-item['links'] for item in counts)}


def coverage_history(c,ref,unit,year):
    rows=c.execute('''SELECT fiscal_year FROM document_index WHERE data_ref=? AND business_unit=?
        UNION SELECT fiscal_year FROM document_requirements WHERE data_ref=? AND business_unit=?''',
        (ref,unit,ref,unit)).fetchall()
    years={year,*[row['fiscal_year'] for row in rows]}
    return [scope_coverage(c,ref,unit,value) for value in sorted(years,reverse=True)]
