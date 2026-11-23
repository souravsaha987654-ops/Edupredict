/* EduPredict AI - small helper scripts (no frameworks) */
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

// sliders: live value + coloured fill
function bindSliders(root = document) {
  $$('input[type=range]', root).forEach(r => {
    const out = r.parentElement.querySelector('output'), unit = r.dataset.unit || '';
    const upd = () => { r.style.setProperty('--pct', ((r.value - r.min) / (r.max - r.min) * 100) + '%'); if (out) out.textContent = r.value + unit; };
    r.addEventListener('input', upd); upd();
  });
}

// generic step-by-step wizard (used by onboarding and the questionnaire)
function wizard(form, onDone) {
  const panes = $$('.pane', form), bars = $$('.steps b'); let i = 0;
  const show = n => {
    i = n; panes.forEach((p, k) => p.classList.toggle('on', k === n)); bars.forEach((b, k) => b.classList.toggle('on', k <= n));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  $$('[data-next]', form).forEach(b => b.onclick = () => {
    if (b.dataset.require && !$(b.dataset.require, form).value.trim()) { $(b.dataset.require, form).focus(); return; }
    i < panes.length - 1 ? show(i + 1) : onDone();
  });
  $$('[data-back]', form).forEach(b => b.onclick = () => (i > 0 ? show(i - 1) : history.back()));
  show(0);
}

// chip group helper
function chipGroup(box, name, options, selected) {
  box.innerHTML = options.map(o => `<label class="chip"><input type="radio" name="${name}" value="${o}" ${o === selected ? 'checked' : ''}><span>${o}</span></label>`).join('');
}

// result ring animation
function animateRing() {
  const fg = $('.ring .fg'); if (!fg) return;
  const C = 2 * Math.PI * 90, score = +fg.dataset.score; fg.style.strokeDasharray = C; fg.style.strokeDashoffset = C;
  requestAnimationFrame(() => requestAnimationFrame(() => fg.style.strokeDashoffset = C * (1 - score / 100)));
  const n = $('.ring .n'); let v = 0; const t = setInterval(() => { v += Math.max(1, Math.round(score / 40)); if (v >= score) { v = score; clearInterval(t); } n.textContent = v; }, 30);
}

// AI mock interview
async function post(url, data) {
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  const j = await r.json(); if (!r.ok) throw new Error(j.error || 'Something went wrong'); return j;
}
function initInterview() {
  const setup = $('#setup'), room = $('#room'); if (!setup) return;
  let qs = [], idx = 0, scores = [];
  const chat = $('#chat'), ans = $('#ans'), send = $('#send');
  const bubble = (cls, build) => { const d = document.createElement('div'); d.className = 'm ' + cls; build(d); chat.appendChild(d); chat.scrollTop = 1e6; return d; };
  const say = (t, cls = 'ai') => bubble(cls, d => d.textContent = t);
  const ask = () => { $('#prog').textContent = `Question ${idx + 1} of ${qs.length}`; $('#pb').style.width = (idx / qs.length * 100) + '%'; say(qs[idx].question); ans.disabled = send.disabled = false; ans.focus(); };

  $('#start').onclick = async () => {
    const topics = $('#syl').value.split(/\n|,/).map(s => s.trim()).filter(Boolean);
    if (!topics.length) { $('#syl').focus(); return; }
    $('#start').disabled = true; $('#start').textContent = 'Preparing questions…';
    try {
      const d = await post('/api/interview/questions', { topics, difficulty: $('input[name=diff]:checked').value });
      qs = d.questions; idx = 0; scores = []; setup.style.display = 'none'; room.style.display = 'block';
      $('#src').textContent = d.source === 'gemini' ? '✨ Powered by Gemini' : '📝 Practice mode (add a Gemini key for AI questions)';
      say('Hello! I am your AI examiner. Take your time and answer in your own words.'); ask();
    } catch (e) { alert(e.message); $('#start').disabled = false; $('#start').textContent = 'Start interview'; }
  };

  send.onclick = async () => {
    const a = ans.value.trim(); if (!a) { ans.focus(); return; }
    ans.value = ''; ans.disabled = send.disabled = true; say(a, 'u');
    const wait = say('Evaluating your answer…');
    try {
      const q = qs[idx], d = await post('/api/interview/evaluate', { topic: q.topic, question: q.question, answer: a });
      wait.remove(); scores.push(d.score);
      bubble('ai', m => {
        const s = document.createElement('span'); s.className = 'sc'; s.textContent = `Score ${d.score}/10`; m.append(s);
        const p = document.createElement('div'); p.textContent = d.feedback; m.append(p);
        if (d.tip) { const t = document.createElement('div'); t.style.marginTop = '6px'; t.textContent = '💡 ' + d.tip; m.append(t); }
        if (d.key_points && d.key_points.length) { const u = document.createElement('ul'); d.key_points.forEach(k => { const l = document.createElement('li'); l.textContent = k; u.append(l); }); m.append(u); }
      });
      idx++; idx < qs.length ? setTimeout(ask, 900) : finish();
    } catch (e) { wait.remove(); say('Sorry, ' + e.message); ans.disabled = send.disabled = false; }
  };

  function finish() {
    $('#pb').style.width = '100%'; $('#prog').textContent = 'Interview complete 🎉';
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length, low = scores.indexOf(Math.min(...scores));
    $('#compose').style.display = 'none';
    const box = $('#summary'); box.style.display = 'block';
    $('#avg').textContent = avg.toFixed(1) + ' / 10';
    $('#weak').textContent = qs[low].topic;
    $('#rows').innerHTML = qs.map((q, k) => `<div class="r"><span></span><div class="pbar"><i style="width:${scores[k] * 10}%"></i></div><b>${scores[k]}</b></div>`).join('');
    $$('#rows .r span').forEach((s, k) => s.textContent = qs[k].topic);
  }
}

document.addEventListener('DOMContentLoaded', () => { bindSliders(); animateRing(); initInterview(); });
