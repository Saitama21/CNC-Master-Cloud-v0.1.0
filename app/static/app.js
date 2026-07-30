const state = {
  file: null,
  image: null,
  crop: null,
  dragging: false,
  start: null,
  health: null,
};

const $ = (id) => document.getElementById(id);
const fileInput = $('fileInput');
const dropZone = $('dropZone');
const previewArea = $('previewArea');
const canvas = $('imageCanvas');
const ctx = canvas.getContext('2d');
const pdfPreview = $('pdfPreview');
const promptInput = $('promptInput');
const analyzeBtn = $('analyzeBtn');

function toast(message) {
  const el = $('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(el.timer);
  el.timer = setTimeout(() => el.classList.remove('show'), 3200);
}

async function loadHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('Сервер недоступен');
    state.health = await res.json();
    $('statusDot').className = 'status-dot online';
    $('statusTitle').textContent = state.health.mock_mode ? 'Тестовый режим' : 'OpenAI подключён';
    $('statusText').textContent = state.health.mock_mode ? 'API не расходуется' : state.health.model;
    $('modelName').textContent = state.health.model;
    $('modeName').textContent = state.health.mock_mode ? 'MOCK' : 'LIVE';
    $('fileLimit').textContent = `${state.health.max_file_mb} МБ`;
    if (state.health.supported_types) { document.querySelector('#settingsView .setting-card p').textContent = `Поддерживаются: ${state.health.supported_types.join(', ')}`; }
  } catch (error) {
    $('statusDot').className = 'status-dot error';
    $('statusTitle').textContent = 'Нет соединения';
    $('statusText').textContent = error.message;
  }
}

function setView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(v => v.classList.toggle('active', v.dataset.view === name));
  $(`${name}View`).classList.add('active');
  const copy = {
    analysis: ['Новый анализ', 'Загрузите изображение, PDF или SLDDRW и задайте вопрос'],
    history: ['История', 'Все сохранённые результаты'],
    settings: ['Настройки', 'Состояние сервера и модели'],
  };
  $('pageTitle').textContent = copy[name][0];
  $('pageSubtitle').textContent = copy[name][1];
  $('newAnalysisBtn').style.display = name === 'analysis' ? '' : 'none';
  if (name === 'history') loadHistory();
}

document.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', () => setView(btn.dataset.view)));

document.querySelectorAll('.quick-prompts button').forEach(btn => btn.addEventListener('click', () => {
  promptInput.value = btn.dataset.prompt;
  updateAnalyzeState();
}));

['dragenter', 'dragover'].forEach(type => dropZone.addEventListener(type, e => {
  e.preventDefault(); dropZone.classList.add('dragover');
}));
['dragleave', 'drop'].forEach(type => dropZone.addEventListener(type, e => {
  e.preventDefault(); dropZone.classList.remove('dragover');
}));
dropZone.addEventListener('drop', e => handleFile(e.dataTransfer.files[0]));
fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));
promptInput.addEventListener('input', updateAnalyzeState);

function resetAnalysis() {
  state.file = null; state.image = null; state.crop = null; state.dragging = false;
  fileInput.value = ''; promptInput.value = '';
  dropZone.classList.remove('hidden'); previewArea.classList.add('hidden');
  canvas.style.display = 'block'; pdfPreview.style.display = 'none'; pdfPreview.src = '';
  $('fileBadge').textContent = 'Нет файла'; $('selectionInfo').textContent = 'Область не выбрана';
  $('selectAllBtn').disabled = true; $('clearSelectionBtn').disabled = true;
  $('resultContent').classList.add('hidden'); $('resultEmpty').classList.remove('hidden');
  $('resultMeta').textContent = ''; updateAnalyzeState();
}
$('newAnalysisBtn').addEventListener('click', resetAnalysis);

function updateAnalyzeState() {
  analyzeBtn.disabled = !(state.file && promptInput.value.trim().length >= 3);
}

function handleFile(file) {
  if (!file) return;
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const allowed = ['image/jpeg','image/png','image/webp','application/pdf'];
  const isSlddrw = ext === 'slddrw';
  if (!(allowed.includes(file.type) || isSlddrw)) return toast('Поддерживаются JPG, PNG, WEBP, PDF и SLDDRW');
  if (state.health && file.size > state.health.max_file_mb * 1024 * 1024) return toast(`Файл больше ${state.health.max_file_mb} МБ`);
  state.file = file; state.crop = null;
  $('fileBadge').textContent = file.name;
  dropZone.classList.add('hidden'); previewArea.classList.remove('hidden');
  $('clearSelectionBtn').disabled = true;
  if (file.type === 'application/pdf') {
    canvas.style.display = 'none'; pdfPreview.style.display = 'block';
    pdfPreview.src = URL.createObjectURL(file);
    $('selectionHint').classList.add('hidden'); $('selectionInfo').textContent = 'PDF анализируется целиком';
    $('selectAllBtn').disabled = true;
  } else if (isSlddrw) {
    pdfPreview.style.display = 'none'; canvas.style.display = 'none';
    $('selectionHint').classList.remove('hidden');
    $('selectionHint').textContent = 'SLDDRW будет обработан через встроенное превью и извлечённые данные';
    $('selectionInfo').textContent = 'SLDDRW анализируется целиком';
    $('selectAllBtn').disabled = true;
  } else {
    pdfPreview.style.display = 'none'; canvas.style.display = 'block';
    $('selectionHint').classList.remove('hidden'); $('selectionHint').textContent = 'Проведите мышью или пальцем, чтобы выделить область'; $('selectAllBtn').disabled = false;
    const image = new Image();
    image.onload = () => { state.image = image; resizeCanvas(); drawCanvas(); };
    image.src = URL.createObjectURL(file);
  }
  updateAnalyzeState();
}

function resizeCanvas() {
  if (!state.image) return;
  const maxWidth = previewArea.clientWidth || 900;
  const ratio = Math.min(1, maxWidth / state.image.naturalWidth);
  canvas.width = Math.max(1, Math.round(state.image.naturalWidth * ratio));
  canvas.height = Math.max(1, Math.round(state.image.naturalHeight * ratio));
}

function drawCanvas() {
  if (!state.image) return;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(state.image,0,0,canvas.width,canvas.height);
  if (state.crop) {
    const x = state.crop.x * canvas.width, y = state.crop.y * canvas.height;
    const w = state.crop.width * canvas.width, h = state.crop.height * canvas.height;
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,.52)';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.clearRect(x,y,w,h);
    ctx.drawImage(
      state.image,
      state.crop.x * state.image.naturalWidth,
      state.crop.y * state.image.naturalHeight,
      state.crop.width * state.image.naturalWidth,
      state.crop.height * state.image.naturalHeight,
      x, y, w, h
    );
    ctx.strokeStyle = '#76f5b2'; ctx.lineWidth = 2; ctx.setLineDash([8,5]); ctx.strokeRect(x,y,w,h);
    ctx.restore();
  }
}

function pointerPosition(e) {
  const rect = canvas.getBoundingClientRect();
  const clientX = e.clientX ?? e.touches?.[0]?.clientX;
  const clientY = e.clientY ?? e.touches?.[0]?.clientY;
  return {
    x: Math.max(0, Math.min(canvas.width, (clientX - rect.left) * canvas.width / rect.width)),
    y: Math.max(0, Math.min(canvas.height, (clientY - rect.top) * canvas.height / rect.height)),
  };
}

function startSelection(e) { if (!state.image) return; e.preventDefault(); state.dragging = true; state.start = pointerPosition(e); }
function moveSelection(e) {
  if (!state.dragging) return; e.preventDefault();
  const p = pointerPosition(e), x = Math.min(state.start.x,p.x), y = Math.min(state.start.y,p.y);
  const width = Math.abs(p.x-state.start.x), height = Math.abs(p.y-state.start.y);
  state.crop = {x:x/canvas.width,y:y/canvas.height,width:width/canvas.width,height:height/canvas.height};
  drawCanvas();
}
function endSelection(e) {
  if (!state.dragging) return; state.dragging = false;
  if (!state.crop || state.crop.width*canvas.width < 8 || state.crop.height*canvas.height < 8) state.crop = null;
  updateSelectionInfo(); drawCanvas();
}
canvas.addEventListener('pointerdown', startSelection);
canvas.addEventListener('pointermove', moveSelection);
window.addEventListener('pointerup', endSelection);

function updateSelectionInfo() {
  if (!state.crop) { $('selectionInfo').textContent = 'Область не выбрана'; $('clearSelectionBtn').disabled = true; return; }
  $('selectionInfo').textContent = `Область: ${Math.round(state.crop.width*100)}% × ${Math.round(state.crop.height*100)}%`;
  $('clearSelectionBtn').disabled = false;
  $('selectionHint').classList.add('hidden');
}
$('selectAllBtn').addEventListener('click', () => { state.crop = {x:0,y:0,width:1,height:1}; updateSelectionInfo(); drawCanvas(); });
$('clearSelectionBtn').addEventListener('click', () => { state.crop = null; updateSelectionInfo(); $('selectionHint').classList.remove('hidden'); drawCanvas(); });
window.addEventListener('resize', () => { if (state.image) { resizeCanvas(); drawCanvas(); } });

function renderText(text) {
  const escaped = text.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  return escaped
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

analyzeBtn.addEventListener('click', async () => {
  if (!state.file) return;
  analyzeBtn.disabled = true; $('progress').classList.remove('hidden');
  const form = new FormData();
  form.append('file', state.file); form.append('prompt', promptInput.value.trim());
  const ext = (state.file.name.split('.').pop() || '').toLowerCase();
  if (state.crop && state.file.type !== 'application/pdf' && ext !== 'slddrw') form.append('crop_json', JSON.stringify(state.crop));
  try {
    const res = await fetch('/api/analyze', {method:'POST',body:form});
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Ошибка анализа');
    $('resultEmpty').classList.add('hidden'); $('resultContent').classList.remove('hidden');
    $('resultContent').innerHTML = renderText(data.response);
    $('resultMeta').textContent = `${data.model}${data.mock ? ' · MOCK' : ''} · #${data.id}`;
    $('resultContent').scrollIntoView({behavior:'smooth',block:'start'});
    toast('Анализ сохранён в истории');
  } catch (error) { toast(error.message); }
  finally { $('progress').classList.add('hidden'); updateAnalyzeState(); }
});

async function loadHistory() {
  const list = $('historyList'); list.innerHTML = '<div class="result-empty"><span>Загрузка...</span></div>';
  try {
    const res = await fetch('/api/history'); const items = await res.json();
    if (!items.length) { list.innerHTML = '<div class="result-empty"><strong>История пока пуста</strong></div>'; return; }
    list.innerHTML = items.map(item => `
      <div class="history-item" data-id="${item.id}">
        <div><h3>${escapeHtml(item.filename)} ${item.mock ? '<small>MOCK</small>' : ''}</h3><p>${escapeHtml(item.prompt)}</p><small>${new Date(item.created_at*1000).toLocaleString('ru-RU')} · ${escapeHtml(item.model)}</small></div>
        <button class="history-delete" data-delete="${item.id}" title="Удалить">×</button>
      </div>`).join('');
    list.querySelectorAll('.history-item').forEach((el,index) => el.addEventListener('click', e => {
      if (e.target.dataset.delete) return;
      const item = items[index]; setView('analysis');
      $('resultEmpty').classList.add('hidden'); $('resultContent').classList.remove('hidden');
      $('resultContent').innerHTML = renderText(item.response); $('resultMeta').textContent = `${item.model}${item.mock ? ' · MOCK' : ''} · #${item.id}`;
    }));
    list.querySelectorAll('[data-delete]').forEach(btn => btn.addEventListener('click', async e => {
      e.stopPropagation(); await fetch(`/api/history/${btn.dataset.delete}`, {method:'DELETE'}); loadHistory();
    }));
  } catch (error) { list.innerHTML = `<div class="result-empty"><strong>${escapeHtml(error.message)}</strong></div>`; }
}
function escapeHtml(value='') { return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
$('refreshHistoryBtn').addEventListener('click', loadHistory);

loadHealth();
