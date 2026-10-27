/// <reference path="./app.js" />
/// <reference path="./coverage.js" />
'use strict';
/**
 * @typedef {HTMLFormElement & {elements: HTMLFormControlsCollection & {
 * fiscal_year: HTMLInputElement, business_unit: HTMLSelectElement,
 * data_ref: HTMLSelectElement, reporting_period: HTMLSelectElement,
 * files: HTMLInputElement, coverage_mode: HTMLSelectElement,
 * coverage_note: HTMLInputElement, gdrive_url: HTMLInputElement,
 * link_title: HTMLInputElement
 * }}} AnnualUploadForm
 */
/** @returns {AnnualUploadForm | null} */
function getAnnualForm(){const form=document.querySelector('form#annualForm');return form instanceof HTMLFormElement?/** @type {AnnualUploadForm} */(form):null}
/** @param {HTMLFormElement} form @param {string} id */
function annualButton(form,id){const button=form.querySelector('#'+id);if(!(button instanceof HTMLButtonElement))throw Error('Tombol '+id+' tidak ditemukan');return button}
let archiveDocs=[],archiveTotal=0,archiveYear=new Date().getFullYear(),archiveCategory='',archiveUnit='',archivePage=1,archiveLoading=false,archiveError='',archiveRequest=0;
const documentCategories=()=>[...new Set((D?.data||[]).map(row=>row.category||'Lainnya'))];
const uploadableData=()=>D.data.filter(row=>U.role==='lead'||row.owner===U.username);

function archiveHTML(){
 const years=Array.from({length:new Date().getFullYear()+4-2000},(_,i)=>new Date().getFullYear()+3-i);
 return `<div class="annual-archive-head"><div><b>Dokumen yang tersimpan</b><small>${archiveTotal} dokumen · Tahun ${archiveYear}</small></div><div class="annual-filters"><label>Tahun<select id="archiveYear">${years.map(year=>`<option value="${year}" ${archiveYear===year?'selected':''}>${year}</option>`).join('')}</select></label><label>Jenis dokumen<select id="archiveCategory"><option value="">Semua jenis</option>${documentCategories().map(category=>`<option ${archiveCategory===category?'selected':''}>${esc(category)}</option>`).join('')}</select></label><label>Unit bisnis<select id="archiveUnit"><option value="">Semua unit</option>${[['EKA','PT EKA AKAR JATI'],['HOTEL','Proyek Hotel'],['LAINNYA','Unit Usaha Lain']].map(([value,label])=>`<option value="${value}" ${archiveUnit===value?'selected':''}>${label}</option>`).join('')}</select></label></div></div>
 ${archiveLoading?'<p class="empty" role="status">Memuat dokumen…</p>':archiveError?`<p class="error annual-message" role="alert">${esc(archiveError)} <button type="button" class="btn" data-archive-retry>Coba lagi</button></p>`:archiveDocs.length?archiveDocs.map(doc=>`<div class="annual-row"><div><strong>${esc(doc.original_name)}</strong><small>${doc.fiscal_year} · ${esc(doc.category)} · ${esc(doc.business_unit)} · ${esc(doc.reporting_period)} · Versi ${doc.version_num} · ${doc.source_type==='google_drive'?'Tautan Google Drive':Math.ceil(doc.size/1024)+' KB'}</small></div><a class="btn" href="/api/files/${encodeURIComponent(doc.file_id)}" ${doc.source_type==='google_drive'?'target="_blank"':''} rel="noopener noreferrer">${doc.source_type==='google_drive'?'Buka Google Drive':'Unduh'}</a></div>`).join(''):`<p class="empty">Belum ada dokumen sesuai filter tahun ${archiveYear}.</p>`}
 ${archiveTotal>50?`<div class="annual-actions annual-message"><button type="button" class="btn" data-archive-page="-1" ${archiveLoading||archivePage<=1?'disabled':''}>Sebelumnya</button><small>Halaman ${archivePage} dari ${Math.ceil(archiveTotal/50)}</small><button type="button" class="btn" data-archive-page="1" ${archiveLoading||archivePage*50>=archiveTotal?'disabled':''}>Berikutnya</button></div>`:''}`;
}
function updateArchive(){const archive=document.querySelector('#annualArchive');if(archive)archive.innerHTML=archiveHTML()}
async function loadArchive(){
 if(!U||U.role==='manager')return;
 const sequence=++archiveRequest,version=sessionVersion;
 archiveLoading=true;archiveError='';updateArchive();
 const query=new URLSearchParams({year:String(archiveYear),page:String(archivePage),page_size:'50'});
 if(archiveCategory)query.set('category',archiveCategory);
 if(archiveUnit)query.set('unit',archiveUnit);
 try{
  const result=await request('/api/documents?'+query);
  if(sequence!==archiveRequest||version!==sessionVersion)return;
  archiveDocs=result.items;archiveTotal=result.total;
 }catch(error){if(sequence===archiveRequest&&version===sessionVersion){archiveDocs=[];archiveTotal=0;archiveError='Arsip gagal dimuat: '+error.message}}
 finally{if(sequence===archiveRequest&&version===sessionVersion){archiveLoading=false;updateArchive()}}
}
function resetArchive(){archiveRequest++;archiveDocs=[];archiveTotal=0;archiveYear=new Date().getFullYear();archiveCategory='';archiveUnit='';archivePage=1;archiveLoading=false;archiveError='';resetCoverage()}
function yearlyPanel(){
 const rows=uploadableData(),categories=[...new Set(rows.map(row=>row.category||'Lainnya'))],category=categories[0]||'';
 const canUpload=['finance','lead'].includes(U.role)&&rows.length;
 return `<section class="panel annual-panel"><div class="annual-title"><div><div class="eyebrow">PENYIMPANAN DOKUMEN</div><h3>Arsip laporan tahunan</h3><p>Pilih tahun dan jenis dokumen, lalu unggah file langsung atau kirim tautan Google Drive. Keduanya dapat dikirim bersama.</p></div><span class="pill">File atau Google Drive</span></div>
 ${canUpload?`<form id="annualForm" class="annual-form"><fieldset><legend class="section-title">KIRIM DOKUMEN</legend><div class="annual-grid">
 <label>Tahun laporan<input name="fiscal_year" type="number" min="2000" max="${new Date().getFullYear()+3}" value="${archiveYear}" required></label>
 <label>Jenis dokumen<select id="annualCategory" required>${categories.map(value=>`<option>${esc(value)}</option>`).join('')}</select></label>
 <label>Unit bisnis<select name="business_unit" required><option value="EKA">PT EKA AKAR JATI</option><option value="HOTEL">Proyek Hotel</option><option value="LAINNYA">Unit Usaha Lain</option></select></label>
 <label class="annual-wide">Kebutuhan data<select name="data_ref" required>${rows.filter(row=>(row.category||'Lainnya')===category).map(row=>`<option value="${esc(row.id)}">${esc(row.title)}</option>`).join('')}</select></label>
 ${coverageControlsHTML()}
 <label>Periode dokumen<select name="reporting_period"><option value="tahunan">Tahunan</option>${[['q1','Kuartal 1'],['q2','Kuartal 2'],['q3','Kuartal 3'],['q4','Kuartal 4'],...['jan','feb','mar','apr','mei','jun','jul','agu','sep','okt','nov','des'].map(month=>[month,month.toUpperCase()])].map(([value,label])=>`<option value="${value}">${label}</option>`).join('')}</select></label>
 <label class="annual-wide">Unggah file langsung<input type="file" name="files" multiple accept=".pdf,.xlsx,.xls,.csv,.docx,.png,.jpg,.jpeg,.webp,.txt" aria-describedby="annualFileHint"><small id="annualFileHint">Opsional jika memakai Google Drive. Maksimal 20 dokumen per pengiriman, 25 MB per file. File identik dilewati; revisi disimpan sebagai versi baru.</small></label>
 <div id="annualFileList" class="annual-wide annual-file-list" aria-live="polite">Belum ada file dipilih.</div>
 <div class="annual-wide drive-inputs"><strong>Atau gunakan tautan Google Drive</strong><label>Tautan file / folder Google Drive<input name="gdrive_url" type="url" maxlength="2048" placeholder="https://drive.google.com/file/d/.../view" aria-describedby="driveLinkHint"></label><label>Nama dokumen tautan (opsional)<input name="link_title" maxlength="160" placeholder="Contoh: Laporan Keuangan 2021 — Google Drive"></label><small id="driveLinkHint">Boleh tautan file, folder, Google Sheets, atau Google Docs. Pastikan akun reviewer sudah diberi akses. Tautan dicatat di arsip; file tetap berada di Google Drive.</small></div>
 <label class="annual-wide">Catatan sumber<input name="remarks" maxlength="500" placeholder="Contoh: Laporan keuangan 2023 dari tim Finance"></label></div>
 <div class="annual-actions"><button type="submit" id="annualSubmit" class="btn primary">Simpan dokumen</button><small>Pilih file, isi tautan Google Drive, atau gunakan keduanya.</small></div></fieldset><p id="annualResult" role="status" aria-live="polite">Dokumen yang dikirim masih perlu diperiksa sebelum dinyatakan siap.</p></form>`:''}
 <div id="annualArchive" class="annual-archive">${archiveHTML()}</div></section>`;
}
/** @param {AnnualUploadForm} form */
async function submitAnnual(form){
 if(form.dataset.uploading||form.dataset.coverageSaving)return;
 const requirement=coveragePayload(form);
 const selected=[...form.elements.files.files];
 const driveURL=form.elements.gdrive_url.value.trim();
 if(!selected.length&&!driveURL)throw Error('Pilih file atau isi tautan Google Drive terlebih dahulu');
 if(selected.length+Number(!!driveURL)>20)throw Error('Maksimal 20 dokumen (file dan tautan) per pengiriman');
 for(const file of selected){if(!file.size)throw Error('File '+file.name+' kosong');if(file.size>25*1024*1024)throw Error('File '+file.name+' melebihi 25 MB')}
 const categoryInput=form.querySelector('#annualCategory');
 if(!(categoryInput instanceof HTMLSelectElement))throw Error('Pilihan jenis dokumen tidak ditemukan');
 const payload=new FormData(form),version=sessionVersion,category=categoryInput.value;
 if(!selected.length)payload.delete('files');
 payload.set('gdrive_url',driveURL);
 payload.set('required_periods',requirement.required_periods.join(','));payload.set('coverage_note',requirement.note);
 const button=form.querySelector('#annualSubmit'),fieldset=form.querySelector('fieldset'),result=form.querySelector('#annualResult');
 form.dataset.uploading='true';fieldset.disabled=true;button.textContent='Menyimpan dokumen…';result.textContent='Sedang menyimpan dokumen. Tunggu sampai selesai.';
 let uploaded;
 try{
  uploaded=await request('/api/documents/batch',{method:'POST',body:payload});
 }catch(error){result.textContent='Pengiriman gagal. File dan tautan tetap tersedia untuk dicoba lagi. '+error.message;throw error}
 finally{delete form.dataset.uploading;fieldset.disabled=false;button.textContent='Simpan dokumen'}
 if(version!==sessionVersion||!U)return;
 archiveYear=Number(payload.get('fiscal_year'));archiveCategory=category;archiveUnit=String(payload.get('business_unit')||'');archivePage=1;
 const message=`${uploaded.count} dokumen tersimpan pada tahun ${archiveYear}, ${category}. ${uploaded.skipped.length} ${driveURL?'dokumen duplikat':'file identik'} dilewati.`;
 // Mark the successful upload immediately, even if refreshing the list later fails.
 form.elements.files.value='';form.elements.gdrive_url.value='';form.elements.link_title.value='';form.querySelector('#annualFileList').textContent='Belum ada file dipilih.';result.textContent=message;
 for(const row of D.data)if(row.id===payload.get('data_ref')&&uploaded.count){row.status='diterima';row.validation='belum_diperiksa'}
 await Promise.all([loadArchive(),loadCoverage()]);toast(message+(uploaded.coverage.done?' Pengumpulan dokumen tahun ini Done.':''));
}
addEventListener('change',event=>{
 const target=event.target;
 if(!(target instanceof HTMLInputElement||target instanceof HTMLSelectElement))return;
 if(target.id==='annualCategory'){
  const form=getAnnualForm();if(!form)return;const select=form.elements.data_ref;
  select.innerHTML=uploadableData().filter(row=>(row.category||'Lainnya')===target.value).map(row=>`<option value="${esc(row.id)}">${esc(row.title)}</option>`).join('');
  loadCoverage();
 }
 if(target instanceof HTMLInputElement&&target.matches('#annualForm input[name="files"]')){
  const files=[...target.files];document.querySelector('#annualFileList').innerHTML=files.length?`<b>${files.length} file dipilih</b><ul>${files.map(file=>`<li>${esc(file.name)} <small>(${Math.ceil(file.size/1024)} KB)</small></li>`).join('')}</ul>`:'Belum ada file dipilih.';
 }
 if(['archiveYear','archiveCategory','archiveUnit'].includes(target.id)){
  if(target.id==='archiveYear')archiveYear=Number(target.value);
  if(target.id==='archiveCategory')archiveCategory=target.value;
  if(target.id==='archiveUnit')archiveUnit=target.value;
  archivePage=1;loadArchive();
 }
});
addEventListener('click',event=>{
 const target=event.target;if(!(target instanceof Element))return;
 const next=target.closest('[data-archive-page]');
 if(next instanceof HTMLElement){archivePage=Math.max(1,archivePage+Number(next.dataset.archivePage));loadArchive()}
 if(target.closest('[data-archive-retry]'))loadArchive();
});
