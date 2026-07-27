ADMIN_HTML = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CNC Master Cloud — админка</title>
  <style>
    :root{font-family:Inter,system-ui,sans-serif;color:#e8edf2;background:#101418}
    body{max-width:1180px;margin:0 auto;padding:24px}
    h1{margin:0 0 4px}.muted{color:#9aa7b2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
    .card{background:#182027;border:1px solid #293640;border-radius:14px;padding:18px;margin:16px 0}
    input,select,textarea,button{box-sizing:border-box;width:100%;padding:10px;margin:6px 0;border-radius:9px;border:1px solid #3a4a56;background:#11181e;color:#fff}
    button{background:#2b6cb0;border:0;font-weight:700;cursor:pointer}button:hover{filter:brightness(1.1)}
    table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px;border-bottom:1px solid #2b3740}
    .stats{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.stat{background:#11181e;padding:12px;border-radius:10px;text-align:center}
    .stat b{font-size:22px;display:block}.ok{color:#74d99f}.bad{color:#ff8585}
    @media(max-width:800px){.stats{grid-template-columns:repeat(2,1fr)}}
  </style>
</head>
<body>
  <h1>⚙️ CNC Master Cloud</h1>
  <div class="muted">Админ-панель онлайн-базы</div>

  <section class="card">
    <label>ADMIN_KEY</label>
    <input id="key" type="password" placeholder="Вставьте ключ из .env">
    <button onclick="loadAll()">Подключиться и обновить</button>
    <div id="status" class="muted"></div>
  </section>

  <div id="stats" class="stats"></div>

  <div class="grid">
    <section class="card">
      <h2>Производитель</h2>
      <input id="mName" placeholder="Название">
      <input id="mSlug" placeholder="slug">
      <input id="mUrl" placeholder="Официальный сайт">
      <button onclick="addManufacturer()">Добавить</button>
    </section>

    <section class="card">
      <h2>Стойка ЧПУ</h2>
      <select id="cManufacturer"></select>
      <input id="cName" placeholder="Модель стойки">
      <input id="cFamily" placeholder="Семейство">
      <input id="cTypes" placeholder="Типы через запятую: turning,milling">
      <textarea id="cDesc" placeholder="Описание"></textarea>
      <button onclick="addController()">Добавить</button>
    </section>

    <section class="card">
      <h2>G/M-код</h2>
      <select id="codeController"></select>
      <select id="codeType"><option>G</option><option>M</option></select>
      <input id="codeValue" placeholder="G96">
      <input id="codeTitle" placeholder="Название">
      <textarea id="codeDesc" placeholder="Описание"></textarea>
      <input id="codeSyntax" placeholder="Синтаксис">
      <input id="codeSource" placeholder="Ссылка на источник">
      <button onclick="addCode()">Добавить</button>
    </section>

    <section class="card">
      <h2>Материал</h2>
      <input id="matCode" placeholder="AISI304">
      <input id="matName" placeholder="Название">
      <input id="matIso" placeholder="ISO-группа: P/M/K/N/S/H">
      <div class="grid">
        <input id="matMin" type="number" placeholder="Vc min">
        <input id="matMax" type="number" placeholder="Vc max">
      </div>
      <textarea id="matNotes" placeholder="Примечания"></textarea>
      <button onclick="addMaterial()">Добавить</button>
    </section>
  </div>

  <section class="card">
    <h2>Стойки в базе</h2>
    <div style="overflow:auto"><table><thead><tr><th>ID</th><th>Производитель</th><th>Модель</th><th>Типы</th></tr></thead><tbody id="controllersTable"></tbody></table></div>
  </section>

<script>
const statusEl = document.getElementById('status');
const key = () => document.getElementById('key').value;
const headers = () => ({'Content-Type':'application/json','X-Admin-Key':key()});

async function req(url, options={}) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
function setStatus(msg, ok=true){statusEl.textContent=msg;statusEl.className=ok?'ok':'bad'}
async function loadAll(){
  try{
    const [stats,mfr,ctl]=await Promise.all([
      req('/api/v1/admin/stats',{headers:headers()}),
      req('/api/v1/manufacturers'),
      req('/api/v1/controllers')
    ]);
    document.getElementById('stats').innerHTML=Object.entries(stats).map(([k,v])=>`<div class="stat"><b>${v}</b>${k}</div>`).join('');
    const mOpts=mfr.map(x=>`<option value="${x.id}">${x.name}</option>`).join('');
    document.getElementById('cManufacturer').innerHTML=mOpts;
    document.getElementById('codeController').innerHTML=ctl.map(x=>`<option value="${x.id}">${x.manufacturer?.name||''} — ${x.name}</option>`).join('');
    document.getElementById('controllersTable').innerHTML=ctl.map(x=>`<tr><td>${x.id}</td><td>${x.manufacturer?.name||''}</td><td>${x.name}</td><td>${(x.machine_types||[]).join(', ')}</td></tr>`).join('');
    setStatus('Подключено');
  }catch(e){setStatus(e.message,false)}
}
async function addManufacturer(){
  try{
    await req('/api/v1/admin/manufacturers',{method:'POST',headers:headers(),body:JSON.stringify({
      name:mName.value,slug:mSlug.value,website_url:mUrl.value||null,active:true
    })}); setStatus('Производитель добавлен'); loadAll();
  }catch(e){setStatus(e.message,false)}
}
async function addController(){
  try{
    await req('/api/v1/admin/controllers',{method:'POST',headers:headers(),body:JSON.stringify({
      manufacturer_id:+cManufacturer.value,name:cName.value,family:cFamily.value||null,
      machine_types:cTypes.value.split(',').map(x=>x.trim()).filter(Boolean),
      software_versions:[],description:cDesc.value||null,active:true
    })}); setStatus('Стойка добавлена'); loadAll();
  }catch(e){setStatus(e.message,false)}
}
async function addCode(){
  try{
    await req('/api/v1/admin/codes',{method:'POST',headers:headers(),body:JSON.stringify({
      controller_id:+codeController.value,code_type:codeType.value,code:codeValue.value.toUpperCase(),
      title:codeTitle.value,description:codeDesc.value,syntax:codeSyntax.value||null,
      source_url:codeSource.value||null,verification_status:'needs_review',active:true
    })}); setStatus('Код добавлен');
  }catch(e){setStatus(e.message,false)}
}
async function addMaterial(){
  try{
    await req('/api/v1/admin/materials',{method:'POST',headers:headers(),body:JSON.stringify({
      code:matCode.value.toUpperCase(),name:matName.value,iso_group:matIso.value.toUpperCase()||null,
      vc_min:matMin.value?+matMin.value:null,vc_max:matMax.value?+matMax.value:null,
      notes:matNotes.value||null,active:true
    })}); setStatus('Материал добавлен'); loadAll();
  }catch(e){setStatus(e.message,false)}
}
</script>
</body>
</html>"""
