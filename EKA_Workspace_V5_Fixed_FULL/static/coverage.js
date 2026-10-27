/// <reference path="./app.js" />
/// <reference path="./annual.js" />
'use strict';
const COVERAGE_PERIODS=[['tahunan','Tahunan'],['q1','Kuartal 1'],['q2','Kuartal 2'],['q3','Kuartal 3'],['q4','Kuartal 4'],...['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'].map(month=>[month.toLowerCase(),month])];
const COVERAGE_MODES={fleksibel:'Fleksibel: tahunan atau periode lengkap',tahunan:'Tahunan saja',kuartalan:'Kuartalan (4 kuartal)',bulanan:'Bulanan (12 bulan)',khusus:'Periode tertentu'};
let coverageData=null,coverageScopeKey='',coverageRequest=0,coverageLoading=false;
const coveragePeriodLabel=period=>COVERAGE_PERIODS.find(([value])=>value===period)?.[1]||period;
function selectedCoverageScope(){
 const form=getAnnualForm();
 if(!form)return null;
 const fiscal_year=Number(form.elements.fiscal_year.value);
 if(!Number.isInteger(fiscal_year)||fiscal_year<2000||fiscal_year>new Date().getFullYear()+3)return null;
 return {data_ref:form.elements.data_ref.value,business_unit:form.elements.business_unit.value,fiscal_year};
}
const coverageKey=scope=>scope?JSON.stringify(scope):'';
function coverageControlsHTML(){
 return `<div class="annual-wide coverage-settings"><div class="coverage-heading"><strong>Kapan pengumpulan dokumen dianggap Done?</strong><small>Berlaku hanya untuk tahun, unit, dan kebutuhan data yang dipilih di atas.</small></div>
 <label>Patokan kelengkapan<select name="coverage_mode" id="coverageMode">${Object.entries(COVERAGE_MODES).map(([value,label])=>`<option value="${value}">${label}</option>`).join('')}</select><small id="coverageRule">Satu laporan tahunan sudah cukup; data bulanan tidak wajib.</small></label>
 <div id="coverageCustom" hidden><span>Pilih periode yang memang dibutuhkan</span><div class="coverage-periods">${COVERAGE_PERIODS.map(([value,label])=>`<label><input type="checkbox" name="coverage_period" value="${value}">${label}</label>`).join('')}</div></div>
 <label>Catatan ketersediaan / alasan periode<input name="coverage_note" maxlength="500" placeholder="Contoh: Tahun 2021 hanya tersedia laporan tahunan; bulanan tidak dibutuhkan."></label>
 <button type="button" id="saveCoverage" class="btn subtle">Simpan kebutuhan tahun ini</button>
 <div id="coverageSummary" class="coverage-summary" role="status" aria-live="polite">Memuat kelengkapan…</div>
 <div id="coverageHistory" class="coverage-history"></div></div>`;
}
/** @param {HTMLFormElement} form */
function coveragePeriodInputs(form){return [...form.querySelectorAll('input')].filter(input=>input.name==='coverage_period')}
function updateCoverageRule(){
 const form=getAnnualForm();if(!form)return;
 const mode=form.elements.coverage_mode.value;
 document.getElementById('coverageCustom').hidden=mode!=='khusus';
 const rules={fleksibel:'Cukup 1 laporan tahunan, atau 4 kuartal, atau 12 bulan. Laporan tahunan tidak memerlukan data bulanan.',tahunan:'Hanya laporan tahunan yang dibutuhkan. Bulanan dan kuartalan tidak wajib.',kuartalan:'Lengkap setelah keempat kuartal tersedia.',bulanan:'Lengkap setelah 12 bulan tersedia.',khusus:'Hanya periode yang dicentang yang dibutuhkan. Isi alasan pemilihan periode.'};
 document.querySelector('#coverageRule').textContent=rules[mode];
 const allowed=mode==='tahunan'?['tahunan']:mode==='kuartalan'?['q1','q2','q3','q4']:mode==='bulanan'?COVERAGE_PERIODS.slice(5).map(([value])=>value):mode==='khusus'?coveragePeriodInputs(form).filter(input=>input.checked).map(input=>input.value):COVERAGE_PERIODS.map(([value])=>value);
 const period=form.elements.reporting_period;
 for(const option of period.options)option.disabled=!allowed.includes(option.value);
 if(!allowed.includes(period.value))period.value=allowed[0]||'';
 period.required=true;
}
function drawCoverage(result){
 const item=result.current;
 const status=item.done?'Done — dokumen lengkap':item.status==='sebagian'?'Sebagian dokumen tersedia':'Belum ada dokumen';
 const missing=item.missing_periods.map(coveragePeriodLabel).join(', ');
 document.querySelector('#coverageSummary').innerHTML=`<div class="coverage-status"><b class="pill ${item.done?'done':item.status==='sebagian'?'warn':''}">${status}</b><strong>${item.fiscal_year} · ${esc(result.title)} · ${esc(item.business_unit)}</strong></div><p>${item.completed_periods}/${item.total_periods} periode terpenuhi · ${item.document_count} dokumen (${item.file_count} file, ${item.link_count} tautan) · ${item.progress}%</p>${item.done?`<p>Lengkap berdasarkan ${esc(COVERAGE_MODES[item.basis]||'periode yang dipilih')}.${['tahunan'].includes(item.basis)?' Data bulanan tidak wajib.':''}</p>`:`<p>Belum tersedia: ${esc(missing)}.${item.mode==='fleksibel'?' Satu laporan tahunan juga dapat melengkapi kebutuhan ini.':''}</p>`}<small>Done mencatat kelengkapan pengumpulan dokumen. Pemeriksaan isi data: ${result.validation==='valid'?'sudah valid':result.validation==='belum_diperiksa'?'belum diperiksa':'perlu diperiksa'}.</small>`;
 document.querySelector('#coverageHistory').innerHTML=`<strong>Riwayat kelengkapan per tahun</strong>${result.history.map(row=>`<div class="coverage-year"><button type="button" data-coverage-year="${row.fiscal_year}" class="btn ${row.fiscal_year===item.fiscal_year?'subtle':''}">${row.fiscal_year}</button><span>${esc(COVERAGE_MODES[row.mode])}<small>${row.document_count} dokumen · ${row.completed_periods}/${row.total_periods} periode</small></span><b class="pill ${row.done?'done':row.status==='sebagian'?'warn':''}">${row.done?'Done':row.status==='sebagian'?'Sebagian':'Belum ada'}</b></div>`).join('')}`;
}
async function loadCoverage(){
 const form=getAnnualForm(),scope=selectedCoverageScope();
 if(!form)return;
 const sequence=++coverageRequest,version=sessionVersion,key=coverageKey(scope);
 coverageLoading=true;annualButton(form,'annualSubmit').disabled=true;annualButton(form,'saveCoverage').disabled=true;
 if(!scope){document.querySelector('#coverageSummary').textContent='Isi tahun laporan yang valid terlebih dahulu.';coverageLoading=false;return}
 document.querySelector('#coverageSummary').textContent='Memuat kelengkapan tahun '+scope.fiscal_year+'…';
 document.querySelector('#coverageHistory').replaceChildren();
 try{
  const result=await request('/api/documents/coverage?'+new URLSearchParams({ref_id:scope.data_ref,unit:scope.business_unit,year:String(scope.fiscal_year)}));
  if(sequence!==coverageRequest||version!==sessionVersion||key!==coverageKey(selectedCoverageScope()))return;
  coverageData=result;coverageScopeKey=key;
  form.elements.coverage_mode.value=result.current.mode;form.elements.coverage_note.value=result.current.note;
  coveragePeriodInputs(form).forEach(input=>input.checked=result.current.configured_periods.includes(input.value));
  updateCoverageRule();drawCoverage(result);
  annualButton(form,'annualSubmit').disabled=false;annualButton(form,'saveCoverage').disabled=false;
 }catch(error){if(sequence===coverageRequest&&version===sessionVersion){coverageData=null;coverageScopeKey='';document.querySelector('#coverageSummary').innerHTML=`<p class="error">${esc(error.message)}</p><button type="button" class="btn" data-coverage-retry>Coba muat kelengkapan lagi</button>`}}
 finally{if(sequence===coverageRequest)coverageLoading=false}
}
/** @param {AnnualUploadForm} form */
function coveragePayload(form){
 const scope=selectedCoverageScope();
 if(!scope||coverageLoading||coverageKey(scope)!==coverageScopeKey)throw Error('Tunggu kelengkapan tahun ini selesai dimuat');
 const mode=form.elements.coverage_mode.value,required_periods=coveragePeriodInputs(form).filter(input=>input.checked).map(input=>input.value),note=form.elements.coverage_note.value.trim();
 if(mode==='khusus'&&(!required_periods.length||!note))throw Error('Pilih periode yang dibutuhkan dan isi alasan pada catatan');
 return {...scope,mode,required_periods:mode==='khusus'?required_periods:[],note};
}
async function saveCoverage(){
 const form=getAnnualForm();if(!form||form.dataset.uploading||form.dataset.coverageSaving)return;
 try{
  const body=coveragePayload(form);form.dataset.coverageSaving='true';annualButton(form,'saveCoverage').disabled=true;
  await request('/api/documents/requirements',{method:'POST',body:JSON.stringify(body)});
  await loadCoverage();toast('Kebutuhan dokumen tahun '+body.fiscal_year+' disimpan.');
 }catch(error){err(error)}
 finally{delete form.dataset.coverageSaving;if(form.isConnected&&!coverageLoading&&coverageScopeKey===coverageKey(selectedCoverageScope()))annualButton(form,'saveCoverage').disabled=false}
}
function resetCoverage(){coverageRequest++;coverageData=null;coverageScopeKey='';coverageLoading=false}
addEventListener('change',event=>{
 const target=event.target;if(!(target instanceof HTMLInputElement||target instanceof HTMLSelectElement))return;
 if(target.matches('#annualForm [name=fiscal_year],#annualForm [name=business_unit],#annualForm [name=data_ref]'))loadCoverage();
 if(target.id==='coverageMode'||target.name==='coverage_period')updateCoverageRule();
});
addEventListener('click',event=>{
 const target=event.target;if(!(target instanceof Element))return;
 if(target.closest('#saveCoverage'))saveCoverage();
 if(target.closest('[data-coverage-retry]'))loadCoverage();
 const year=target.closest('[data-coverage-year]');
 if(year instanceof HTMLElement){const form=getAnnualForm();if(form){form.elements.fiscal_year.value=year.dataset.coverageYear;loadCoverage()}}
});
