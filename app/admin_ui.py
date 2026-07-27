ADMIN_HTML = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CNC Master Cloud ENGINEERING CLIENT — Админ</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#ecf2f8;background:#0d1217}body{max-width:1380px;margin:auto;padding:22px}
h1{margin:0}.muted{color:#95a4b2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.card{background:#151d24;border:1px solid #293641;border-radius:14px;padding:16px;margin:14px 0}.wide{grid-column:1/-1}
input,select,textarea,button{box-sizing:border-box;width:100%;padding:10px;margin:5px 0;border:1px solid #3a4b58;border-radius:8px;background:#0e151b;color:#fff}
button{background:#2767a7;border:0;font-weight:700;cursor:pointer}.danger{background:#8e3030}.ok{color:#70db9a}.bad{color:#ff8585}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px;border-bottom:1px solid #2c3944;text-align:left;vertical-align:top}
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}.stat{background:#0e151b;padding:12px;border-radius:9px;text-align:center}.stat b{font-size:22px;display:block}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.policy{border:1px solid #30404c;border-radius:10px;padding:10px;margin:8px 0;background:#101820}
@media(max-width:700px){.row{grid-template-columns:1fr}}
</style></head>
<body>
<h1>⚙️ CNC Master Cloud ENGINEERING CLIENT</h1><div class="muted">Админ-панель · лимиты, пользователи, каталог и база</div>
<section class="card"><label>ADMIN_KEY</label><input id="key" type="password" placeholder="Ключ из Railway Variables"><button onclick="loadAll()">Подключиться</button><div id="status" class="muted"></div></section>
<div id="stats" class="statgrid"></div>
<div class="grid">
<section class="card wide"><h2>⏱ Лимиты функций по часам</h2>
<p class="muted">Лимит — число запусков одной функции на пользователя в течение текущего часа. Пустой лимит = без лимита. Время доступности задаётся по часам 0–23; одинаковые начало и конец = круглосуточно.</p>
<div id="policies"></div></section>
<section class="card"><h2>👤 Персональный доступ</h2>
<input id="ovTelegram" type="number" placeholder="Telegram ID пользователя"><select id="ovFeature"></select>
<div class="row"><select id="ovEnabled"><option value="inherit">Наследовать включение</option><option value="true">Включить</option><option value="false">Отключить</option></select><input id="ovLimit" type="number" min="0" placeholder="Лимит/час (пусто = общий)"></div>
<div class="row"><input id="ovStart" type="number" min="0" max="23" placeholder="Начало, час"><input id="ovEnd" type="number" min="0" max="23" placeholder="Конец, час"></div>
<label><input id="ovUnlimited" type="checkbox" style="width:auto"> Безлимит</label><textarea id="ovNote" placeholder="Комментарий"></textarea>
<button onclick="saveOverride()">Сохранить персональное правило</button></section>
<section class="card"><h2>🔩 Добавить инструмент</h2>
<input id="tKey" placeholder="Уникальный ключ, например MY001"><select id="tCategory"></select><input id="tSub" placeholder="Подкатегория"><input id="tName" placeholder="Название"><input id="tCode" placeholder="Маркировка"><input id="tOps" placeholder="Операции через запятую: turn_rough,face"><input id="tIso" placeholder="ISO через запятую: P,M"><textarea id="tDim" placeholder="Размеры"></textarea><textarea id="tDesc" placeholder="Описание"></textarea><textarea id="tCompat" placeholder="Совместимость"></textarea><textarea id="tHint" placeholder="Подсказка по марке/геометрии"></textarea><button onclick="addTool()">Добавить/обновить инструмент</button></section>
<section class="card wide"><h2>Пользователи</h2><div style="overflow:auto"><table><thead><tr><th>ID</th><th>Telegram</th><th>Имя</th><th>Username</th><th>Дата</th></tr></thead><tbody id="users"></tbody></table></div></section>
<section class="card"><h2>Материал</h2><input id="matCode" placeholder="AISI304"><input id="matName" placeholder="Название"><input id="matIso" placeholder="ISO P/M/K/N/S/H"><div class="row"><input id="matMin" type="number" placeholder="Vc min"><input id="matMax" type="number" placeholder="Vc max"></div><textarea id="matNotes" placeholder="Примечание"></textarea><button onclick="addMaterial()">Добавить материал</button></section>
<section class="card"><h2>Производитель стойки</h2><input id="mName" placeholder="Название"><input id="mSlug" placeholder="slug"><input id="mUrl" placeholder="Сайт"><button onclick="addManufacturer()">Добавить производителя</button></section>
<section class="card"><h2>Стойка ЧПУ</h2><select id="cManufacturer"></select><input id="cName" placeholder="Модель"><input id="cFamily" placeholder="Семейство"><input id="cTypes" placeholder="turning,milling,multitasking"><textarea id="cDesc" placeholder="Описание"></textarea><button onclick="addController()">Добавить стойку</button></section>
</div>
<script>
const $=id=>document.getElementById(id), statusEl=$('status'); const key=()=>$('key').value;
const headers=()=>({'Content-Type':'application/json','X-Admin-Key':key()});
async function req(url,opt={}){const r=await fetch(url,opt);if(!r.ok)throw new Error(await r.text());return r.json()}
function status(msg,ok=true){statusEl.textContent=msg;statusEl.className=ok?'ok':'bad'}
const val=id=>$(id).value; const numOrNull=id=>val(id)===''?null:+val(id);
async function loadAll(){try{const [stats,policies,users,mfr,tools]=await Promise.all([req('/api/v1/admin/stats',{headers:headers()}),req('/api/v1/admin/policies',{headers:headers()}),req('/api/v1/admin/users',{headers:headers()}),req('/api/v1/manufacturers'),req('/api/v1/tools/categories')]);
$('stats').innerHTML=Object.entries(stats).map(([k,v])=>`<div class="stat"><b>${v}</b>${k}</div>`).join('');
$('policies').innerHTML=policies.map(p=>`<div class="policy" id="p-${p.feature_key}"><b>${p.title}</b><div class="row"><label><input style="width:auto" type="checkbox" id="pe-${p.feature_key}" ${p.enabled?'checked':''}> Включено</label><input id="pl-${p.feature_key}" type="number" min="0" value="${p.limit_per_hour??''}" placeholder="Лимит/час"></div><div class="row"><input id="ps-${p.feature_key}" type="number" min="0" max="23" value="${p.allowed_start_hour??''}" placeholder="С какого часа"><input id="pn-${p.feature_key}" type="number" min="0" max="23" value="${p.allowed_end_hour??''}" placeholder="До какого часа"></div><input id="pt-${p.feature_key}" value="${p.timezone||'Europe/Kyiv'}" placeholder="Timezone"><button onclick="savePolicy('${p.feature_key}','${p.title.replaceAll("'","&#39;")}')">Сохранить</button></div>`).join('');
$('ovFeature').innerHTML=policies.map(p=>`<option value="${p.feature_key}">${p.title}</option>`).join('');
$('users').innerHTML=users.map(u=>`<tr><td>${u.id}</td><td>${u.telegram_id}</td><td>${u.full_name}</td><td>${u.username||''}</td><td>${u.created_at}</td></tr>`).join('');
$('cManufacturer').innerHTML=mfr.map(x=>`<option value="${x.id}">${x.name}</option>`).join('');
$('tCategory').innerHTML=Object.entries(tools.categories).map(([k,v])=>`<option value="${k}">${v}</option>`).join(''); status('Подключено');}catch(e){status(e.message,false)}}
async function savePolicy(k,title){try{await req('/api/v1/admin/policies/'+k,{method:'PUT',headers:headers(),body:JSON.stringify({feature_key:k,title,enabled:$('pe-'+k).checked,limit_per_hour:numOrNull('pl-'+k),allowed_start_hour:numOrNull('ps-'+k),allowed_end_hour:numOrNull('pn-'+k),timezone:val('pt-'+k)||'Europe/Kyiv'})});status('Лимит сохранён')}catch(e){status(e.message,false)}}
async function saveOverride(){try{const ev=val('ovEnabled');await req('/api/v1/admin/user-overrides',{method:'POST',headers:headers(),body:JSON.stringify({telegram_id:+val('ovTelegram'),feature_key:val('ovFeature'),enabled:ev==='inherit'?null:ev==='true',limit_per_hour:numOrNull('ovLimit'),allowed_start_hour:numOrNull('ovStart'),allowed_end_hour:numOrNull('ovEnd'),unlimited:$('ovUnlimited').checked,note:val('ovNote')||null})});status('Персональное правило сохранено')}catch(e){status(e.message,false)}}
async function addTool(){try{await req('/api/v1/admin/tools',{method:'POST',headers:headers(),body:JSON.stringify({key:val('tKey').toUpperCase(),category:val('tCategory'),subcategory:val('tSub')||'custom',name:val('tName'),code:val('tCode'),operation_tags:val('tOps').split(',').map(x=>x.trim()).filter(Boolean),iso_groups:val('tIso').split(',').map(x=>x.trim().toUpperCase()).filter(Boolean),dimensions:val('tDim'),description:val('tDesc'),compatibility:val('tCompat'),grade_hint:val('tHint'),source:'Добавлено администратором',active:true})});status('Инструмент добавлен')}catch(e){status(e.message,false)}}
async function addMaterial(){try{await req('/api/v1/admin/materials',{method:'POST',headers:headers(),body:JSON.stringify({code:val('matCode').toUpperCase(),name:val('matName'),iso_group:val('matIso').toUpperCase()||null,vc_min:numOrNull('matMin'),vc_max:numOrNull('matMax'),notes:val('matNotes')||null,active:true})});status('Материал добавлен')}catch(e){status(e.message,false)}}
async function addManufacturer(){try{await req('/api/v1/admin/manufacturers',{method:'POST',headers:headers(),body:JSON.stringify({name:val('mName'),slug:val('mSlug'),website_url:val('mUrl')||null,active:true})});status('Производитель добавлен');loadAll()}catch(e){status(e.message,false)}}
async function addController(){try{await req('/api/v1/admin/controllers',{method:'POST',headers:headers(),body:JSON.stringify({manufacturer_id:+val('cManufacturer'),name:val('cName'),family:val('cFamily')||null,machine_types:val('cTypes').split(',').map(x=>x.trim()).filter(Boolean),software_versions:[],description:val('cDesc')||null,active:true})});status('Стойка добавлена')}catch(e){status(e.message,false)}}
</script></body></html>"""
