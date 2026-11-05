let bankFile, bank, stats = {}, cur, last, sel = [], place = {}, held = null, done = false, ok = false;
const $ = id => document.getElementById(id);
const load = () => JSON.parse(localStorage.getItem('stats:' + bankFile) || '{}');
const save = () => localStorage.setItem('stats:' + bankFile, JSON.stringify(stats));

async function init() {
  const list = await (await fetch('banks/index.json')).json();
  list.forEach(b => $('bank').add(new Option(b.name, b.file)));
  $('bank').onchange = () => openBank($('bank').value);
  $('export').onclick = exportData;
  $('import').onchange = importData;
  $('reset').onclick = () => { if (confirm('Apagar o progresso deste banco?')) { stats = {}; save(); next(); } };
  $('card').onclick = onClick;
  $('card').ondragstart = e => { const c = e.target.closest('.chip'); if (c) e.dataTransfer.setData('text', c.dataset.item); };
  $('card').ondragover = e => { if (e.target.closest('.slot')) e.preventDefault(); };
  $('card').ondrop = e => {
    const s = e.target.closest('.slot');
    if (s && !done) { e.preventDefault(); put(+s.dataset.t, +e.dataTransfer.getData('text')); }
  };
  openBank(list[0].file);
}

async function openBank(file) {
  bankFile = file;
  bank = await (await fetch('banks/' + file)).json();
  stats = load(); last = null; next();
}

// Peso = quanto a questão deve aparecer. Nunca vista: 3. Errou: +2. Acertou: -1 (mínimo 0).
const weight = q => stats[q.id] ? 0.3 + stats[q.id].score : 3;

function next() {
  const pool = bank.questions.filter(q => q.id !== last);
  const w = pool.map(weight);
  let r = Math.random() * w.reduce((a, b) => a + b, 0);
  cur = pool.find((q, i) => (r -= w[i]) < 0) || pool[0];
  last = cur.id; sel = []; place = {}; held = null; done = false;
  render();
}

function put(t, i) {
  Object.keys(place).forEach(k => { if (place[k] === i) delete place[k]; });
  place[t] = i; held = null; render();
}

function onClick(e) {
  const t = e.target;
  if (t.id === 'go') return done ? next() : check();
  if (done) return;
  const slot = t.closest('.slot'), chip = t.closest('.chip'), opt = t.closest('.opt');
  if (slot) {
    const k = +slot.dataset.t;
    if (held !== null) put(k, held);
    else if (place[k] !== undefined) { delete place[k]; render(); }
  } else if (chip) { held = +chip.dataset.item; render(); }
  else if (opt) {
    const i = +opt.dataset.i;
    if (cur.type === 'multiple') sel = sel.includes(i) ? sel.filter(x => x !== i) : [...sel, i];
    else sel = [i];
    render();
  }
}

function check() {
  const q = cur;
  ok = q.type === 'dragdrop'
    ? q.targets.every((_, t) => place[t] === q.answer[t])
    : sel.length === q.answer.length && q.answer.every(a => sel.includes(a));
  const s = stats[q.id] ||= { right: 0, wrong: 0, score: 0 };
  if (ok) { s.right++; s.score = Math.max(0, s.score - 1); }
  else { s.wrong++; s.score = Math.min(8, s.score + 2); }
  save(); done = true; render();
}

function render() {
  const q = cur;
  const chip = i => `<span class="chip${held === i ? ' held' : ''}" draggable="${!done}" data-item="${i}">${q.items[i]}</span>`;
  let h = q.case ? `<div class="case">${bank.cases[q.case]}</div>` : '';
  h += `<h2>${q.question}</h2>`;
  if (q.type === 'dragdrop') {
    const used = Object.values(place);
    h += `<p class="hint">Arraste (ou toque no item e depois no destino).</p>`;
    h += `<div class="pool">${q.items.map((_, i) => used.includes(i) ? '' : chip(i)).join('')}</div>`;
    h += q.targets.map((tg, t) => {
      const c = done ? (place[t] === q.answer[t] ? ' right' : ' wrong') : '';
      const fix = done && place[t] !== q.answer[t] ? `<div class="hint">Correto: ${q.items[q.answer[t]]}</div>` : '';
      return `<div class="slot${c}" data-t="${t}">${tg}<div class="drop">${place[t] !== undefined ? chip(place[t]) : ''}</div>${fix}</div>`;
    }).join('');
  } else {
    if (q.type === 'multiple') h += `<p class="hint">Escolha ${q.answer.length}.</p>`;
    h += q.options.map((o, i) => {
      let c = sel.includes(i) ? ' sel' : '';
      if (done) c = q.answer.includes(i) ? ' right' : sel.includes(i) ? ' wrong' : '';
      return `<button class="opt${c}" data-i="${i}">${o}</button>`;
    }).join('');
  }
  if (done) h += `<div class="explain"><b>${ok ? 'Correto' : 'Incorreto'}.</b> ${q.explanation || ''}</div>`;
  h += `<button id="go">${done ? 'Próxima' : 'Responder'}</button>`;
  $('card').innerHTML = h;
  const v = Object.values(stats), r = v.reduce((a, s) => a + s.right, 0), w = v.reduce((a, s) => a + s.wrong, 0);
  $('stats').textContent = `${v.length}/${bank.questions.length} vistas · ${r + w ? Math.round(100 * r / (r + w)) : 0}% de acerto · ${v.filter(s => s.score >= 2).length} difíceis`;
}

function exportData() {
  const all = {};
  Object.keys(localStorage).filter(k => k.startsWith('stats:')).forEach(k => all[k] = localStorage[k]);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(all)], { type: 'application/json' }));
  a.download = 'progresso-quiz.json'; a.click();
}

async function importData(e) {
  const all = JSON.parse(await e.target.files[0].text());
  Object.entries(all).forEach(([k, v]) => localStorage.setItem(k, v));
  stats = load(); next();
}

init();
