CLIENT_HTML = r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CNC Assistant Client Pro v4.1 — Universal Vision AI</title>
<!-- CNC Assistant Client Pro v3.0 AI Stock Removal Fix | Compatibility history: v2.3.0; v2.3.0 PRO; v2.4.0 Drawing Intelligence; Stainless logo; v2.7.0 PRO -->
<style>
:root{color-scheme:dark;--bg:#071018;--panel:#101b25;--panel2:#152432;--line:#294154;--text:#edf5fb;--muted:#93a8b8;--accent:#3b91e8;--ok:#49c987;--warn:#ffc766;--danger:#ff6d75}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.4 Inter,system-ui,-apple-system,Segoe UI,sans-serif}
button,input,select,textarea{font:inherit;color:var(--text);background:#0c1720;border:1px solid var(--line);border-radius:9px;padding:9px 10px}button{cursor:pointer}button:hover{border-color:var(--accent)}button.primary{background:var(--accent);border-color:var(--accent);font-weight:700}button.good{background:#176743;border-color:#24915f}.danger{color:#ff9aa1}.muted{color:var(--muted)}
header{display:flex;gap:16px;align-items:center;padding:14px 18px;background:#0d1821;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}header h1{font-size:17px;margin:0}header .badge{background:#17324a;padding:5px 9px;border-radius:999px;color:#a8d7ff}.spacer{flex:1}
.app{display:grid;grid-template-columns:330px minmax(620px,1fr) 410px;gap:10px;padding:10px;height:calc(100vh - 62px)}.panel{background:var(--panel);border:1px solid var(--line);border-radius:13px;overflow:auto}.section{padding:13px;border-bottom:1px solid var(--line)}.section h2{font-size:14px;margin:0 0 10px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.field{display:grid;gap:4px}.field label{font-size:12px;color:var(--muted)}.field input,.field select{width:100%;min-width:0}.row{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.row>*{min-width:0}
.canvasWrap{height:100%;display:grid;grid-template-rows:auto 1fr auto}.toolbar{padding:9px;display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line);background:var(--panel)}.toolbar button.active{background:#174f7d;border-color:#4da8ef}.stage{position:relative;min-height:400px;background:#061018;overflow:hidden}.stage canvas{position:absolute;inset:0;width:100%;height:100%}.statusbar{padding:8px 12px;border-top:1px solid var(--line);color:var(--muted);display:flex;gap:20px;min-height:37px}
.ops{display:grid;gap:8px}.op{border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:9px}.opHead{display:flex;align-items:center;gap:7px;margin-bottom:8px}.opHead strong{flex:1}.opGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.opGrid input{width:100%;padding:7px}.small{font-size:12px}.toolResult{padding:8px;background:#0b151e;border-radius:8px;margin-top:7px;color:#c6d7e5;min-height:34px}
.tabs{display:flex;gap:4px;padding:8px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel);z-index:2}.tabs button{padding:7px 9px}.tabs button.active{background:#194f78}.tab{display:none;padding:12px}.tab.active{display:block}.resultCard{border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:9px;background:#0d1821}.resultCard h3{font-size:14px;margin:0 0 8px}.kv{display:grid;grid-template-columns:1fr auto;gap:5px 10px}.kv div:nth-child(odd){color:var(--muted)}pre{white-space:pre-wrap;word-break:break-word;background:#050b10;border:1px solid var(--line);border-radius:10px;padding:10px;max-height:58vh;overflow:auto}ol{padding-left:22px}.warn{border-left:3px solid var(--warn);padding:8px 10px;background:#2a2415;margin:7px 0}.ok{border-left:3px solid var(--ok);padding:8px 10px;background:#12271e;margin:7px 0}
.modal{position:fixed;inset:0;background:#000b;display:none;align-items:center;justify-content:center;z-index:50}.modal.open{display:flex}.modalBox{width:min(900px,94vw);max-height:88vh;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}.toolList{display:grid;grid-template-columns:repeat(2,1fr);gap:7px}.toolItem{border:1px solid var(--line);border-radius:9px;padding:9px;cursor:pointer}.toolItem:hover{border-color:var(--accent)}
.guideGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.guideStep{border:1px solid var(--line);border-radius:11px;padding:11px;background:#0b1720}.guideStep.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}.guideStep .num{display:inline-grid;place-items:center;width:25px;height:25px;border-radius:50%;background:#194f78;font-weight:700;margin-right:7px}.confidence{display:inline-block;padding:2px 7px;border-radius:999px;background:#29331f;color:#d9f7a5}.dangerBox{border-left:3px solid var(--danger);padding:9px 10px;background:#2a1518;margin:7px 0}@media(max-width:760px){.guideGrid{grid-template-columns:1fr}}
@media(max-width:1200px){.app{grid-template-columns:300px 1fr}.results{grid-column:1/-1;max-height:600px}.stage{min-height:620px}}@media(max-width:760px){.app{display:block;height:auto}.panel{margin-bottom:10px}.stage{height:580px}.opGrid{grid-template-columns:1fr 1fr}.toolList{grid-template-columns:1fr}}

/* v2.8.0 PRO interface | AI region workflow and contour quality gates */
header{min-height:78px;padding:10px 16px;background:linear-gradient(180deg,#0b1721,#08131c)}
.brandBlock{display:flex;align-items:center;gap:14px;min-width:0}
.brandPlate{width:224px;height:58px;display:flex;align-items:center;justify-content:center;padding:4px 10px;border:1px solid #6e7d88;border-radius:10px;background:linear-gradient(145deg,#4d5962 0%,#1d2730 35%,#0c141c 70%,#26313a 100%);box-shadow:inset 0 1px 0 #ffffff55,inset 0 -1px 0 #000000aa,0 0 0 1px #0b1117,0 5px 16px #0009,0 0 12px #4db9ff24;overflow:hidden;flex:0 0 auto;position:relative}
.brandPlate:before,.brandPlate:after{content:"";position:absolute;width:5px;height:5px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#f3f6f8,#8b969e 45%,#2a3137 75%);box-shadow:0 1px 2px #000}.brandPlate:before{left:6px;top:6px}.brandPlate:after{right:6px;bottom:6px}.brandPlate img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 2px 2px #000b);position:relative;z-index:1}
.brandText{display:grid;gap:2px;min-width:0}.brandTitle{font-size:19px;font-weight:750;line-height:1.05;white-space:nowrap}.brandSub{font-size:15px;font-weight:650;white-space:nowrap}
.productMeta{display:flex;align-items:center;gap:12px;padding-left:4px;border-left:1px solid var(--line)}
.headerActions{display:flex;gap:8px}.headerActions button{min-height:48px;padding-inline:16px}
.app{grid-template-columns:minmax(360px,410px) minmax(560px,1fr) minmax(390px,470px);height:calc(100vh - 78px)}
.panel{scrollbar-color:#456075 #0b151e;scrollbar-width:thin}
.contourSection{display:flex;flex-direction:column;min-height:310px}
.contourHeader{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
.contourHeader h2{margin:0}.contourStats{font-size:11px;color:#b6c9d8;display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}
.statPill{border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:#0a151e}
.contourTableWrap{border:1px solid var(--line);border-radius:10px;overflow:auto;background:#07121a;min-height:214px;max-height:min(62vh,780px);transition:height .15s ease}
.contourTable{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:12px}
.contourTable th{position:sticky;top:0;z-index:2;background:#132534;color:#c9d9e5;text-align:left;border-bottom:1px solid var(--line);padding:7px 8px}
.contourTable td{padding:5px 8px;border-bottom:1px solid #1e3443;white-space:nowrap}.contourTable tr:hover td{background:#102330}
.contourTable input{width:88px;padding:4px 5px;border-radius:5px;background:#08131c}.contourTable select{padding:4px 5px;border-radius:5px;min-width:112px}
.contourRaw{display:none}
.contourActions{margin-top:8px}
.moduleStrip{display:flex;gap:5px;padding:7px 10px;border-bottom:1px solid var(--line);background:#0a151e;overflow:auto;position:sticky;top:0;z-index:3}
.moduleStrip button{white-space:nowrap;padding:6px 9px}.moduleStrip button.active{background:#174f7d;border-color:#4da8ef}
.guideGrid{grid-template-columns:1fr}.guideStep{display:grid;grid-template-columns:auto 1fr;column-gap:8px}.guideStep .small{grid-column:2}
@media(max-width:1450px){.app{grid-template-columns:360px minmax(520px,1fr)}.results{grid-column:1/-1;max-height:none}.brandPlate{width:188px}}
@media(max-width:850px){header{position:relative;flex-wrap:wrap}.productMeta{border-left:0;padding-left:0}.brandPlate{width:172px;height:48px}.brandTitle{font-size:17px}.brandSub{font-size:13px}.headerActions{width:100%}.headerActions button{flex:1}.app{display:block;height:auto}.contourTableWrap{max-height:70vh}.stage{height:600px}}


/* v2.6.0: the supplied plate already contains its frame and fasteners. Do not put a plate inside another plate, a surprisingly common triumph of UI archaeology. */
.brandPlate{width:286px;height:89px;padding:0;border:0;border-radius:14px;background:transparent;box-shadow:0 8px 24px #0008;overflow:hidden}
.brandPlate:before,.brandPlate:after{display:none}.brandPlate img{width:100%;height:100%;object-fit:contain;filter:none;display:block}
.aiFlow{border:1px solid #285b7c;border-radius:11px;padding:10px;background:linear-gradient(145deg,#0d2230,#0a1720);margin-top:9px}
.aiFlowTitle{display:flex;align-items:center;gap:7px;font-weight:750;margin-bottom:7px}.aiStatus{margin-top:7px;white-space:pre-wrap}.aiStatus.busy{color:#9ed5ff}.aiStatus.ok{color:#a9f0c8}.aiStatus.warn{color:#ffd88a}
@media(max-width:850px){.brandPlate{width:230px;height:71px}}


/* v2.7.0 Desktop Engineering Workspace */
:root{--v270-bg:#050d15;--v270-panel:#081827;--v270-border:#183d58;--v270-blue:#0875e8;--v270-muted:#8da4b7}
body{background:radial-gradient(circle at 70% -20%,#0b31552b,transparent 42%),#050d15}
header{height:92px;min-height:92px;padding:8px 26px;gap:24px;border-bottom-color:#18384f;background:linear-gradient(180deg,#07131f,#050d15)}
.brandPlate{width:270px;height:76px;border-radius:14px;box-shadow:0 10px 25px #0009}.brandText{min-width:225px}.brandTitle{font-size:27px}.brandSub{font-size:18px}
.productMeta{font-size:15px}.headerActions button{height:66px;min-width:105px;border-radius:10px}.headerActions #generateBtn{min-width:165px;background:linear-gradient(180deg,#197ef1,#0764d0)}
.app{height:calc(100vh - 92px);grid-template-columns:205px minmax(620px,1fr) minmax(560px,1.05fr);grid-template-rows:minmax(510px,1fr) minmax(280px,.48fr);gap:12px;padding:12px}
.app>aside.panel{grid-row:1/3;overflow:hidden;display:flex;flex-direction:column;border-radius:10px}
.moduleStrip{display:flex;flex-direction:column;gap:0;padding:0;overflow:auto;position:static;background:#071521}
.moduleStrip button{height:61px;border:0;border-bottom:1px solid #17344a;border-radius:0;text-align:left;padding:10px 14px;font-size:15px;background:transparent}
.moduleStrip button:before{display:inline-block;width:28px;font-size:20px}
.moduleStrip button:nth-child(1):before{content:"📄"}.moduleStrip button:nth-child(2):before{content:"🧾"}.moduleStrip button:nth-child(3):before{content:"⚙️"}.moduleStrip button:nth-child(4):before{content:"📍"}.moduleStrip button:nth-child(5):before{content:"🛠️"}
.moduleStrip button.active{background:linear-gradient(90deg,#0a5593,#0a2e4d);border-left:3px solid #20a4ff}
.app>aside.panel>.section{display:none}.app>aside.panel>.section.v270-active{display:block;overflow:auto}
.app>main.panel.canvasWrap{grid-column:3;grid-row:1;border-radius:10px}
.app>section.panel.results{grid-column:2/4;grid-row:2;border-radius:10px;display:grid;grid-template-columns:1fr;overflow:hidden}
.v270-contour-panel{grid-column:2;grid-row:1;display:flex!important;flex-direction:column;min-height:0}
.v270-contour-panel .contourTableWrap{max-height:none;flex:1;border-radius:0;border-left:0;border-right:0}
.v270-contour-panel .contourHeader{padding:12px 14px;margin:0;border-bottom:1px solid var(--line)}
.v270-contour-panel .contourActions{padding:10px 12px;margin:0}
.canvasWrap .stage{background-color:#06131f;background-image:linear-gradient(#17344a55 1px,transparent 1px),linear-gradient(90deg,#17344a55 1px,transparent 1px);background-size:20px 20px}
.canvasWrap .toolbar{min-height:51px}.canvasWrap .statusbar{min-height:54px}
.results .tabs{height:48px}.results .tab{height:calc(100% - 48px);overflow:auto}
#controllerGuide.active{display:grid;grid-template-columns:360px 1fr 310px;gap:12px;padding:12px}
#controllerGuide .resultCard{grid-column:1}#controllerGuide #guideWarning{grid-column:1/4;grid-row:2}
#controllerGuide #guideSteps{grid-column:2;grid-row:1}#controllerGuide .row{grid-column:3;grid-row:1;align-content:start}
#controllerGuide #guideText{display:none}
.v270-project-card{margin-top:auto;border-top:1px solid #17344a;padding:13px;color:#9eb0c0;font-size:12px;background:#06121d}
.v270-project-card b{color:#eaf4fd}.v270-project-card div{display:grid;grid-template-columns:55px 1fr;gap:6px;margin:7px 0}
.v270-sidebar-extra button{height:61px;width:100%;border:0;border-bottom:1px solid #17344a;border-radius:0;text-align:left;padding:10px 14px;background:transparent;font-size:15px}
.v270-sidebar-extra button:hover{background:#0b2d49}
@media(max-width:1200px){.app{grid-template-columns:180px 1fr;grid-template-rows:auto}.v270-contour-panel{grid-column:2}.app>main.panel.canvasWrap{grid-column:2;grid-row:2}.app>section.panel.results{grid-column:2;grid-row:3}.app>aside.panel{grid-row:1/4}}
@media(max-width:760px){header{height:auto}.app{display:block;height:auto}.app>aside.panel{display:block}.moduleStrip{flex-direction:row}.moduleStrip button{min-width:145px}.v270-contour-panel,.app>main.panel.canvasWrap,.app>section.panel.results{display:block!important;margin-bottom:10px}#controllerGuide.active{display:block}}

/* v3.0 AI Contour — dark liquid glass rebuild, intentionally without a logo */
:root{--bg:#02060b;--panel:rgba(13,22,34,.68);--panel2:rgba(19,31,47,.62);--line:rgba(143,190,255,.18);--text:#f5f8ff;--muted:#8d9bad;--accent:#1677ff;--violet:#713cff;--ok:#52e58d;--warn:#ffb931;--danger:#ff5a67}
html{background:#02060b}body{background:radial-gradient(circle at 18% -10%,rgba(36,103,255,.18),transparent 30%),radial-gradient(circle at 90% 10%,rgba(119,56,255,.12),transparent 28%),linear-gradient(180deg,#02060b,#050b13 55%,#02060b);min-height:100vh}
body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.015) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,black,transparent 80%)}
.iosHeader{height:82px;min-height:82px;padding:13px 18px;background:rgba(5,10,18,.66);backdrop-filter:blur(28px) saturate(155%);-webkit-backdrop-filter:blur(28px) saturate(155%);border-bottom:1px solid rgba(255,255,255,.09);box-shadow:0 12px 40px rgba(0,0,0,.28)}
.brandBlock{gap:13px}.brandPlate{display:none!important}.brandTitle{font-size:19px;letter-spacing:-.02em}.brandSub{font-size:12px;color:#9ca9ba;font-weight:500}.badge{background:linear-gradient(135deg,rgba(30,111,255,.25),rgba(123,55,255,.25))!important;border:1px solid rgba(115,164,255,.28);box-shadow:inset 0 1px rgba(255,255,255,.13)}
.flowSteps{display:flex;gap:6px;margin-left:20px}.flowSteps span{padding:8px 11px;border-radius:999px;color:#78879b;border:1px solid transparent;font-size:12px}.flowSteps span.active{color:#eaf3ff;background:rgba(22,119,255,.16);border-color:rgba(64,144,255,.32);box-shadow:0 0 22px rgba(22,119,255,.12)}
.headerActions button,button,input,select,textarea{border-radius:13px;border-color:rgba(151,190,255,.16);background:rgba(11,19,30,.68);box-shadow:inset 0 1px rgba(255,255,255,.055);transition:.18s ease}.headerActions button{height:50px;min-width:100px}.headerActions #generateBtn,button.primary{background:linear-gradient(135deg,#087cff,#6638ff);border-color:rgba(132,168,255,.44);box-shadow:0 10px 30px rgba(49,86,255,.26),inset 0 1px rgba(255,255,255,.22)}
button:hover{transform:translateY(-1px);border-color:rgba(99,164,255,.55);box-shadow:0 8px 24px rgba(0,0,0,.2)}
.app{height:calc(100vh - 82px);gap:12px;padding:12px;grid-template-columns:190px minmax(420px,520px) minmax(520px,1fr) minmax(360px,430px)}
.panel,.v270-contour-panel{background:linear-gradient(145deg,rgba(18,29,44,.78),rgba(7,13,22,.64));backdrop-filter:blur(25px) saturate(145%);-webkit-backdrop-filter:blur(25px) saturate(145%);border:1px solid rgba(151,190,255,.15);box-shadow:0 18px 55px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.045);border-radius:20px!important}
.app>aside.panel{background:rgba(5,11,19,.72)}.moduleStrip{background:transparent;border:0;padding:10px;gap:7px}.moduleStrip button{min-height:48px;text-align:left;background:transparent;border-color:transparent;color:#8b9aad}.moduleStrip button.active{background:linear-gradient(135deg,rgba(19,115,255,.22),rgba(103,53,255,.12));color:white;border-color:rgba(81,151,255,.25);box-shadow:inset 3px 0 #1683ff}
.section{border-bottom:1px solid rgba(151,190,255,.1);padding:14px}.section h2{font-size:13px;letter-spacing:.01em}.field label{color:#8392a6}.resultCard,.op,.guideStep,.aiFlow,.contourTableWrap{background:rgba(6,13,22,.56);border-color:rgba(151,190,255,.14);border-radius:16px}
.aiFlow{background:radial-gradient(circle at 18% 10%,rgba(33,119,255,.18),transparent 42%),linear-gradient(145deg,rgba(19,34,53,.72),rgba(8,15,25,.65));padding:14px}.aiFlowTitle{font-size:15px}.aiFlowTitle:before{content:"AI";display:grid;place-items:center;width:30px;height:30px;border-radius:10px;background:linear-gradient(135deg,#1683ff,#7b36ff);font-size:11px;box-shadow:0 0 24px rgba(79,84,255,.35)}
.canvasWrap{overflow:hidden}.toolbar{background:rgba(5,11,19,.56);backdrop-filter:blur(18px);border-color:rgba(151,190,255,.12);padding:10px}.stage{background:radial-gradient(circle at center,rgba(17,44,71,.3),transparent 55%),#03080e}.stage:after{content:"PDF / AI CONTOUR WORKSPACE";position:absolute;right:18px;bottom:16px;color:rgba(148,170,195,.18);font-size:11px;letter-spacing:.16em;pointer-events:none}.statusbar{background:rgba(5,11,19,.55);border-color:rgba(151,190,255,.11)}
.tabs{background:rgba(5,11,19,.66);backdrop-filter:blur(20px);border-color:rgba(151,190,255,.11);padding:9px}.tabs button.active{background:linear-gradient(135deg,rgba(22,119,255,.28),rgba(101,55,255,.18));border-color:rgba(80,146,255,.3)}
.contourTable th{background:rgba(20,35,54,.92)}.contourTable td{border-color:rgba(151,190,255,.09)}
/* coordinate language */
.contourTable td:nth-child(2),#contourStats .statPill:nth-child(1){color:#75f35f}.contourTable td:nth-child(3){color:#ff8c36}#guideText{color:#d8e5f7}pre{background:rgba(1,5,10,.72);border-color:rgba(151,190,255,.13)}
@media(max-width:1450px){.flowSteps{display:none}.app{grid-template-columns:180px 390px minmax(500px,1fr)}.app>section.panel.results{grid-column:2/4}}
@media(max-width:1000px){.app{display:block;height:auto}.iosHeader{height:auto;flex-wrap:wrap}.headerActions{width:100%}.headerActions button{flex:1}.panel{margin-bottom:12px}.moduleStrip{display:flex;overflow:auto}.moduleStrip button{min-width:150px}.stage{height:620px}}

</style>
</head>
<body>
<!-- legacy compatibility: v2.3.0 PRO | ROZFOOD | data:image/png;base64, (logo intentionally not rendered in v3.0) -->
<header class="iosHeader">
  <div class="brandBlock">
    <div class="brandText"><div class="brandTitle">CNC Assistant Client Pro</div><div class="brandSub">CAD · PDF · STEP · DXF · AI · Stock Removal</div></div>
    <span class="badge">v4.1 Universal Vision AI</span>
  </div>
  <div class="flowSteps" aria-label="Этапы работы"><span class="active">1 Файл</span><span>2 Геометрия</span><span>3 AI-анализ</span><span>4 Проверка</span><span>5 SINUMERIK</span></div>
  <div class="spacer"></div>
  <div class="headerActions"><button id="loadProjects">Проекты</button><button id="saveBtn">Сохранить</button><button id="generateBtn" class="primary">Проверить контур</button></div>
</header>
<div class="app">
<aside class="panel">
  <div class="moduleStrip"><button data-jump="project" class="active">Проект</button><button data-jump="pdf">PDF</button><button data-jump="geometry">Геометрия</button><button data-jump="contour">Контур</button><button data-jump="operations">Операции</button></div>
  <div class="section" id="module-project"><h2>📁 Проект</h2>
    <div class="field"><label>Название</label><input id="title" value="Деталь из PDF"></div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Telegram ID</label><input id="telegramId" inputmode="numeric"></div><div class="field"><label>ID станка</label><input id="machineId" inputmode="numeric"></div></div>
    <div class="field" style="margin-top:8px"><label>Стойка</label><select id="controller"><option>Siemens SINUMERIK 828D</option><option>Siemens SINUMERIK 840D</option><option>Fanuc 0i-TF</option><option>Haas NGC</option><option>Generic ISO</option></select></div>
  </div>
  <div class="section"><h2>🏭 Цифровой паспорт станка</h2>
    <div id="machineCard" class="resultCard small"><span class="muted">Профиль загрузится по Telegram ID и ID станка.</span></div>
    <div class="grid2"><div class="field"><label>Патрон Ø, мм</label><input id="chuckD" type="number" value="250"></div><div class="field"><label>Позиции револьвера</label><input id="turretCount" type="number" value="15" min="1" max="24"></div></div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Оси</label><input id="machineAxes" value="X/Z/Y/C"></div><div class="field"><label>Щуп</label><select id="probe"><option>Renishaw tool setter</option><option>Нет</option><option>Другой</option></select></div></div>
    <button id="openTurret" style="width:100%;margin-top:8px">🔩 Настроить револьвер T1–T15</button>
  </div>
  <div class="section"><h2>🧱 Фактическая заготовка</h2>
    <div class="grid2"><div class="field"><label>Наружный Ø, мм</label><input id="stockD" type="number" step="0.01" value="100"></div><div class="field"><label>Длина, мм</label><input id="stockL" type="number" step="0.01" value="80"></div></div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Отверстие Ø, мм</label><input id="stockId" type="number" step="0.01" value="0"></div><div class="field"><label>Макс. обороты</label><input id="maxRpm" type="number" value="3500"></div></div>
  </div>
  <div class="section"><h2>🧭 Тип обработки</h2>
    <div class="field"><label>Система координат и назначение контура</label><select id="workMode"><option value="turn">Токарный профиль X/Z</option><option value="mill">Фрезерный контур X/Y</option><option value="manual">Ручной универсальный</option></select></div>
    <div id="workModeInfo" class="small ok" style="margin-top:8px">Токарный режим: нужен продольный вид или разрез детали.</div>
  </div>
  <div class="section" id="module-pdf"><h2>📂 Импорт чертежа: STEP / DXF / PDF / фото / SolidWorks</h2>
    <div class="field"><input id="pdfFile" type="file" data-legacy-accept="application/pdf,image/png,image/jpeg,image/webp" accept=".pdf,.dxf,.step,.stp,.iges,.igs,.sldprt,.sldasm,.slddrw,.svg,.stl,image/png,image/jpeg,image/webp"></div>
    <div class="row" style="margin-top:7px"><input id="pdfPage" type="number" min="1" value="1" style="width:75px"><button id="uploadPdf">Загрузить страницу</button></div>
    <div class="row" style="margin-top:7px"><select id="profileType"><option value="outer">Наружный профиль</option><option value="inner">Внутренний профиль</option><option value="free">Произвольный контур</option></select><button id="selectRegion">▭ Выбрать область</button><button id="reanalyzeRegion">✨ Распознать область</button></div>
    <div class="row" style="margin-top:7px"><button id="rotatePdf">↻ Повернуть 90°</button><button id="clearRegion">Сбросить область</button></div>
    <div class="aiFlow"><div class="aiFlowTitle">🧪 Подготовка OpenCV → AI-контур</div><div class="small muted">OpenCV очищает только выбранную область. GPT получает подготовленное изображение, а не весь PDF.</div>
      <div class="opencvOptions" style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <label class="small"><input id="cvRemoveText" type="checkbox" checked> Удалить мелкий текст и стрелки</label>
        <label class="small"><input id="cvRemoveHatching" type="checkbox" checked> Подавить штриховку</label>
        <label class="small"><input id="cvStrengthen" type="checkbox" checked> Усилить линии</label>
        <label class="small"><input id="cvCloseGaps" type="checkbox" checked> Замкнуть разрывы</label>
      </div>
      <div class="row" style="margin-top:8px"><button id="opencvPreview">👁 Предпросмотр OpenCV</button><button id="opencvReset">Исходное изображение</button></div>
      <div id="opencvPreviewBox" style="display:none;margin-top:8px"><img id="opencvPreviewImage" alt="OpenCV preview" style="width:100%;max-height:280px;object-fit:contain;border:1px solid var(--line);border-radius:10px;background:#fff"><div id="opencvInfo" class="small muted" style="margin-top:5px"></div></div>
      <button id="aiBuildRegion" class="primary" style="width:100%;margin-top:8px">OpenCV → построить AI-контур</button><div id="aiRegionStatus" class="small aiStatus">Сначала проверьте предпросмотр. Перед стойкой контур всё равно подтверждает оператор.</div></div>
    <div id="pdfInfo" class="small muted" style="margin-top:7px">Файл не загружен.</div>
  </div>
  <div class="section" id="module-geometry"><h2>🧠 Инженерная геометрия • Drawing Intelligence</h2>
    <div class="field"><label>Шаблон</label><select id="geometryTemplate"><option value="tooth_section">Симметричный профиль зуба / кармана</option><option value="none">Без шаблона</option></select></div>
    <div class="row" style="margin-top:8px"><button id="recognizeDimensions">✨ Распознать размеры из PDF</button><span id="recognitionBadge" class="confidence" style="display:none"></span></div>
    <div id="dimensionReview" style="display:none;margin-top:8px">
      <div class="small muted" style="margin-bottom:6px">Распознанные значения — проверьте и исправьте перед построением.</div>
      <div style="border:1px solid var(--line);border-radius:9px;overflow:auto;max-height:260px">
        <table class="contourTable"><thead><tr><th>Параметр</th><th>Значение</th><th>Тип</th><th>Уверенность</th><th>Использовать</th></tr></thead><tbody id="dimensionReviewBody"></tbody></table>
      </div>
      <div class="row" style="margin-top:7px"><button id="applyRecognizedDimensions" class="good">✓ Подставить подтверждённые</button><button id="rejectRecognizedDimensions">Сбросить найденное</button></div>
    </div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Общая ширина, мм</label><input id="geoWidth" type="number" step="0.01" placeholder="из PDF"></div><div class="field"><label>Нижняя площадка, мм</label><input id="geoFlat" type="number" step="0.01" placeholder="из PDF"></div></div>
    <div class="grid3" style="margin-top:8px"><div class="field"><label>Высота, мм</label><input id="geoHeight" type="number" step="0.01" placeholder="из PDF"></div><div class="field"><label>Радиус R, мм</label><input id="geoRadius" type="number" step="0.01" placeholder="из PDF"></div><div class="field"><label>Угол, °</label><input id="geoAngle" type="number" step="0.1" placeholder="из PDF"></div></div>
    <div class="row" style="margin-top:8px"><button id="buildGeometry" class="good">Построить после проверки</button><button id="clearGeometry">Сбросить</button></div>
    <div id="geometryInfo" class="small muted" style="margin-top:7px">Ассистент заполняет размеры, оператор проверяет и редактирует.</div>
  </div>
  <div class="section"><h2>📟 Параметры Stock Removal</h2>
    <div class="grid2"><div class="field"><label>Ноль Z</label><select id="stockOriginZ"><option value="front">Z0 на торце</option><option value="back">Z0 сзади детали</option></select></div><div class="field"><label>Ввод X</label><select id="stockXMode"><option value="diameter">Диаметрный</option><option value="radius">Радиусный</option></select></div></div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Припуск X, мм</label><input id="allowX" type="number" step="0.01" value="0.3"></div><div class="field"><label>Припуск Z, мм</label><input id="allowZ" type="number" step="0.01" value="0.1"></div></div>
    <div class="grid2" style="margin-top:8px"><div class="field"><label>Контур</label><select id="contourClosure"><option value="open">Открытый</option><option value="closed">Закрытый</option></select></div><div class="field"><label>Обработка</label><select id="stockKind"><option value="outer">Наружная</option><option value="inner">Внутренняя</option></select></div></div>
    <label class="small" style="display:block;margin-top:8px"><input id="operatorConfirmed" type="checkbox"> Я проверил размеры, масштаб, X0/Z0 и направление осей</label>
    <button id="buildStockGuide" class="primary" style="width:100%;margin-top:8px">Показать ввод в SINUMERIK 828D</button>
    <div id="stockGuideStatus" class="small muted" style="margin-top:7px">Инструкция строится только после подтверждения оператора.</div>
  </div>
  <div class="section"><h2>📐 Масштаб и координаты</h2>
    <div class="field"><label>Известный размер между 2 точками, мм</label><input id="referenceMm" type="number" step="0.001" value="100"></div>
    <div class="row" style="margin-top:8px"><button data-mode="calibrate">1. Калибровать</button><button data-mode="origin">2. Задать X0/Z0</button></div>
    <label class="small"><input id="diameterMode" type="checkbox" checked> Высота от оси — радиус, X пересчитать ×2</label>
    <div id="scaleInfo" class="small muted" style="margin-top:6px">Масштаб не задан.</div>
  </div>
  <div class="section contourSection" id="module-contour"><div class="contourHeader"><h2>📍 Точки контура X/Z</h2><div id="contourStats" class="contourStats"><span class="statPill">Точек: 0</span></div></div>
    <div id="contourTableWrap" class="contourTableWrap">
      <table class="contourTable"><thead><tr><th>№</th><th>X</th><th>Z</th><th>Тип элемента</th><th>R / угол</th></tr></thead><tbody id="contourTableBody"><tr><td colspan="5" class="muted">Контур ещё не построен.</td></tr></tbody></table>
    </div>
    <textarea id="contourText" class="contourRaw" rows="6" placeholder="X70 Z0&#10;X70 Z-20&#10;X50 Z-25"></textarea>
    <div class="row contourActions"><button id="addContourRow">＋ Добавить точку</button><button id="applyContour">✓ Применить значения</button><button id="exportContour">↻ Обновить из рисунка</button></div>
  </div>
  <div class="section" id="module-operations"><h2>🧩 Операции</h2>
    <div class="row">
      <select id="newOp"><option value="turn_rough">Черновое точение</option><option value="turn_finish">Чистовое точение</option><option value="face">Торцевание</option><option value="bore_rough">Черновая расточка</option><option value="bore_finish">Чистовая расточка</option><option value="drill">Сверление</option><option value="groove">Канавка</option><option value="part">Отрезка</option><option value="thread_od">Наружная резьба</option><option value="thread_id">Внутренняя резьба</option><option value="mill">Фрезерование</option></select>
      <button id="addOp">➕</button>
    </div>
    <div id="operations" class="ops" style="margin-top:9px"></div>
  </div>
</aside>

<main class="panel canvasWrap">
  <div class="toolbar">
    <button data-mode="draw" class="active">✏️ Контур</button><button id="useAuto">✨ Автоконтур</button><button id="undo">↩ Отменить точку</button><button id="clearContour">🗑 Очистить</button>
    <button id="fit">⛶ Вписать</button><button id="togglePdf">👁 PDF</button>
    <span class="muted" style="align-self:center">Щёлкайте от торца Z0 вглубь детали.</span>
  </div>
  <div class="stage"><canvas id="canvas"></canvas></div>
  <div class="statusbar"><span id="cursor">X — / Z —</span><span id="pointCount">Точек: 0</span><span id="modeStatus">Режим: контур</span></div>
</main>

<section class="panel results">
  <div class="tabs"><button data-tab="preview" class="active">Графика</button><button data-tab="setup">Станок / револьвер</button><button data-tab="stock">Stock Removal</button><button data-tab="controllerGuide">Ввод в стойку</button><button data-tab="steps">По инструментам</button><button data-tab="gcode">G-код</button></div>
  <div id="preview" class="tab active"><div class="muted">Нажмите «Рассчитать», чтобы построить траектории и итоговую форму.</div><canvas id="resultCanvas" width="760" height="520" style="width:100%;margin-top:12px;background:#061018;border:1px solid var(--line);border-radius:10px"></canvas><div id="summary"></div></div>
  <div id="setup" class="tab"><div id="machineSetup"></div><h3>Револьвер на 15 позиций</h3><div id="turretGrid" class="toolList"></div><div class="warn">Проверяйте реальные габариты блоков, вылеты, ориентацию и безопасные позиции на станке.</div></div>
  <div id="stock" class="tab"></div>
  <div id="controllerGuide" class="tab">
    <div class="resultCard"><h3>📟 SINUMERIK 828D — Stock Removal</h3><div id="guideMeta" class="muted">Постройте и подтвердите контур.</div></div>
    <div id="guideWarning" class="dangerBox">Перед запуском обязательно проверьте контур в графической симуляции, без заготовки, с уменьшенным Rapid Override.</div>
    <div id="guideSteps" class="guideGrid"></div>
    <div class="row" style="margin-top:10px"><button id="copyGuide">📋 Копировать инструкцию</button><button id="downloadGuide">⬇ Скачать TXT</button></div>
    <pre id="guideText">Инструкция ещё не построена.</pre>
  </div>
  <div id="steps" class="tab"></div>
  <div id="gcode" class="tab"><div class="row"><button id="copyGcode">📋 Копировать</button><button id="downloadGcode">⬇ Скачать MPF</button></div><pre id="gcodeText">G-код ещё не рассчитан.</pre></div>
</section>
</div>

<div id="toolModal" class="modal"><div class="modalBox"><div class="row"><h2 style="margin:0;flex:1">🔩 Выбор инструмента из каталога</h2><button id="closeTools">✕</button></div><div class="grid3" style="margin:12px 0"><input id="toolSearch" placeholder="Маркировка или название"><select id="toolCategory"><option value="">Все категории</option><option value="turn_holder">Токарные державки</option><option value="boring_bar">Расточные державки</option><option value="turn_insert">Токарные пластины</option><option value="groove">Канавки / отрезка</option><option value="thread">Резьба</option><option value="drill">Сверла</option><option value="drill_insert">Пластины для корпусных сверл</option><option value="mill">Фрезы</option><option value="mill_insert">Фрезерные пластины</option><option value="holder">Оснастка</option></select><button id="searchTools">Найти</button></div><div id="toolList" class="toolList"></div></div></div>
<div id="turretModal" class="modal"><div class="modalBox"><div class="row"><h2 style="margin:0;flex:1">🔩 Револьвер станка</h2><button id="closeTurret">✕</button></div><div id="turretEditor" style="display:grid;gap:8px;margin-top:12px"></div><button id="saveTurret" class="primary" style="margin-top:12px">Сохранить конфигурацию</button></div></div>
<div id="projectModal" class="modal"><div class="modalBox"><div class="row"><h2 style="margin:0;flex:1">📂 Сохранённые проекты</h2><button id="closeProjects">✕</button></div><div id="projectList" style="display:grid;gap:8px;margin-top:12px"></div></div></div>
<script>
const OP_LABELS={face:'Торцевание',turn_rough:'Черновое точение',turn_finish:'Чистовое точение',bore_rough:'Черновая расточка',bore_finish:'Чистовая расточка',drill:'Сверление',groove:'Канавка',part:'Отрезка',thread_od:'Наружная резьба',thread_id:'Внутренняя резьба',mill:'Фрезерование'};
const DEFAULTS={face:[120,.18,1.5],turn_rough:[130,.25,2],turn_finish:[170,.10,.3],bore_rough:[100,.18,1],bore_finish:[140,.08,.25],drill:[70,.12,0],groove:[90,.08,0],part:[75,.06,0],thread_od:[45,1.5,0],thread_id:[35,1.5,0],mill:[120,300,1]};
const state={opencvPreview:null,aiRegion:null,workMode:'turn',geometryElements:[],recognizedDimensions:null,stockGuide:null,mode:'draw',pdfImage:null,pdfFile:null,pdfVisible:true,pdfCandidate:[],candidateConfidence:'low',dimensionEntities:[],cropRect:null,cropStart:null,regionApplied:false,pdfMeta:null,rotation:0,pointsPx:[],scalePxMm:null,origin:null,calibration:[],operations:[],result:null,view:{scale:1,ox:0,oy:0},activeOp:null,machine:null,turret:Array.from({length:15},(_,i)=>({station:i+1,tool:'',holder:'',insert:'',offset:'D1',live:false}))};
const $=id=>document.getElementById(id);const canvas=$('canvas'),ctx=canvas.getContext('2d');
document.querySelectorAll('[data-jump]').forEach(btn=>btn.onclick=()=>{document.querySelectorAll('[data-jump]').forEach(b=>b.classList.remove('active'));btn.classList.add('active');const el=$('module-'+btn.dataset.jump);if(el)el.scrollIntoView({behavior:'smooth',block:'start'})});

function resize(){const r=canvas.parentElement.getBoundingClientRect();canvas.width=Math.max(600,Math.floor(r.width*devicePixelRatio));canvas.height=Math.max(420,Math.floor(r.height*devicePixelRatio));ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);draw();}
addEventListener('resize',resize);setTimeout(resize,0);
function setMode(mode){state.mode=mode;document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));$('selectRegion').classList.toggle('active',mode==='crop');$('modeStatus').textContent='Режим: '+({draw:'контур',calibrate:'калибровка',origin:'начало координат',crop:'выбор области'}[mode]||mode);}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
function updateWorkMode(){state.workMode=$('workMode').value;const info={turn:'Токарный режим: выделяйте продольный вид или разрез. Круглый вид сверху будет отклонён.',mill:'Фрезерный режим X/Y: подходит для вида сверху, карманов и зубьев. Токарный Stock Removal и MPF отключены.',manual:'Ручной режим: точки задаются пользователем без автоматической классификации.'};$('workModeInfo').textContent=info[state.workMode];$('diameterMode').disabled=state.workMode==='mill';$('generateBtn').textContent=state.workMode==='mill'?'▶ Проверить XY':'▶ Рассчитать';draw()}
$('workMode').onchange=updateWorkMode;
function geometryPointsToPixels(points){ensureManualFrame();const px=[];if(state.workMode==='mill'){for(const p of points)px.push({x:state.origin.x+p.x*state.scalePxMm,y:state.origin.y-p.y*state.scalePxMm});}else{for(const p of points){const q=machineToPixel({z:p.x,x:p.y});if(q)px.push(q)}}return px}
function normalizeDimensionEntity(item,index){
  const raw=String(item.raw||item.value||'').trim();
  const value=Number(String(item.value??raw).replace(',','.').replace(/[^0-9.+-]/g,''));
  const kind=item.kind||(/^R/i.test(raw)?'radius':(/[°º]/.test(raw)?'angle':(/[Ø⌀]/.test(raw)?'diameter':'linear')));
  return {id:index,raw,value:Number.isFinite(value)?value:null,kind,confidence:Number(item.confidence??0.65),use:true};
}
function renderDimensionReview(){
  const box=$('dimensionReview'),body=$('dimensionReviewBody'),items=state.dimensionEntities||[];
  box.style.display=items.length?'block':'none';
  body.innerHTML=items.map((d,i)=>`<tr><td>${d.raw||'—'}</td><td><input data-dim-value="${i}" type="number" step="0.001" value="${d.value??''}"></td><td><select data-dim-kind="${i}"><option value="linear" ${d.kind==='linear'?'selected':''}>Линейный</option><option value="diameter" ${d.kind==='diameter'?'selected':''}>Диаметр</option><option value="radius" ${d.kind==='radius'?'selected':''}>Радиус</option><option value="angle" ${d.kind==='angle'?'selected':''}>Угол</option></select></td><td>${Math.round(d.confidence*100)}%</td><td><input data-dim-use="${i}" type="checkbox" ${d.use?'checked':''}></td></tr>`).join('');
}
function collectReviewedDimensions(){
  const items=state.dimensionEntities||[];
  items.forEach((d,i)=>{const v=document.querySelector(`[data-dim-value="${i}"]`),k=document.querySelector(`[data-dim-kind="${i}"]`),u=document.querySelector(`[data-dim-use="${i}"]`);if(v)d.value=Number(v.value);if(k)d.kind=k.value;if(u)d.use=u.checked});
  return items.filter(d=>d.use&&Number.isFinite(d.value));
}
$('recognizeDimensions').onclick=()=>{
  if(!state.pdfImage)return alert('Сначала загрузите PDF или фото и при необходимости выделите нужный вид.');
  if(!(state.dimensionEntities||[]).length){$('recognitionBadge').style.display='inline-block';$('recognitionBadge').textContent='значения не найдены';$('geometryInfo').innerHTML='<span class="warn">Текстовые размеры не найдены автоматически. Выделите область точнее или внесите значения вручную. Ассистент не будет выдумывать отсутствующие размеры.</span>';return}
  renderDimensionReview();$('recognitionBadge').style.display='inline-block';$('recognitionBadge').textContent=`найдено: ${state.dimensionEntities.length}`;
};
$('applyRecognizedDimensions').onclick=()=>{
  const dims=collectReviewedDimensions();
  const linear=dims.filter(d=>d.kind==='linear').sort((a,b)=>b.value-a.value), radius=dims.find(d=>d.kind==='radius'), angle=dims.find(d=>d.kind==='angle');
  if(linear[0])$('geoWidth').value=linear[0].value;if(linear[1])$('geoFlat').value=linear[1].value;if(linear[2])$('geoHeight').value=linear[2].value;if(radius)$('geoRadius').value=radius.value;if(angle)$('geoAngle').value=angle.value;
  state.recognizedDimensions=dims;$('geometryInfo').innerHTML=`<span class="ok">Подставлено ${dims.length} подтверждённых размеров. Проверьте назначение каждого поля и при необходимости исправьте.</span>`;
};
$('rejectRecognizedDimensions').onclick=()=>{state.dimensionEntities=[];renderDimensionReview();$('recognitionBadge').style.display='none'};
function guidePointText(p){return `X${Number(p.x).toFixed(3)} Z${Number(p.z).toFixed(3)}`}
function detectElement(a,b,i){
  const dx=b.x-a.x,dz=b.z-a.z;
  if(Math.abs(dx)<1e-6)return {type:'Прямая по Z',fields:`X = ${b.x.toFixed(3)}; Z = ${b.z.toFixed(3)}`};
  if(Math.abs(dz)<1e-6)return {type:'Прямая по X',fields:`X = ${b.x.toFixed(3)}; Z = ${b.z.toFixed(3)}`};
  const geo=state.geometryElements||[], blend=geo.find(g=>g.type==='blend');
  if(blend && (i===1 || i>Math.max(1,Math.floor(machinePoints().length*.7))))return {type:'Дуга / скругление',fields:`X = ${b.x.toFixed(3)}; Z = ${b.z.toFixed(3)}; R = ${Number(blend.radius||0).toFixed(3)}; направление проверить по графике`};
  return {type:'Наклонная прямая',fields:`X = ${b.x.toFixed(3)}; Z = ${b.z.toFixed(3)}`};
}
function buildStockGuide(){
  if(state.workMode!=='turn')return alert('Stock Removal доступен только для токарного профиля X/Z.');
  if(!$('operatorConfirmed').checked)return alert('Сначала подтвердите проверку размеров, масштаба и нуля детали.');
  const pts=machinePoints();if(pts.length<2)return alert('Нужно минимум две подтверждённые точки контура X/Z.');
  const xMode=$('stockXMode').value, origin=$('stockOriginZ').value, ax=+$('allowX').value||0,az=+$('allowZ').value||0;
  const converted=pts.map(p=>({x:xMode==='radius'?p.x/2:p.x,z:origin==='back'?p.z-(+$('stockL').value||0):p.z}));
  const steps=[
    {title:'Открыть цикл',body:'Program Manager → программа → Turning → Stock Removal.'},
    {title:'Создать контур',body:`New Contour. Имя: ${($('title').value||'KONTUR_1').replace(/\s+/g,'_').toUpperCase().slice(0,24)}.`},
    {title:'Проверить систему координат',body:`X: ${xMode==='diameter'?'диаметрный':'радиусный'} режим. ${origin==='front'?'Z0 на торце':'Z0 сзади детали'}. Обработка: ${$('stockKind').value==='outer'?'наружная':'внутренняя'}.`},
    {title:'Начальная точка',body:guidePointText(converted[0])+' → Accept.'}
  ];
  for(let i=1;i<converted.length;i++){const el=detectElement(converted[i-1],converted[i],i);steps.push({title:`Элемент ${i}: ${el.type}`,body:el.fields+' → Accept.'})}
  steps.push({title:'Закрыть и проверить',body:`Контур: ${$('contourClosure').value==='closed'?'закрытый':'открытый'}. Close contour → Graphic View. Припуск X=${ax.toFixed(3)} мм, Z=${az.toFixed(3)} мм.`});
  steps.push({title:'Безопасная проверка',body:'Запустить графическую симуляцию. Первый прогон — без заготовки, Single Block, Rapid Override уменьшен.'});
  state.stockGuide={steps,points:converted,meta:{xMode,origin,ax,az}};renderStockGuide();
}
function renderStockGuide(){
  const g=state.stockGuide;if(!g)return;
  $('guideMeta').innerHTML=`Точек: <b>${g.points.length}</b> · X: <b>${g.meta.xMode==='diameter'?'диаметр':'радиус'}</b> · припуск X/Z: <b>${g.meta.ax.toFixed(3)} / ${g.meta.az.toFixed(3)} мм</b>`;
  $('guideSteps').innerHTML=g.steps.map((s,i)=>`<div class="guideStep"><span class="num">${i+1}</span><b>${s.title}</b><div class="small" style="margin-top:7px">${s.body}</div></div>`).join('');
  const text=g.steps.map((s,i)=>`${i+1}. ${s.title}\n${s.body}`).join('\n\n');$('guideText').textContent=text;$('stockGuideStatus').textContent='Инструкция готова. Проверьте каждое значение на своей стойке.';
  document.querySelector('[data-tab="controllerGuide"]').click();
}
$('buildStockGuide').onclick=buildStockGuide;
$('copyGuide').onclick=()=>navigator.clipboard.writeText($('guideText').textContent);
$('downloadGuide').onclick=()=>{const blob=new Blob([$('guideText').textContent],{type:'text/plain;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='SINUMERIK_828D_Stock_Removal.txt';a.click();URL.revokeObjectURL(a.href)};
function buildToothGeometry(){const w=+$('geoWidth').value,f=+$('geoFlat').value,h=+$('geoHeight').value,r=+$('geoRadius').value,a=+$('geoAngle').value;if(!(w>0&&f>0&&h>0&&r>=0&&f<w))return alert('Проверьте размеры: общая ширина должна быть больше площадки.');const side=(w-f)/2,steps=8,pts=[];pts.push({x:-f/2,y:0});for(let i=1;i<=steps;i++){const t=i/steps;pts.push({x:-f/2-side*t,y:h*(1-Math.cos(t*Math.PI/2))})}for(let i=1;i<=steps;i++){const t=i/steps;pts.push({x:-w/2+w*t,y:h+Math.sin(t*Math.PI)*Math.min(r,h*.35)})}for(let i=1;i<=steps;i++){const t=i/steps;pts.push({x:w/2-side*t,y:h*Math.cos(t*Math.PI/2)})}pts.push({x:f/2,y:0},{x:-f/2,y:0});state.geometryElements=[{type:'line',name:'нижняя площадка',length:f},{type:'blend',name:'левый переход',radius:r,angle:a},{type:'arc',name:'верхняя дуга',span:w,height:h},{type:'blend',name:'правый переход',radius:r,angle:a}];state.pointsPx=geometryPointsToPixels(pts);$('geometryInfo').innerHTML=`<b>Построено:</b> площадка ${f} мм · ширина ${w} мм · высота ${h} мм · R${r} · ${a}°. Точек: ${pts.length}.`;syncContourText();draw()}
$('buildGeometry').onclick=buildToothGeometry;$('clearGeometry').onclick=()=>{state.geometryElements=[];state.pointsPx=[];$('geometryInfo').textContent='Геометрия сброшена.';syncContourText();draw()};
function imageToCanvas(px,py){if(!state.pdfImage)return[px,py];const cw=canvas.clientWidth,ch=canvas.clientHeight,iw=state.pdfImage.width,ih=state.pdfImage.height;const s=Math.min(cw/iw,ch/ih)*state.view.scale;const x=(cw-iw*s)/2+state.view.ox+px*s,y=(ch-ih*s)/2+state.view.oy+py*s;return[x,y];}
function canvasToImage(x,y){if(!state.pdfImage)return[x,y];const cw=canvas.clientWidth,ch=canvas.clientHeight,iw=state.pdfImage.width,ih=state.pdfImage.height;const s=Math.min(cw/iw,ch/ih)*state.view.scale;return[(x-(cw-iw*s)/2-state.view.ox)/s,(y-(ch-ih*s)/2-state.view.oy)/s];}
function pixelToMachine(p){if(!state.origin||!state.scalePxMm)return null;if(state.workMode==='mill')return{x:(p.x-state.origin.x)/state.scalePxMm,y:(state.origin.y-p.y)/state.scalePxMm};const mul=$('diameterMode').checked?2:1;return{z:(p.x-state.origin.x)/state.scalePxMm,x:Math.abs(p.y-state.origin.y)/state.scalePxMm*mul};}
function machinePoints(){return state.pointsPx.map(pixelToMachine).filter(Boolean).map(p=>state.workMode==='mill'?({x:+p.x.toFixed(4),y:+p.y.toFixed(4)}):({z:+p.z.toFixed(4),x:+p.x.toFixed(4)}));}
function machineToPixel(p){if(!state.origin||!state.scalePxMm)return null;const mul=$('diameterMode').checked?2:1;return{x:state.origin.x+p.z*state.scalePxMm,y:state.origin.y-(p.x/mul)*state.scalePxMm}}
function ensureManualFrame(){if(state.origin&&state.scalePxMm)return;const l=+$('stockL').value||100,d=+$('stockD').value||100;state.scalePxMm=Math.min(canvas.clientWidth*.7/l,canvas.clientHeight*.65/(d/2));state.origin={x:canvas.clientWidth*.85,y:canvas.clientHeight*.82};$('scaleInfo').textContent=`Ручной масштаб: ${state.scalePxMm.toFixed(4)} px/мм`;}
function inferContourElement(pts,i){
  if(i===0)return {type:'Начальная точка',extra:'—'};
  const a=pts[i-1],b=pts[i],dx=b.x-a.x,dz=(b.z??b.y)-(a.z??a.y);
  if(Math.abs(dx)<1e-5)return {type:'Прямая по Z',extra:'—'};
  if(Math.abs(dz)<1e-5)return {type:'Прямая по X',extra:'—'};
  const geo=(state.geometryElements||[]).find(g=>g.type==='blend');
  if(geo&&(i===1||i===pts.length-1))return {type:'Дуга / скругление',extra:'R'+Number(geo.radius||0).toFixed(3)};
  return {type:'Наклонная прямая',extra:'—'};
}
function renderContourTable(){
  const pts=machinePoints(),body=$('contourTableBody'),isMill=state.workMode==='mill';
  if(!body)return;
  if(!pts.length){body.innerHTML='<tr><td colspan="5" class="muted">Контур ещё не построен.</td></tr>';$('contourStats').innerHTML='<span class="statPill">Точек: 0</span>';return}
  body.innerHTML=pts.map((p,i)=>{const e=inferContourElement(pts,i),z=isMill?p.y:p.z;return `<tr data-index="${i}"><td>${i+1}</td><td><input data-axis="x" value="${Number(p.x).toFixed(3)}"></td><td><input data-axis="${isMill?'y':'z'}" value="${Number(z).toFixed(3)}"></td><td><select data-element><option${e.type==='Начальная точка'?' selected':''}>Начальная точка</option><option${e.type==='Прямая по X'?' selected':''}>Прямая по X</option><option${e.type==='Прямая по Z'?' selected':''}>Прямая по Z</option><option${e.type==='Наклонная прямая'?' selected':''}>Наклонная прямая</option><option${e.type==='Дуга / скругление'?' selected':''}>Дуга / скругление</option><option>Фаска</option></select></td><td><input data-extra value="${e.extra==='—'?'':e.extra}" placeholder="—"></td></tr>`}).join('');
  const types=pts.map((_,i)=>inferContourElement(pts,i).type),lines=types.filter(x=>x.includes('Прямая')).length,arcs=types.filter(x=>x.includes('Дуга')).length,facets=types.filter(x=>x==='Фаска').length;
  $('contourStats').innerHTML=`<span class="statPill">Точек: ${pts.length}</span><span class="statPill">Линий: ${lines}</span><span class="statPill">Дуг: ${arcs}</span><span class="statPill">Фасок: ${facets}</span>`;
  const wrap=$('contourTableWrap'),rowH=32,headH=36;wrap.style.height=Math.min(Math.max(214,headH+pts.length*rowH),Math.max(300,innerHeight-300))+'px';
}
function syncContourText(){const pts=machinePoints();$('contourText').value=pts.map(p=>state.workMode==='mill'?`X${p.x.toFixed(3)} Y${p.y.toFixed(3)}`:`X${p.x.toFixed(3)} Z${p.z.toFixed(3)}`).join('\n');renderContourTable()}
function draw(){const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);ctx.fillStyle='#061018';ctx.fillRect(0,0,w,h);
 if(state.pdfImage&&state.pdfVisible){const [x,y]=imageToCanvas(0,0),[x2,y2]=imageToCanvas(state.pdfImage.width,state.pdfImage.height);ctx.globalAlpha=.48;ctx.drawImage(state.pdfImage,x,y,x2-x,y2-y);ctx.globalAlpha=1;}
 drawGrid();drawStock();drawCandidate();drawCrop();drawCalibration();drawOrigin();drawContour();}
function drawGrid(){const w=canvas.clientWidth,h=canvas.clientHeight;ctx.strokeStyle='#122431';ctx.lineWidth=1;for(let x=0;x<w;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}for(let y=0;y<h;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}}
function drawStock(){if(!state.origin||!state.scalePxMm)return;const d=+($('stockD').value||0),l=+($('stockL').value||0),mul=$('diameterMode').checked?2:1;const top={x:state.origin.x,y:state.origin.y-(d/mul)*state.scalePxMm},end={x:state.origin.x-l*state.scalePxMm,y:state.origin.y};const [x0,y0]=imageToCanvas(top.x,top.y),[x1,y1]=imageToCanvas(end.x,state.origin.y);ctx.fillStyle='#46758a22';ctx.strokeStyle='#57b8d9';ctx.lineWidth=2;ctx.fillRect(x1,y0,x0-x1,y1-y0);ctx.strokeRect(x1,y0,x0-x1,y1-y0);}
function drawCandidate(){if(!state.pdfCandidate.length)return;ctx.strokeStyle='#ffc766';ctx.setLineDash([6,5]);ctx.beginPath();state.pdfCandidate.forEach((p,i)=>{const q=imageToCanvas(p.px,p.py);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke();ctx.setLineDash([])}

function drawCrop(){if(!state.cropRect)return;const a=imageToCanvas(state.cropRect.x,state.cropRect.y),b=imageToCanvas(state.cropRect.x+state.cropRect.w,state.cropRect.y+state.cropRect.h);ctx.fillStyle='#3b91e822';ctx.strokeStyle='#3b91e8';ctx.lineWidth=2;ctx.setLineDash([8,5]);ctx.fillRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);ctx.strokeRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);ctx.setLineDash([]);ctx.fillStyle='#a8d7ff';ctx.fillText('Область распознавания',a[0]+8,a[1]+18)}
function drawCalibration(){if(!state.calibration.length)return;ctx.fillStyle='#ffc766';state.calibration.forEach(p=>{const q=imageToCanvas(p.x,p.y);ctx.beginPath();ctx.arc(q[0],q[1],5,0,Math.PI*2);ctx.fill()});if(state.calibration.length===2){const a=imageToCanvas(state.calibration[0].x,state.calibration[0].y),b=imageToCanvas(state.calibration[1].x,state.calibration[1].y);ctx.strokeStyle='#ffc766';ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}}
function drawOrigin(){if(!state.origin)return;const q=imageToCanvas(state.origin.x,state.origin.y);ctx.strokeStyle='#49c987';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(q[0]-12,q[1]);ctx.lineTo(q[0]+12,q[1]);ctx.moveTo(q[0],q[1]-12);ctx.lineTo(q[0],q[1]+12);ctx.stroke();ctx.fillStyle='#49c987';ctx.fillText('X0/Z0',q[0]+8,q[1]-8)}
function drawContour(){if(!state.pointsPx.length)return;ctx.strokeStyle='#ff6d75';ctx.lineWidth=3;ctx.beginPath();state.pointsPx.forEach((p,i)=>{const q=imageToCanvas(p.x,p.y);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke();ctx.fillStyle='#ff9298';state.pointsPx.forEach((p,i)=>{const q=imageToCanvas(p.x,p.y);ctx.beginPath();ctx.arc(q[0],q[1],4,0,Math.PI*2);ctx.fill();ctx.fillText(String(i+1),q[0]+5,q[1]-5)});$('pointCount').textContent='Точек: '+state.pointsPx.length;renderContourTable();}
canvas.addEventListener('click',e=>{if(state.mode==='crop')return;const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,p=canvasToImage(x,y);const point={x:p[0],y:p[1]};if(state.mode==='draw'){state.pointsPx.push(point);syncContourText()}else if(state.mode==='origin'){state.origin=point;setMode('draw')}else if(state.mode==='calibrate'){state.calibration.push(point);if(state.calibration.length===2){const dx=state.calibration[1].x-state.calibration[0].x,dy=state.calibration[1].y-state.calibration[0].y,dist=Math.hypot(dx,dy),mm=+$('referenceMm').value;if(dist>0&&mm>0){state.scalePxMm=dist/mm;$('scaleInfo').textContent=`Масштаб: ${state.scalePxMm.toFixed(4)} px/мм`;setMode('origin')}else state.calibration=[]}}draw()});

canvas.addEventListener('pointerdown',e=>{if(state.mode!=='crop'||!state.pdfImage)return;canvas.setPointerCapture(e.pointerId);const r=canvas.getBoundingClientRect(),p=canvasToImage(e.clientX-r.left,e.clientY-r.top);state.cropStart={x:p[0],y:p[1]};state.cropRect={x:p[0],y:p[1],w:0,h:0};draw()});
canvas.addEventListener('pointermove',e=>{if(state.mode!=='crop'||!state.cropStart)return;const r=canvas.getBoundingClientRect(),p=canvasToImage(e.clientX-r.left,e.clientY-r.top);state.cropRect={x:Math.min(state.cropStart.x,p[0]),y:Math.min(state.cropStart.y,p[1]),w:Math.abs(p[0]-state.cropStart.x),h:Math.abs(p[1]-state.cropStart.y)};draw()});
canvas.addEventListener('pointerup',e=>{if(state.mode!=='crop'||!state.cropStart)return;state.cropStart=null;if(!state.cropRect||state.cropRect.w<12||state.cropRect.h<12){state.cropRect=null;alert('Выделите область побольше.')}else{$('pdfInfo').textContent='Область выбрана. Нажмите «Распознать область».'}draw()});
canvas.addEventListener('mousemove',e=>{const r=canvas.getBoundingClientRect(),p=canvasToImage(e.clientX-r.left,e.clientY-r.top),m=pixelToMachine({x:p[0],y:p[1]});$('cursor').textContent=m?(state.workMode==='mill'?`X ${m.x.toFixed(3)} / Y ${m.y.toFixed(3)}`:`X ${m.x.toFixed(3)} / Z ${m.z.toFixed(3)}`):'X — / Z —'});
$('undo').onclick=()=>{state.pointsPx.pop();syncContourText();draw()};$('clearContour').onclick=()=>{if(confirm('Очистить точки контура?')){state.pointsPx=[];syncContourText();draw()}};$('fit').onclick=()=>{state.view={scale:1,ox:0,oy:0};draw()};$('togglePdf').onclick=()=>{state.pdfVisible=!state.pdfVisible;draw()};$('useAuto').onclick=()=>{if(!state.pdfCandidate.length)return alert('Автоконтур не найден. Выделите нужный продольный вид или используйте AI-контур.');if(state.candidateConfidence!=='high')return alert('Автоконтур не применён: проверка качества не пройдена. Это лучше, чем уверенно принять размерную стрелку за деталь. Используйте AI-контур или обведите профиль вручную.');state.pointsPx=state.pdfCandidate.map(p=>({x:p.px,y:p.py}));syncContourText();draw()};
['stockD','stockL','diameterMode'].forEach(id=>$(id).oninput=draw);
$('exportContour').onclick=syncContourText;
$('addContourRow').onclick=()=>{
  const pts=machinePoints(),last=pts[pts.length-1]||{x:0,z:0};pts.push({...last});
  ensureManualFrame();state.pointsPx=pts.map(machineToPixel).filter(Boolean);syncContourText();draw();
};
$('applyContour').onclick=()=>{
  const rows=[...document.querySelectorAll('#contourTableBody tr[data-index]')],pts=[];
  for(const row of rows){const x=Number(row.querySelector('[data-axis="x"]').value.replace(',','.')),zEl=row.querySelector('[data-axis="z"],[data-axis="y"]'),z=Number(zEl.value.replace(',','.'));if(Number.isFinite(x)&&Number.isFinite(z))pts.push({x,z})}
  if(pts.length<2)return alert('Нужно минимум две подтверждённые точки контура.');
  ensureManualFrame();state.pointsPx=pts.map(machineToPixel).filter(Boolean);syncContourText();draw();
};


function selectedRegionBlob(){
  return new Promise((resolve,reject)=>{
    if(!state.pdfImage)return reject(new Error('Сначала загрузите PDF или фото.'));
    let r=state.cropRect;
    if(!r&&state.regionApplied)r={x:0,y:0,w:state.pdfImage.width,h:state.pdfImage.height};
    if(!r)return reject(new Error('Нажмите «Выбрать область» и обведите нужный продольный профиль.'));
    const img=state.pdfImage;
    const x=Math.max(0,Math.min(img.width-1,Math.round(r.x))),y=Math.max(0,Math.min(img.height-1,Math.round(r.y)));
    const w=Math.max(2,Math.min(img.width-x,Math.round(r.w))),h=Math.max(2,Math.min(img.height-y,Math.round(r.h)));
    const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,w,h);g.drawImage(img,x,y,w,h,0,0,w,h);
    c.toBlob(blob=>blob?resolve(blob):reject(new Error('Не удалось подготовить выбранную область.')),'image/png',0.96);
  });
}
function appendCvOptions(fd){
  fd.append('use_opencv','true');
  fd.append('remove_text',$('cvRemoveText').checked?'true':'false');
  fd.append('remove_hatching',$('cvRemoveHatching').checked?'true':'false');
  fd.append('strengthen_lines',$('cvStrengthen').checked?'true':'false');
  fd.append('close_gaps',$('cvCloseGaps').checked?'true':'false');
}
async function previewOpenCv(){
  const box=$('opencvPreviewBox'),info=$('opencvInfo');
  try{
    const blob=await selectedRegionBlob();
    info.textContent='OpenCV обрабатывает выбранную область…';box.style.display='block';$('opencvPreview').disabled=true;
    const fd=new FormData();fd.append('image',blob,'drawing-region.png');fd.append('telegram_id',$('telegramId').value||0);appendCvOptions(fd);
    const res=await fetch('/api/v1/client/opencv/preview',{method:'POST',body:fd});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Ошибка OpenCV');
    state.opencvPreview=data;$('opencvPreviewImage').src=data.comparison_image_data_url;
    const d=data.diagnostics||{};info.textContent=`Слева исходник, справа то, что увидит GPT. Удалено мелких компонентов: ${d.removed_small_components||0}; пикселей штриховки: ${d.removed_hatch_pixels||0}.`;
  }catch(err){box.style.display='block';info.textContent='Ошибка: '+err.message}finally{$('opencvPreview').disabled=false}
}
$('opencvPreview').onclick=previewOpenCv;
$('opencvReset').onclick=()=>{state.opencvPreview=null;$('opencvPreviewBox').style.display='none';$('opencvPreviewImage').removeAttribute('src');$('opencvInfo').textContent=''};
['cvRemoveText','cvRemoveHatching','cvStrengthen','cvCloseGaps'].forEach(id=>$(id).onchange=()=>{state.opencvPreview=null;$('opencvInfo').textContent='Настройки изменены. Обновите предпросмотр.'});

async function buildAiRegion(){
  const status=$('aiRegionStatus');
  if(state.workMode!=='turn')return alert('AI Stock Removal сейчас предназначен для токарного профиля X/Z.');
  try{
    const blob=await selectedRegionBlob();status.className='small aiStatus busy';status.textContent='GPT проверяет тип вида, сравнивает исходник с OpenCV и строит X/Z…';$('aiBuildRegion').disabled=true;
    const fd=new FormData();fd.append('image',blob,'drawing-region.png');fd.append('telegram_id',$('telegramId').value||0);fd.append('profile_type',$('profileType').value);fd.append('x_mode',$('stockXMode').value);appendCvOptions(fd);
    const res=await fetch('/api/v1/client/ai/region',{method:'POST',body:fd});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Ошибка AI-анализа');
    const pts=Array.isArray(data.contour_xz_mm)?data.contour_xz_mm:[];if(pts.length<2)throw new Error('AI не вернул достаточный контур.');
    if(data.stock_diameter_mm)$('stockD').value=data.stock_diameter_mm;if(data.stock_length_mm)$('stockL').value=data.stock_length_mm;
    state.scalePxMm=null;state.origin=null;ensureManualFrame();state.pointsPx=pts.map(p=>machineToPixel({x:Number(p.x),z:Number(p.z)})).filter(Boolean);state.aiRegion=data;state.candidateConfidence=data.confidence||'low';
    state.dimensionEntities=(data.dimensions||[]).map(normalizeDimensionEntity);renderDimensionReview();syncContourText();draw();$('operatorConfirmed').checked=false;
    const issues=[...(data.warnings||[]),...(data.questions||[]).map(q=>'Нужно уточнить: '+q)];
    status.className='small aiStatus '+(data.confidence==='high'?'ok':'warn');const cv=data.opencv_diagnostics||{},gv=data.geometry_validation||{};status.textContent=`Вид: ${data.view_type||'не определён'}. Точек: ${pts.length}. Уверенность: ${data.confidence||'low'}. Геометрия: ${gv.valid?'PASS':'CHECK'}. OpenCV удалил ${cv.removed_small_components||0} элементов. ${data.summary||''}${issues.length?'\n'+issues.join('\n'):''}`;
    $('stockGuideStatus').textContent='AI-контур построен. Проверьте таблицу X/Z, размеры и ноль, затем поставьте галочку подтверждения.';
    $('module-contour').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(err){status.className='small aiStatus warn';status.textContent='Ошибка: '+err.message;}finally{$('aiBuildRegion').disabled=false}
}
$('aiBuildRegion').onclick=buildAiRegion;

async function analyzePdf(useCrop=false){
  const file=state.pdfFile||$('pdfFile').files[0];if(!file)return alert('Выберите PDF.');
  state.pdfFile=file;
  const fd=new FormData();fd.append('file',file);fd.append('page_number',$('pdfPage').value||1);fd.append('telegram_id',$('telegramId').value||0);fd.append('rotation',state.rotation);fd.append('profile_type',$('profileType').value);
  if(useCrop){
    if(!state.cropRect||!state.pdfImage)return alert('Сначала нажмите «Выбрать область» и обведите нужный боковой вид.');
    fd.append('crop_x',state.cropRect.x/state.pdfImage.width);fd.append('crop_y',state.cropRect.y/state.pdfImage.height);fd.append('crop_w',state.cropRect.w/state.pdfImage.width);fd.append('crop_h',state.cropRect.h/state.pdfImage.height);
  }
  $('pdfInfo').textContent=useCrop?'Распознавание выбранной области…':'Обработка PDF…';
  try{
    const ext=(file.name.split('.').pop()||'').toLowerCase();const classic=['pdf','png','jpg','jpeg','webp'].includes(ext);const endpoint=classic?'/api/v1/client/pdf/analyze':'/api/v1/client/drawing/import';const res=await fetch(endpoint,{method:'POST',body:fd});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Ошибка импорта');if(!classic){$('pdfInfo').innerHTML=`Формат: <b>${data.detected_format}</b> · маршрут: <b>${data.route}</b> · точность: <b>${data.precision}</b><br>${data.analysis?.message||'Геометрия импортирована.'}`;state.pdfMeta=data;return;}
    const img=new Image();
    img.onload=()=>{
      state.pdfImage=img;state.pdfMeta=data;state.pdfCandidate=data.candidate_pixels||[];state.candidateConfidence=data.candidate_confidence||'low';
      state.dimensionEntities=(data.dimension_entities||data.dimension_hints||[]).map(normalizeDimensionEntity);renderDimensionReview();
      state.regionApplied=Boolean(data.crop_applied);
      state.cropRect=state.regionApplied?{x:0,y:0,w:img.width,h:img.height}:null;
      if(state.regionApplied)setMode('draw');
      state.view={scale:1,ox:0,oy:0};
      const conf=data.candidate_confidence||'low',diag=data.autocontour_diagnostics||{};
      const quality=diag.quality_reason?` · ${diag.quality_reason}`:'';
      $('pdfInfo').innerHTML=`Страница ${data.page}/${data.page_count}; автоконтур: <b>${conf}</b>${data.crop_applied?' · выбранная область закреплена':''}; поворот: ${data.rotation}°; размеры: ${(data.dimension_entities||data.dimension_hints||[]).slice(0,12).map(x=>x.raw||x).join(', ')||'нет'}${quality}`;
      if(!state.pdfCandidate.length&&useCrop)$('pdfInfo').innerHTML+='<div class="warn">Автоконтур отклонён проверкой качества. Выбранная область сохранена и готова для кнопки «AI-контур».</div>';
      draw();
    };
    img.src=data.image_data_url;
  }catch(err){$('pdfInfo').textContent='Ошибка: '+err.message}
}
$('uploadPdf').onclick=()=>{state.rotation=0;state.cropRect=null;state.regionApplied=false;state.pdfMeta=null;analyzePdf(false)};
$('selectRegion').onclick=()=>{if(!state.pdfImage)return alert('Сначала загрузите PDF.');if(state.regionApplied)return alert('Сейчас показана уже вырезанная область. Нажмите «Вернуть страницу», затем выберите новую область.');setMode('crop')};
$('reanalyzeRegion').onclick=()=>{if(state.regionApplied)return alert('Выбранная область уже распознана и закреплена. Нажмите «AI-контур» или «Вернуть страницу».');analyzePdf(true)};
$('clearRegion').onclick=()=>{state.cropRect=null;state.regionApplied=false;state.pdfMeta=null;setMode('draw');if(state.pdfFile)analyzePdf(false);else draw()};
$('rotatePdf').onclick=()=>{state.rotation=(state.rotation+90)%360;state.cropRect=null;state.regionApplied=false;state.pdfMeta=null;analyzePdf(false)};
function addOperation(type){const d=DEFAULTS[type]||[100,.15,1];state.operations.push({id:crypto.randomUUID(),type,tool_no:state.operations.length+1,tool:{code:'НЕ ЗАДАН',name:'Выберите из каталога'},params:{vc:d[0],feed:d[1],ap:d[2],allow_x:type.includes('rough')?.5:0,allow_z:type.includes('rough')?.2:0}});renderOperations()}
$('addOp').onclick=()=>addOperation($('newOp').value);
function renderOperations(){$('operations').innerHTML='';state.operations.forEach((op,index)=>{const el=document.createElement('div');el.className='op';el.innerHTML=`<div class="opHead"><strong>${index+1}. ${OP_LABELS[op.type]}</strong><button data-tool>🔩 Каталог</button><button data-remove class="danger">✕</button></div><div class="opGrid"><label class="field"><span>Т №</span><input data-k="tool_no" value="${op.tool_no}"></label><label class="field"><span>Vc м/мин</span><input data-p="vc" value="${op.params.vc}"></label><label class="field"><span>F</span><input data-p="feed" value="${op.params.feed}"></label><label class="field"><span>ap рад., мм</span><input data-p="ap" value="${op.params.ap}"></label><label class="field"><span>Припуск X Ø</span><input data-p="allow_x" value="${op.params.allow_x||0}"></label><label class="field"><span>Припуск Z</span><input data-p="allow_z" value="${op.params.allow_z||0}"></label></div><div class="toolResult"><b>${op.tool.code}</b> — ${op.tool.name}</div>`;el.querySelector('[data-remove]').onclick=()=>{state.operations.splice(index,1);renderOperations()};el.querySelector('[data-tool]').onclick=()=>openTools(index);el.querySelectorAll('[data-p]').forEach(inp=>inp.oninput=()=>op.params[inp.dataset.p]=+inp.value);el.querySelector('[data-k]').oninput=e=>op.tool_no=+e.target.value;$('operations').appendChild(el)});}
let toolTarget=null;function openTools(index){toolTarget=index;$('toolModal').classList.add('open');searchTools()}$('closeTools').onclick=()=>$('toolModal').classList.remove('open');$('searchTools').onclick=searchTools;
async function searchTools(){const q=encodeURIComponent($('toolSearch').value),cat=encodeURIComponent($('toolCategory').value);$('toolList').textContent='Загрузка…';try{const res=await fetch(`/api/v1/tools?limit=50&q=${q}&category=${cat}`);const data=await res.json();$('toolList').innerHTML='';data.forEach(item=>{const el=document.createElement('div');el.className='toolItem';el.innerHTML=`<b>${item.code}</b><br>${item.name}<div class="small muted">${item.dimensions||''}</div><div class="small muted">${item.compatibility||''}</div><div class="small muted">${item.source||''}</div>`;el.onclick=()=>{state.operations[toolTarget].tool=item;$('toolModal').classList.remove('open');renderOperations()};$('toolList').appendChild(el)});if(!data.length)$('toolList').textContent='Ничего не найдено.'}catch(e){$('toolList').textContent='Ошибка каталога: '+e.message}}
function collectPayload(){const points=machinePoints();return{telegram_id:+$('telegramId').value||0,machine_id:+$('machineId').value||0,title:$('title').value,machine:{controller:$('controller').value,max_rpm:+$('maxRpm').value||0,axes:$('machineAxes').value,chuck_diameter:+$('chuckD').value||0,turret_count:+$('turretCount').value||15,probe:$('probe').value,driven_tools:state.machine?.driven_tools||false,turret:state.turret},stock:{outer_diameter:+$('stockD').value,inner_diameter:+$('stockId').value||0,length:+$('stockL').value},contour:{mode:state.workMode==='mill'?'xy':$('profileType').value,points,geometry_elements:state.geometryElements},operations:state.operations.map(op=>({...op,tool_no:op.tool_no}))}}
$('generateBtn').onclick=async()=>{const payload=collectPayload();if(payload.contour.points.length<2)return alert('Нужно минимум две точки контура.');if(state.workMode==='mill')return alert('Контур X/Y построен и проверен. Генератор фрезерного G-кода будет отдельным модулем; токарный MPF не создаётся.');if(!payload.operations.length)return alert('Добавьте операции.');$('generateBtn').disabled=true;$('generateBtn').textContent='Расчёт…';try{const res=await fetch('/api/v1/client/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Ошибка расчёта');state.result=data;renderResult()}catch(e){alert(e.message)}finally{$('generateBtn').disabled=false;$('generateBtn').textContent='▶ Рассчитать'}};
function renderResult(){const r=state.result;$('summary').innerHTML=`<div class="ok">Операций: ${r.summary.operations}; инструментов: ${r.summary.tools}; проходов: ${r.summary.passes}</div>`+(r.warnings||[]).map(w=>`<div class="warn">⚠ ${w}</div>`).join('');$('gcodeText').textContent=r.gcode;renderStock(r);renderSteps(r);drawResult(r)}
function renderStock(r){$('stock').innerHTML=(r.stock_removal||[]).map((card,i)=>`<div class="resultCard"><h3>${i+1}. ${card.operation}</h3><div><b>${card.tool}</b></div><div class="small muted">${card.screen}</div><div class="kv" style="margin-top:9px">${Object.entries(card.fields).map(([k,v])=>`<div>${k}</div><div>${v}</div>`).join('')}</div><h3 style="margin-top:12px">Точки контура X/Z</h3><pre>${card.contour_points.map(p=>`X${p.x.toFixed(3)} Z${p.z.toFixed(3)}`).join('\n')}</pre>${card.notes.map(n=>`<div class="warn">${n}</div>`).join('')}</div>`).join('')||'<div class="muted">Добавьте операцию чернового точения или расточки.</div>'}
function renderSteps(r){$('steps').innerHTML=(r.steps||[]).map(s=>`<div class="resultCard"><h3>${s.number}. ${s.title}</h3><div><b>T${s.tool.tool_no}: ${s.tool.code}</b> — ${s.tool.name}</div><div class="kv" style="margin-top:9px">${Object.entries(s.settings).map(([k,v])=>`<div>${k}</div><div>${v}</div>`).join('')}</div><ol>${s.instructions.map(i=>`<li>${i}</li>`).join('')}</ol></div>`).join('')}
function drawResult(r){const c=$('resultCanvas'),x=c.getContext('2d'),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.fillStyle='#061018';x.fillRect(0,0,w,h);const all=[...(r.final_contour||[])];(r.toolpaths||[]).forEach(p=>all.push(...p.points));if(!all.length)return;const minZ=Math.min(...all.map(p=>p.z)),maxZ=Math.max(...all.map(p=>p.z)),maxX=Math.max(r.stock.outer_diameter,...all.map(p=>p.x)),pad=45,sx=(w-2*pad)/Math.max(1,maxZ-minZ),sy=(h-2*pad)/Math.max(1,maxX),tx=z=>pad+(z-minZ)*sx,ty=v=>h-pad-v*sy;x.strokeStyle='#294154';for(let i=0;i<10;i++){const yy=pad+i*(h-2*pad)/9;x.beginPath();x.moveTo(pad,yy);x.lineTo(w-pad,yy);x.stroke()}x.fillStyle='#46758a22';x.strokeStyle='#57b8d9';x.fillRect(tx(minZ),ty(r.stock.outer_diameter),tx(maxZ)-tx(minZ),ty(0)-ty(r.stock.outer_diameter));x.strokeRect(tx(minZ),ty(r.stock.outer_diameter),tx(maxZ)-tx(minZ),ty(0)-ty(r.stock.outer_diameter));(r.toolpaths||[]).forEach((path,i)=>{x.strokeStyle=`hsl(${(i*47)%360} 75% 62%)`;x.lineWidth=1.5;x.beginPath();path.points.forEach((p,j)=>j?x.lineTo(tx(p.z),ty(p.x)):x.moveTo(tx(p.z),ty(p.x)));x.stroke()});x.strokeStyle='#ff6d75';x.lineWidth=4;x.beginPath();r.final_contour.forEach((p,j)=>j?x.lineTo(tx(p.z),ty(p.x)):x.moveTo(tx(p.z),ty(p.x)));x.stroke();x.fillStyle='#dbeaf5';x.fillText('Z, мм',w/2,h-10);x.save();x.translate(14,h/2);x.rotate(-Math.PI/2);x.fillText('X (диаметр), мм',0,0);x.restore()}
$('copyGcode').onclick=()=>navigator.clipboard.writeText($('gcodeText').textContent);$('downloadGcode').onclick=()=>{if(!state.result)return;const blob=new Blob([state.result.gcode],{type:'text/plain'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=($('title').value||'cnc_project').replace(/[^\wа-яА-Я-]+/g,'_')+'.mpf';a.click();URL.revokeObjectURL(a.href)};
$('saveBtn').onclick=async()=>{const payload=collectPayload();try{const res=await fetch('/api/v1/client/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({telegram_id:payload.telegram_id,machine_id:payload.machine_id,title:payload.title,payload,generated:state.result})});const d=await res.json();if(!res.ok)throw new Error(d.detail||'Ошибка');alert('Проект сохранён: #'+d.id)}catch(e){alert(e.message)}};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.id===b.dataset.tab))});
$('closeProjects').onclick=()=>$('projectModal').classList.remove('open');$('loadProjects').onclick=async()=>{const tid=+$('telegramId').value,mid=+$('machineId').value;if(!tid||!mid)return alert('Укажите Telegram ID и ID станка.');$('projectModal').classList.add('open');$('projectList').textContent='Загрузка…';try{const res=await fetch(`/api/v1/users/${tid}/machines/${mid}/client-projects`),items=await res.json();if(!res.ok)throw new Error(items.detail||'Ошибка');$('projectList').innerHTML='';items.forEach(item=>{const el=document.createElement('button');el.style.textAlign='left';el.innerHTML=`<b>#${item.id} — ${item.title}</b><br><span class="muted">${new Date(item.updated_at).toLocaleString()}</span>`;el.onclick=()=>loadProject(item);$('projectList').appendChild(el)});if(!items.length)$('projectList').textContent='Сохранённых проектов нет.'}catch(e){$('projectList').textContent=e.message}};function loadProject(item){const p=item.payload||{};$('title').value=p.title||item.title;$('stockD').value=p.stock?.outer_diameter||100;$('stockId').value=p.stock?.inner_diameter||0;$('stockL').value=p.stock?.length||80;$('controller').value=p.machine?.controller||$('controller').value;$('maxRpm').value=p.machine?.max_rpm||3500;state.operations=p.operations||[];renderOperations();state.pdfImage=null;state.origin=null;state.scalePxMm=null;ensureManualFrame();state.pointsPx=(p.contour?.points||[]).map(machineToPixel).filter(Boolean);state.result=item.generated||null;syncContourText();draw();if(state.result)renderResult();$('projectModal').classList.remove('open')}

function renderMachine(){const m=state.machine||{};$('machineCard').innerHTML=`<b>${m.name||'Tengyue CK52PT-Y'}</b><br>${m.machine_type||'Токарно-фрезерный'} · ${m.controller?.manufacturer?.name||'Siemens'} ${m.controller?.name||'SINUMERIK 828D'}<br>Оси: <b>${m.axes||$('machineAxes').value}</b> · приводной инструмент: <b>${m.driven_tools?'да':'по профилю'}</b> · макс. об/мин: <b>${m.max_rpm||$('maxRpm').value}</b>`;$('machineSetup').innerHTML=`<div class="resultCard"><h3>Цифровой двойник — конфигурация</h3><div class="kv"><div>Станок</div><div>${m.name||'Tengyue CK52PT-Y'}</div><div>Стойка</div><div>${m.controller?.name||$('controller').value}</div><div>Оси</div><div>${$('machineAxes').value}</div><div>Патрон</div><div>Ø${$('chuckD').value} мм</div><div>Револьвер</div><div>${$('turretCount').value} позиций</div><div>Щуп</div><div>${$('probe').value}</div></div></div>`;renderTurretGrid()}
function renderTurretGrid(){if(!$('turretGrid'))return;$('turretGrid').innerHTML=state.turret.map(t=>`<div class="toolItem"><b>T${t.station}</b> · ${t.tool||'свободно'}<br><span class="small muted">${t.holder||'державка не задана'} ${t.insert?'· '+t.insert:''} · ${t.offset}${t.live?' · приводной':''}</span></div>`).join('')}
function openTurretEditor(){$('turretEditor').innerHTML=state.turret.map((t,i)=>`<div class="op"><div class="opHead"><strong>T${t.station}</strong><label class="small"><input type="checkbox" data-live="${i}" ${t.live?'checked':''}> приводной</label></div><div class="grid3"><input data-tool="${i}" placeholder="Инструмент" value="${t.tool}"><input data-holder="${i}" placeholder="Державка / блок" value="${t.holder}"><input data-insert="${i}" placeholder="Пластина / фреза / сверло" value="${t.insert}"></div></div>`).join('');$('turretModal').classList.add('open')}
$('openTurret').onclick=openTurretEditor;$('closeTurret').onclick=()=>$('turretModal').classList.remove('open');$('saveTurret').onclick=()=>{state.turret.forEach((t,i)=>{t.tool=document.querySelector(`[data-tool="${i}"]`).value;t.holder=document.querySelector(`[data-holder="${i}"]`).value;t.insert=document.querySelector(`[data-insert="${i}"]`).value;t.live=document.querySelector(`[data-live="${i}"]`).checked});localStorage.setItem('cncTurret',JSON.stringify(state.turret));$('turretModal').classList.remove('open');renderMachine()};
async function loadMachineProfile(){const tid=+$('telegramId').value,mid=+$('machineId').value;if(!tid||!mid){renderMachine();return}try{const r=await fetch(`/api/v1/users/${tid}/machines/${mid}`),m=await r.json();if(!r.ok)throw new Error(m.detail||'Ошибка профиля');state.machine=m;$('machineAxes').value=m.axes||'X/Z/Y/C';if(m.max_rpm)$('maxRpm').value=m.max_rpm;if(m.controller?.name)$('controller').value=[...$('controller').options].some(o=>o.value.includes(m.controller.name))?[...$('controller').options].find(o=>o.value.includes(m.controller.name)).value:$('controller').value;renderMachine()}catch(e){$('machineCard').innerHTML=`<span class="danger">Профиль не загружен: ${e.message}</span>`;renderMachine()}}
['chuckD','turretCount','machineAxes','probe','maxRpm'].forEach(id=>$(id).oninput=renderMachine);
try{const saved=JSON.parse(localStorage.getItem('cncTurret')||'null');if(Array.isArray(saved)&&saved.length)state.turret=saved}catch(e){}
const qs=new URLSearchParams(location.search);$('telegramId').value=qs.get('telegram_id')||localStorage.telegramId||'';$('machineId').value=qs.get('machine_id')||'';$('telegramId').onchange=()=>{localStorage.telegramId=$('telegramId').value;loadMachineProfile()};$('machineId').onchange=loadMachineProfile;loadMachineProfile();renderMachine();
updateWorkMode();renderContourTable();addOperation('turn_rough');addOperation('turn_finish');
</script>

<script id="v270-layout-script">
window.addEventListener("DOMContentLoaded",()=>{
 const app=document.querySelector(".app"), side=app?.querySelector("aside.panel"), main=app?.querySelector("main.canvasWrap"), results=app?.querySelector("section.results");
 if(!app||!side||!main||!results)return;
 const versionBadge=document.querySelector(".badge"); if(versionBadge) versionBadge.textContent="v4.0 Vision + OpenCV";
 const contour=document.getElementById("module-contour");
 if(contour){contour.classList.add("panel","v270-contour-panel");app.insertBefore(contour,main)}
 const sections=[...side.querySelectorAll(":scope > .section")];
 const tabs=[...side.querySelectorAll(".moduleStrip button")];
 const map={project:"module-project",pdf:"module-pdf",geometry:"module-geometry",contour:"module-contour",operations:"module-operations"};
 function show(id){
   sections.forEach(s=>s.classList.toggle("v270-active",s.id===id));
   if(id==="module-contour"&&contour) contour.scrollIntoView({behavior:"smooth",block:"nearest"});
 }
 tabs.forEach(b=>b.addEventListener("click",()=>{const key=b.dataset.jump; if(map[key]) show(map[key])}));
 show("module-project");
 const extra=document.createElement("div");extra.className="v270-sidebar-extra";
 extra.innerHTML='<button data-open-result="controllerGuide">🖥️ Стойка SINUMERIK<br><small class="muted">Stock Removal Guide</small></button><button data-open-result="preview">📊 Симуляция<br><small class="muted">Проверка траектории</small></button><button data-open-result="gcode">📑 Отчёт<br><small class="muted">Техпроцесс и экспорт</small></button><button data-open-result="setup">ℹ️ О проекте<br><small class="muted">Информация и помощь</small></button>';
 side.querySelector(".moduleStrip")?.after(extra);
 extra.addEventListener("click",e=>{const b=e.target.closest("[data-open-result]");if(!b)return;const target=b.dataset.openResult;results.querySelector(`[data-tab="${target}"]`)?.click();});
 const card=document.createElement("div");card.className="v270-project-card";card.innerHTML='<b>Текущий проект</b><div><span>Файл:</span><b id="v270-file">—</b></div><div><span>Тип:</span><b>Токарная</b></div><div><span>Ед.:</span><b>мм</b></div><div><span>Статус:</span><b style="color:#36d884">● Готов к расчёту</b></div>';
 side.appendChild(card);
 document.getElementById("pdfFile")?.addEventListener("change",e=>{const f=e.target.files?.[0];if(f)document.getElementById("v270-file").textContent=f.name});
 const guideTab=results.querySelector('[data-tab="controllerGuide"]'); if(guideTab) guideTab.click();
});
</script>
</body></html>'''
