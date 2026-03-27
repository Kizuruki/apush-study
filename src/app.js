// ─── APUSH Study App — Plain ES Modules, GitHub Pages compatible ───────────
// No build step needed. Uses Anthropic API via user-provided key.

// ─── State ────────────────────────────────────────────────────────────────
const state = {
  view: 'home',
  units: [],
  fiveableNotes: {},
  heimlerNotes: {},
  selectedUnit: null,
  selectedTopic: null,
  question: null,
  unitOverviews: {},
  loading: false,
  error: null,
  selected: null,
  revealed: false,
  sessionScore: { c: 0, t: 0 },
  progress: load('apush_progress') || {},
  topicProgress: load('apush_topic_progress') || {},
  missed: load('apush_missed') || [],
  essayPrompts: null,
  showNotes: true,
  unitOverviews: {},
  fiveableRaw: {},
  heimlerRaw: {},
  questionBank: {},
  questionHistory: load('apush_q_history') || [],
  historyFilter: 'all',
  topicView: 'drill',  // 'drill' | 'notes'
};

// ─── Helpers ──────────────────────────────────────────────────────────────
function load(key) { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } }
function save(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch {} }
function getApiKey() { return localStorage.getItem('openai_api_key') || ''; }
function saveApiKey() {
  const key = document.getElementById('apiKeyInput')?.value?.trim();
  if (!key || !key.startsWith('sk-')) { alert('Please enter a valid OpenAI API key (starts with sk-)'); return; }
  localStorage.setItem('openai_api_key', key);
  document.getElementById('apiKeyModal').style.display = 'none';
  render();
}
window.saveApiKey = saveApiKey;

function updateProgress(unitId, topicId, correct) {
  const up = state.progress;
  if (!up[unitId]) up[unitId] = { total: 0, correct: 0 };
  up[unitId].total++; if (correct) up[unitId].correct++;
  save('apush_progress', up);
  const tp = state.topicProgress;
  const k = `${unitId}-${topicId}`;
  if (!tp[k]) tp[k] = { total: 0, correct: 0 };
  tp[k].total++; if (correct) tp[k].correct++;
  save('apush_topic_progress', tp);
}

function addMissed(unit, topic, question) {
  const m = state.missed.filter(x => x.question?.question !== question?.question);
  state.missed = [{ unit: { id: unit.id, period: unit.period, color: unit.color },
    topic: { id: topic.id, title: topic.title }, question }, ...m].slice(0, 50);
  save('apush_missed', state.missed);
}

function weightedRandomUnit() {
  const pool = [];
  state.units.forEach(u => { for (let i = 0; i < u.weight; i++) pool.push(u); });
  return pool[Math.floor(Math.random() * pool.length)];
}

function pct(c, t) { return t ? Math.round(100 * c / t) : null; }
function esc(s) { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }

// ─── Fiveable URL map (one per CED topic) ─────────────────────────────────
const FIVEABLE_URLS = {
  '1.2':'https://fiveable.me/apush/unit-1/native-american-societies-before-european-contact/study-guide/WSdp3WwC8fc4Hcds2um6',
  '1.3':'https://fiveable.me/apush/unit-1/european-exploration-americas/study-guide/4Xo0Z9vsVo97AfHCtNzM',
  '1.4':'https://fiveable.me/apush/unit-1/columbian-exchange-spanish-exploration-conquest/study-guide/adQt4h0vtMjRyzXDZN8e',
  '1.5':'https://fiveable.me/apush/unit-1/labor-slavery-caste-spanish-colonial-system/study-guide/YNYW7aq8cgcgywTr8aob',
  '1.6':'https://fiveable.me/apush/unit-1/cultural-interactions-between-europeans-native-americans-africans/study-guide/xKdK0605epqUHu2tUwYM',
  '2.2':'https://fiveable.me/apush/unit-2/european-colonization-north-america/study-guide/bOqbTIQvhKy42VNcnRMs',
  '2.3':'https://fiveable.me/apush/unit-2/regions-british-colonies/study-guide/43BTTQADqqAwsWbjpJ5G',
  '2.4':'https://fiveable.me/apush/unit-2/transatlantic-trade/study-guide/UcqUNsSk8bGifGh838TY',
  '2.5':'https://fiveable.me/apush/unit-2/interactions-between-american-indians-europeans/study-guide/chUDbGx9XSPajryeDxcv',
  '2.6':'https://fiveable.me/apush/unit-2/slavery-british-colonies/study-guide/h2ezjfgaQaItQZybcxyf',
  '2.7':'https://fiveable.me/apush/unit-2/colonial-society-culture/study-guide/Lko98iWbbumC8ceFevkv',
  '3.2':'https://fiveable.me/apush/unit-3/seven-years-war-french-indian-war/study-guide/Xiy5IbXj54SmSbIyUazE',
  '3.3':'https://fiveable.me/apush/unit-3/taxation-without-representation/study-guide/RjW4aBcZHoaG4ABJrvIk',
  '3.4':'https://fiveable.me/apush/unit-3/philosophical-foundations-american-revolution/study-guide/1tqf5yAhHDgdepsUL6GT',
  '3.5':'https://fiveable.me/apush/unit-3/american-revolution/study-guide/qmZACCrcWZjV1YajNd9d',
  '3.6':'https://fiveable.me/apush/unit-3/influence-revolutionary-ideals/study-guide/DaZjTIBFYrpHgheRa9sC',
  '3.7':'https://fiveable.me/apush/unit-3/articles-confederation/study-guide/bllK78POE3keG1TCHNXI',
  '3.8':'https://fiveable.me/apush/unit-3/constitutional-convention-debates-over-ratification/study-guide/OVohv8ZoyPEaJ0Ut9yUa',
  '3.9':'https://fiveable.me/apush/unit-3/constitution/study-guide/GFXLutGBoLM4MszJCxWq',
  '3.10':'https://fiveable.me/apush/unit-3/shaping-new-republic/study-guide/jDcJK92nIldkFTb5QJpZ',
  '4.2':'https://fiveable.me/apush/unit-4/rise-political-parties-era-jefferson/study-guide/jBptoMVxCR4JxRknAlm7',
  '4.3':'https://fiveable.me/apush/unit-4/politics-regional-interests-1800-1848/study-guide/1TQCI0h8ONg84TKhEywv',
  '4.5':'https://fiveable.me/apush/unit-4/market-revolution-industrialization/study-guide/XB7wtlsHuzKyN4rtUORe',
  '4.6':'https://fiveable.me/apush/unit-4/market-revolution-society-culture/study-guide/utkUPzxiRypzIvTXl779',
  '4.7':'https://fiveable.me/apush/unit-4/expanding-democracy-1800-1848/study-guide/yvZqvo6sEMe2gvvM03AB',
  '4.8':'https://fiveable.me/apush/unit-4/jackson-federal-power/study-guide/VnevAqqtpZVuKzRpBf4O',
  '4.10':'https://fiveable.me/apush/unit-4/second-great-awakening/study-guide/tR4UP1gR5yZZRsp6w0v9',
  '4.11':'https://fiveable.me/apush/unit-4/an-age-reform-1800-1848/study-guide/pq1BOhhhmXUke0J5WXkS',
  '4.13':'https://fiveable.me/apush/unit-4/society-south-early-republic/study-guide/zhWn5XFSD8f6Lh2VoX4c',
  '5.2':'https://fiveable.me/apush/unit-5/manifest-destiny/study-guide/QCAKf0AWBCPTgZHZtUPD',
  '5.3':'https://fiveable.me/apush/unit-5/mexican-american-war/study-guide/NMqiBxahosm76SKTghut',
  '5.4':'https://fiveable.me/apush/unit-5/compromise-1850/study-guide/SD3f1WJu48SnOd8v1RAm',
  '5.6':'https://fiveable.me/apush/unit-5/failure-compromise/study-guide/Pc8cAsWACsNLhZIwOHf3',
  '5.7':'https://fiveable.me/apush/unit-5/election-1860-secession/study-guide/6wnMakCgnFOoTG2IEnSa',
  '5.8':'https://fiveable.me/apush/unit-5/military-conflict-civil-war/study-guide/d9NgoNY74uuvfh4RmD6l',
  '5.9':'https://fiveable.me/apush/unit-5/government-policies-during-civil-war/study-guide/rI7StngOCC4D0qsmkDvV',
  '5.10':'https://fiveable.me/apush/unit-5/reconstruction/study-guide/DiWHCM2v4Drc73iIcfDS',
  '5.11':'https://fiveable.me/apush/unit-5/failures-reconstruction/study-guide/v760MdiOJXB3TCLYZBZ5',
  '6.3':'https://fiveable.me/apush/unit-6/westward-expansion-social-cultural-development-1865-1898/study-guide/tjZEnBbepPcpcbtaF5eA',
  '6.4':'https://fiveable.me/apush/unit-6/new-south-1865-1898/study-guide/OB83CdTZrgzJYVjQ0xCX',
  '6.5':'https://fiveable.me/apush/unit-6/technological-innovation-1865-1898/study-guide/UbJ4g3jWethQISe6Yzal',
  '6.6':'https://fiveable.me/apush/unit-6/rise-industrial-capitalism-1865-1898/study-guide/KgfyIEY4fiMV5yk7Ng0X',
  '6.7':'https://fiveable.me/apush/unit-6/labor-gilded-age-1865-1898/study-guide/S5kLZj55mM4PK2a8a80A',
  '6.8':'https://fiveable.me/apush/unit-6/immigration-migration-gilded-age-1865-1898/study-guide/tFUqkhIaH3BOei1JuxAM',
  '6.11':'https://fiveable.me/apush/unit-6/reform-gilded-age/study-guide/c8AtStJnup2hvLeHcZcC',
  '6.12':'https://fiveable.me/apush/unit-6/controversies-over-role-government-gilded-age/study-guide/CU4ireSXmjF3ZkbKgQYd',
  '7.2':'https://fiveable.me/apush/unit-7/imperialism-debates/study-guide/XQhEsqd89b8yG7yqh4dK',
  '7.3':'https://fiveable.me/apush/unit-7/spanish-american-war/study-guide/oTnk4443gyjW9WwKdPbK',
  '7.4':'https://fiveable.me/apush/unit-7/progressives/study-guide/a9XjRguda7a0EHsXEXDz',
  '7.5':'https://fiveable.me/apush/unit-7/world-war-i-military-diplomacy/study-guide/4wZDa2Pak8FfrKeucUqt',
  '7.6':'https://fiveable.me/apush/unit-7/world-war-i-home-front/study-guide/z3zU0aD0liS5u8BPkQOX',
  '7.7':'https://fiveable.me/apush/unit-7/1920s-innovations-communication-technology/study-guide/KM5LZjLDw8GP7jySCER1',
  '7.8':'https://fiveable.me/apush/unit-7/1920s-cultural-political-controversies/study-guide/LXAypu3iPW64jHg87JFH',
  '7.9':'https://fiveable.me/apush/unit-7/great-depression/study-guide/hI7MOeaEZFK45NrnWkxr',
  '7.10':'https://fiveable.me/apush/unit-7/new-deal/study-guide/O8bvpnFSbBfiQMHlcl4D',
  '7.12':'https://fiveable.me/apush/unit-7/world-war-ii-mobilization/study-guide/5YjYcPKLKi9eIBZzNaXs',
  '7.13':'https://fiveable.me/apush/unit-7/world-war-ii-military/study-guide/3giKnoeivLFf1jQamalK',
  '8.2':'https://fiveable.me/apush/unit-8/cold-war-1945-1980/study-guide/vLoggG1eZuSCQnMwTaE5',
  '8.3':'https://fiveable.me/apush/unit-8/red-scare/study-guide/DO0e4A4aiTYvyrkA5oje',
  '8.4':'https://fiveable.me/apush/unit-8/economy-after-1945/study-guide/houeOTJKnK56RUnHRRD7',
  '8.6':'https://fiveable.me/apush/unit-8/early-steps-civil-rights-movement-1940s-1950s/study-guide/bLUUfoR5Lt4D1FcR5EOB',
  '8.8':'https://fiveable.me/apush/unit-8/vietnam-war/study-guide/vGcbjSr85W3AwiZZEH7T',
  '8.9':'https://fiveable.me/apush/unit-8/great-society/study-guide/5lE2fsg4BsckTqmDNJqx',
  '8.10':'https://fiveable.me/apush/unit-8/african-american-civil-rights-movement-1960s/study-guide/yInAfvUol9DCb9fB2Eer',
  '8.11':'https://fiveable.me/apush/unit-8/expansion-civil-rights-movement/study-guide/4JIzz1rguSts5wCf7Odr',
  '8.14':'https://fiveable.me/apush/unit-8/society-transition/study-guide/XwxV2oK2ulyRH0YxkAZd',
  '9.2':'https://fiveable.me/apush/unit-9/reagan-conservatism/study-guide/bhzREq69MW1ktHbBP8hg',
  '9.3':'https://fiveable.me/apush/unit-9/end-cold-war/study-guide/jSK48CxJEPXM0bpeuKEg',
  '9.4':'https://fiveable.me/apush/unit-9/a-changing-economy-1980-present/study-guide/NPJrmemKFxqdAtJVbR6e',
  '9.5':'https://fiveable.me/apush/unit-9/migration-immigration-1990s-2000s/study-guide/h48Rw9Wyn6SOzLUA4mF6',
  '9.6':'https://fiveable.me/apush/unit-9/challenges-21st-century/study-guide/EXLLVyYPLInl4kY1shVW',
};

// ─── API call ──────────────────────────────────────────────────────────────
async function callClaude(prompt, maxTokens = 1100) {
  const key = getApiKey();
  if (!key) throw new Error('No API key');
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
    body: JSON.stringify({ model: 'gpt-4o-mini', max_tokens: maxTokens, messages: [{ role: 'user', content: prompt }] })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return data.choices[0].message.content;
}

// ─── Question generator ────────────────────────────────────────────────────
function chunkNotes(text, size = 700) {
  const paras = text.split('\n').map(p => p.trim()).filter(p => p.length > 40);
  if (!paras.length) return text.slice(0, size);
  const chunks = [];
  let cur = [], len = 0;
  for (const p of paras) {
    cur.push(p); len += p.length;
    if (len >= size) { chunks.push(cur.join('\n')); cur = []; len = 0; }
  }
  if (cur.length) chunks.push(cur.join('\n'));
  if (!chunks.length) return text.slice(0, size);
  return chunks[Math.floor(Math.random() * chunks.length)];
}

async function generateQuestion(unit, topic) {
  // 1. Try pre-generated bank first
  const bankPool = state.questionBank[topic.id];
  const historyIds = new Set(
    state.questionHistory
      .filter(h => h.topicId === topic.id)
      .map(h => h.question?.question?.slice(0, 60))
  );
  if (bankPool?.length) {
    const unseen = bankPool.filter(q => !historyIds.has(q.question?.slice(0, 60)));
    const pool = unseen.length ? unseen : bankPool;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  // 2. Fall back to live API with raw notes + random chunk
  const key = getApiKey();
  if (!key) throw new Error('No API key');

  const rawNotes = state.heimlerRaw[topic.id] || state.fiveableRaw[topic.id];
  const chunk = rawNotes
    ? chunkNotes(rawNotes, 700)
    : topic.cedContent;

  const prompt = `You are an expert AP US History exam writer.

UNIT: ${unit.period} (${unit.years}) — ${unit.sub}
TOPIC: ${topic.id} "${topic.title}"
AP THEME: ${topic.themeLabel}

SOURCE NOTES (base your question ONLY on this content):
${chunk}

KEY TERMS FOR CONTEXT: ${topic.keyTerms?.join(', ')}

Generate exactly 3 AP-style MCQs based on the source notes above.

RULES:
- ALL 4 choices must be historically accurate
- Wrong choices are wrong because they answer a DIFFERENT question, NOT because they're false
- Vary question types: Causation / Effect / Connection / Significance / Context
- Each question covers a DIFFERENT aspect of the notes

Return ONLY valid JSON, no markdown:
{"questions":[{"question":"...","choices":[{"letter":"A","text":"..."},{"letter":"B","text":"..."},{"letter":"C","text":"..."},{"letter":"D","text":"..."}],"correct":"C","skill":"Causation","explanation":"...","theme_connection":"...","essay_angle":"..."}]}`;

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
    body: JSON.stringify({ model: 'gpt-4o-mini', max_tokens: 2000, temperature: 0.7,
      messages: [{ role: 'user', content: prompt }] })
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  const text = data.choices[0].message.content.replace(/```json\n?|\n?```/g, '').trim();
  const parsed = JSON.parse(text);
  const questions = parsed.questions;

  // Cache newly generated questions into the bank for this session
  if (!state.questionBank[topic.id]) state.questionBank[topic.id] = [];
  state.questionBank[topic.id].push(...questions);

  return questions[Math.floor(Math.random() * questions.length)];
}

// ─── Essay generator ───────────────────────────────────────────────────────
async function generateEssayPrompts(unit) {
  const topics = unit.topics.map(t => t.title).join(', ');
  const prompt = `You are an AP US History exam writer. Generate 3 essay prompts for ${unit.period} (${unit.years}): ${unit.sub}.

Topics: ${topics}

Return ONLY valid JSON:
{"leq":{"prompt":"Full LEQ prompt text","skill":"Causation/CCOT/Comparison","tip":"Key argument direction"},"saq":{"prompt":"Full SAQ with parts a, b, c","context":"Historical context needed"},"dbq":{"theme":"DBQ theme description","document_types":["type1","type2","type3"],"argument_tip":"How to approach the argument"}}`;

  const raw = await callClaude(prompt, 900);
  return JSON.parse(raw.replace(/```json\n?|\n?```/g, '').trim());
}

// ─── Timeline SVG ──────────────────────────────────────────────────────────
function renderTimeline(events, color) {
  const W = 760, H = 90, PAD = 44;
  const mn = events[0].y, mx = events[events.length-1].y;
  const xOf = y => PAD + ((y - mn) / (mx - mn || 1)) * (W - PAD * 2);
  let svg = `<div class="timeline-scroll"><svg width="${W}" height="${H}" style="display:block">
    <defs><linearGradient id="tl${color.replace('#','')}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${color}" stop-opacity="0.15"/>
      <stop offset="50%" stop-color="${color}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="${color}" stop-opacity="0.15"/>
    </linearGradient></defs>
    <line x1="${PAD}" y1="46" x2="${W-PAD}" y2="46" stroke="url(#tl${color.replace('#','')})" stroke-width="2"/>`;
  events.forEach((ev, i) => {
    const cx = xOf(ev.y), above = i % 2 === 0;
    svg += `<circle cx="${cx}" cy="46" r="4.5" fill="${color}" stroke="white" stroke-width="1.5"/>
      <line x1="${cx}" y1="${above?40:52}" x2="${cx}" y2="${above?26:66}" stroke="${color}" stroke-width="1" stroke-dasharray="2,2"/>
      <text x="${cx}" y="${above?20:76}" text-anchor="middle" font-size="8.5" font-weight="600" fill="${color}">${ev.y}</text>
      <text x="${cx}" y="${above?12:85}" text-anchor="middle" font-size="7.5" fill="#5A5A5A">${ev.e.length>14?ev.e.slice(0,13)+'…':ev.e}</text>`;
  });
  svg += '</svg></div>';
  return svg;
}

// ─── Renders ───────────────────────────────────────────────────────────────
function renderHome() {
  const { units, progress } = state;
  const totalQ = Object.values(progress).reduce((s,p) => s+(p.total||0), 0);
  const totalC = Object.values(progress).reduce((s,p) => s+(p.correct||0), 0);
  const sessionPill = totalQ > 0
    ? `<span style="font-size:12px;color:rgba(255,255,255,0.75);background:rgba(255,255,255,0.1);padding:6px 12px;border-radius:20px">
        Session: ${totalC}/${totalQ} (${Math.round(100*totalC/totalQ)}%)
       </span>` : '';
  const missedPill = state.missed.length > 0
    ? `<span onclick="goMissed()" style="font-size:12px;color:#FCA5A5;background:rgba(220,38,38,0.2);padding:6px 12px;border-radius:20px;cursor:pointer;font-weight:600">
        🔄 ${state.missed.length} missed to review
       </span>` : '';

  const unitCards = units.map(u => {
    const p = progress[u.id] || { total:0, correct:0 };
    const p2 = pct(p.correct, p.total);
    const themes = [...new Set(u.topics.map(t=>t.theme))].slice(0,3);
    const themePills = themes.map(th => {
      const t = u.topics.find(x=>x.theme===th);
      return `<span class="pill" style="background:${t.themeColor}22;color:${t.themeColor}">${th}</span>`;
    }).join('');
    const progressHtml = p2 !== null ? `<div style="margin-top:8px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:3px">${p.correct}/${p.total} correct (${p2}%)</div>
      <div class="progress-bar"><div class="progress-fill" style="width:${p2}%;background:${p2>=70?'var(--ok-border)':p2>=50?'#F59E0B':'#EF4444'}"></div></div>
    </div>` : '';
    return `<div class="card card-clickable unit-card" style="border-left-color:${u.color}" onclick="goUnit(${u.id})">
      <div class="unit-period" style="color:${u.color}">${u.period} · ${u.years}</div>
      <div class="unit-name">${esc(u.sub)}</div>
      <div class="unit-footer">
        <div style="display:flex;gap:4px;flex-wrap:wrap">${themePills}</div>
        <span style="font-size:11px;color:${u.weight>=10?'#EF4444':'var(--muted)'};font-weight:${u.weight>=10?700:400}">${u.examPct}</span>
      </div>
      ${progressHtml}
    </div>`;
  }).join('');

  return `
    <div class="home-header">
      <div class="home-header-inner">
        <div class="home-subtitle">Advanced Placement</div>
        <h1 class="home-title">U.S. History Study</h1>
        <p class="home-desc">CED-aligned questions where every answer choice is historically accurate</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <button onclick="startFullDrill()" class="btn" style="background:#A8762A;color:white;font-size:14px;padding:10px 22px">⚡ Weighted Full Review</button>
          <button onclick="goHistory()" class="btn" style="background:#374151;color:white;font-size:14px;padding:10px 22px">📚 History</button>
          ${missedPill}${sessionPill}
        </div>
      </div>
    </div>
    <div class="home-banner">
      <span>✦ All choices contain real historical facts</span>
      <span>✦ Wrong answers are wrong for CONNECTIONS, not facts</span>
      <span>✦ Progress saved per unit</span>
    </div>
    <div class="unit-grid">${unitCards}</div>`;
}

function renderUnit() {
  const u = state.selectedUnit;
  const tp = state.topicProgress;
  
  const topicRows = u.topics.map(topic => {
    const k = `${u.id}-${topic.id}`;
    const p = tp[k] || { total:0, correct:0 };
    const p2 = pct(p.correct, p.total);
    const fiveUrl = FIVEABLE_URLS[topic.id];
    const fiveLink = fiveUrl
      ? `<a href="${fiveUrl}" target="_blank" style="font-size:11px;color:#5a67d8;text-decoration:none;margin-left:8px" onclick="event.stopPropagation()">📖 Fiveable</a>`
      : '';
    const progressBar = p2 !== null
      ? `<div style="margin-top:5px;display:flex;align-items:center;gap:8px">
          <div class="progress-bar" style="flex:1"><div class="progress-fill" style="width:${p2}%;background:${p2>=70?'var(--ok-border)':'#F59E0B'}"></div></div>
          <span style="font-size:11px;color:var(--muted)">${p.correct}/${p.total}</span>
         </div>` : '';
    return `<div class="card topic-row" style="--active-color:${u.color}" onclick="goTopic('${topic.id}','drill')">
      <div style="flex:1">
        <div class="topic-meta">
          <span class="topic-id" style="color:${u.color}">Topic ${topic.id}</span>
          <span class="pill" style="background:${topic.themeColor}22;color:${topic.themeColor}">${topic.themeLabel}</span>
          ${fiveLink}
        </div>
        <div class="topic-title">${esc(topic.title)}</div>
        <div style="font-size:12px;color:var(--muted);margin-top:3px;line-height:1.5">${esc(topic.cedContent?.slice(0,110))}…</div>
        ${progressBar}
      </div>
      <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end">
        <div class="topic-drill" style="background:${u.color}" onclick="event.stopPropagation();goTopic('${topic.id}','drill')">Drill →</div>
        <div class="topic-drill" style="background:#6D28D9;font-size:11px" onclick="event.stopPropagation();goTopic('${topic.id}','notes')">Notes 📖</div>
      </div>
    </div>`;
  }).join('');

  return `
    <div class="unit-header" style="background:${u.color}">
      <button onclick="goHome()" class="btn btn-ghost" style="margin-bottom:12px;font-size:12px">← All Periods</button>
      <div style="font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.65);text-transform:uppercase;margin-bottom:3px">${u.period} · ${u.years}</div>
      <h1 style="font-family:'Lora',serif;font-size:24px;margin:0 0 4px">${esc(u.sub)}</h1>
      <p style="margin:0;opacity:0.75;font-size:13px">Exam weight: ${u.examPct} · ${u.topics.length} topics</p>
    </div>
    <div class="unit-timeline-wrap">
      <div class="unit-timeline-label">Period Timeline</div>
      ${renderTimeline(u.timeline, u.color)}
    </div>
    <div class="unit-content">
      <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">
        <button onclick="goEssay()" class="btn" style="background:#6D28D9;color:white;font-size:13px">📝 Generate Essay Prompts</button>
        <button onclick="goMissed()" class="btn" style="background:#EF4444;color:white;font-size:13px">🔄 Missed (${state.missed.length})</button>
      </div>
      ${overviewHtml}
      <div class="hint-box">Click any topic to drill it. All 4 choices are historically accurate — wrong answers describe real events but the wrong connection.</div>
      <div class="topic-list">${topicRows}</div>
    </div>`;
}

function renderNotesSummary(unit, topic) {
  const notes = state.heimlerNotes[topic.id] || state.fiveableNotes[topic.id];
  if (notes) {
    return `<div class="summary-card">
      <div class="summary-card-title" style="color:${unit.color}">📚 Study Notes — Topic ${topic.id}</div>
      <div style="font-size:12.5px;color:var(--navy);line-height:1.7;white-space:pre-line">${esc(notes.slice(0,600))}…</div>
    </div>`;
  }
  // Fall back to CED content
  const ex = topic.illustrativeExamples || [];
  const tags = ex.slice(0,5).map(e => `<span class="pill" style="background:${topic.themeColor}18;color:${topic.themeColor};font-size:10px">${esc(e)}</span>`).join('');
  return `<div class="summary-card">
    <div class="summary-card-title" style="color:${unit.color}">📋 CED Content — Topic ${topic.id}</div>
    <div style="font-size:12.5px;color:var(--navy);line-height:1.7;margin-bottom:10px">${esc(topic.cedContent)}</div>
    ${ex.length ? `<div class="summary-examples">
      <div class="summary-examples-label">Illustrative Examples</div>
      <div style="display:flex;gap:5px;flex-wrap:wrap">${tags}</div>
    </div>` : ''}
    <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">
      <div class="summary-examples-label">Key Terms</div>
      <div style="font-size:12px;color:var(--muted)">${(topic.keyTerms||[]).join(' · ')}</div>
    </div>
  </div>`;
}

function renderQuiz() {
  const u = state.selectedUnit, topic = state.selectedTopic;

  // Tab bar shown in both modes
  const tabBar = `
    <div style="display:flex;gap:0;margin-bottom:16px;border:1px solid var(--border);border-radius:8px;overflow:hidden">
      <button onclick="goTopic('${topic.id}','drill')"
        style="flex:1;padding:9px;border:none;cursor:pointer;font-weight:600;font-size:13px;
               background:${state.topicView==='drill'?u.color:'white'};
               color:${state.topicView==='drill'?'white':'var(--navy)'}">
        ⚡ Drill
      </button>
      <button onclick="goTopic('${topic.id}','notes')"
        style="flex:1;padding:9px;border:none;cursor:pointer;font-weight:600;font-size:13px;
               background:${state.topicView==='notes'?u.color:'white'};
               color:${state.topicView==='notes'?'white':'var(--navy)'}">
        📖 Notes
      </button>
    </div>`;

  if (state.topicView === 'notes') {
    const heimlerRaw  = state.heimlerRaw[topic.id];
    const fiveableRaw = state.fiveableRaw[topic.id];
    const heimlerSum  = state.heimlerNotes[topic.id];
    const fiveableSum = state.fiveableNotes[topic.id];

    const rawSection = (label, icon, text, color) => text ? `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px">
        <div style="font-size:10px;letter-spacing:2px;font-weight:700;text-transform:uppercase;color:${color};margin-bottom:10px">
          ${icon} ${label}
        </div>
        <div style="font-size:13px;line-height:1.8;color:var(--navy);white-space:pre-wrap;font-family:'DM Mono',monospace">${esc(text)}</div>
      </div>` : '';

    const notesContent =
      rawSection('Heimler Notes — Original', '📘', heimlerRaw, u.color) ||
      rawSection('Heimler Study Guide — Summary', '📘', heimlerSum, u.color);

    const fiveableContent =
      rawSection('Fiveable Study Guide — Original Scraped', '📗', fiveableRaw, '#059669') ||
      rawSection('Fiveable Study Guide — Summary', '📗', fiveableSum, '#059669');

    const cedContent = `
      <div style="background:#FFF8ED;border:1px solid #FDE68A;border-radius:10px;padding:16px;margin-bottom:12px">
        <div style="font-size:10px;letter-spacing:2px;font-weight:700;text-transform:uppercase;color:#92400E;margin-bottom:8px">
          📋 CED Official Content
        </div>
        <div style="font-size:13px;line-height:1.8;color:var(--navy)">${esc(topic.cedContent)}</div>
        <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">
          <div style="font-size:10px;color:var(--muted);font-weight:700;text-transform:uppercase;margin-bottom:6px">Key Terms</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">${(topic.keyTerms||[]).map(t=>`<span class="pill" style="background:${topic.themeColor}22;color:${topic.themeColor}">${esc(t)}</span>`).join('')}</div>
        </div>
        <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">
          <div style="font-size:10px;color:var(--muted);font-weight:700;text-transform:uppercase;margin-bottom:6px">Illustrative Examples</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">${(topic.illustrativeExamples||[]).map(e=>`<span class="pill" style="background:#F5F3FF;color:#5B21B6;font-size:10px">${esc(e)}</span>`).join('')}</div>
        </div>
      </div>`;

    return `
      <div class="quiz-header" style="background:${u.color}">
        <button onclick="goUnit(${u.id})" class="btn btn-ghost" style="font-size:12px;padding:5px 12px">← Back</button>
        <div class="quiz-header-center">
          <div style="font-size:10px;opacity:0.7;letter-spacing:1px">${u.period} · Topic ${topic.id}</div>
          <div style="font-weight:600;font-size:13px">${esc(topic.title)}</div>
        </div>
        <div style="width:50px"></div>
      </div>
      <div class="quiz-body">
        ${tabBar}
        ${notesContent || ''}
        ${fiveableContent || ''}
        ${cedContent}
      </div>`;
  }
  const { question: q, loading, error, selected, revealed, sessionScore, showNotes } = state;

  const scorePanel = sessionScore.t > 0
    ? `<div class="quiz-session"><div style="font-weight:700">${sessionScore.c}/${sessionScore.t}</div><div style="opacity:0.7;font-size:10px">correct</div></div>`
    : `<div style="width:50px"></div>`;

  let mainContent = '';
  if (loading) {
    mainContent = `<div class="question-card"><div class="loading-box">
      <div class="loading-icon">⏳</div>
      <div style="font-weight:500">Generating question…</div>
      <div class="loading-sub">Building historically accurate choices</div>
    </div></div>`;
  } else if (error) {
    mainContent = `<div class="question-card"><div class="error-box">
      <p>${esc(error)}</p>
      <button onclick="retryQuestion()" class="btn btn-primary">Try Again</button>
    </div></div>`;
  } else if (q) {
    const pillsHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
      <span class="pill" style="background:${topic.themeColor}22;color:${topic.themeColor}">${topic.themeLabel}</span>
      ${q.skill ? `<span class="pill" style="background:#E0E7FF;color:#3730A3">Skill: ${esc(q.skill)}</span>` : ''}
      <span class="pill" style="background:#FEF3C7;color:#92400E">All choices historically accurate</span>
    </div>`;

    const choicesHtml = (q.choices || []).map(ch => {
      let cls = 'choice-btn';
      let badgeCls = 'letter-badge';
      if (revealed) {
        if (ch.letter === q.correct) { cls += ' correct'; badgeCls += ' correct'; }
        else if (ch.letter === selected) { cls += ' wrong'; badgeCls += ' wrong'; }
        else { cls += ' dimmed'; badgeCls += ' dimmed'; }
      } else if (ch.letter === selected) {
        cls += ' selected';
      }
      const check = revealed && ch.letter === q.correct ? ' ✓' : revealed && ch.letter === selected ? ' ✗' : '';
      return `<button class="${cls}" style="--choice-color:${u.color}" onclick="chooseAnswer('${ch.letter}')" ${revealed?'disabled':''}>
        <div class="${badgeCls}">${ch.letter}</div>
        <div>${esc(ch.text)}${check}</div>
      </button>`;
    }).join('');

    const explanationHtml = revealed ? `
      <div class="explanation-box">
        <div class="explanation-title">${selected === q.correct ? '✓ Correct!' : '✗ Incorrect'} — Full Explanation</div>
        <div class="explanation-text">${esc(q.explanation)}</div>
        ${q.theme_connection ? `<div class="theme-connection"><strong style="color:${topic.themeColor}">AP Theme:</strong> ${esc(q.theme_connection)}</div>` : ''}
        ${q.essay_angle ? `<div class="essay-angle"><strong>Essay angle:</strong> ${esc(q.essay_angle)}</div>` : ''}
      </div>
      <div class="study-tip"><strong>Study tip:</strong> Every choice above states real history. Wrong choices are wrong only because they describe different causes, effects, or connections — exactly how the AP exam tests you.</div>` : '';

    const navHtml = revealed
      ? `<div class="nav-btns">
          <button onclick="drillSame()" class="btn" style="background:${u.color};color:white;flex:1;font-size:14px">🔁 Another from this topic</button>
          <button onclick="goUnit(${u.id})" class="btn" style="background:#6D28D9;color:white;flex:1;font-size:14px">📚 Pick new topic</button>
         </div>`
      : `<div class="nav-hint">${selected ? '' : 'Select an answer choice above'}</div>`;

    mainContent = `
      <div class="question-card">
        ${pillsHtml}
        <p class="question-text">${esc(q.question)}</p>
      </div>
      <div class="choices">${choicesHtml}</div>
      ${explanationHtml}
      ${navHtml}`;
  }

  const notesHtml = showNotes
    ? renderNotesSummary(u, topic)
    : `<div style="margin-bottom:10px"><button onclick="toggleNotes()" class="btn btn-outline" style="font-size:12px;padding:6px 12px;color:${u.color};border-color:${u.color}">Show Study Notes</button></div>`;
  const notesToggle = showNotes && q && !loading
    ? `<div style="margin-bottom:10px"><button onclick="toggleNotes()" class="btn btn-outline" style="font-size:12px;padding:6px 12px;color:${u.color};border-color:${u.color}">Hide Notes</button></div>`
    : '';

  return `
    <div class="quiz-header" style="background:${u.color}">
      <button onclick="goUnit(${u.id})" class="btn btn-ghost" style="font-size:12px;padding:5px 12px">← Back</button>
      <div class="quiz-header-center">
        <div style="font-size:10px;opacity:0.7;letter-spacing:1px">${u.period} · Topic ${topic.id}</div>
        <div style="font-weight:600;font-size:13px">${esc(topic.title)}</div>
      </div>
      ${scorePanel}
    </div>
    <div class="quiz-body">
      ${tabBar}
      ${notesHtml}${notesToggle}
      ${mainContent}
    </div>`;
}

function renderEssay() {
  const u = state.selectedUnit;
  const { essayPrompts: p, loading, error } = state;

  let content = '';
  if (loading) {
    content = `<div class="loading-box"><div class="loading-icon">📝</div><div style="font-weight:500">Generating essay prompts…</div></div>`;
  } else if (error) {
    content = `<div class="error-box"><p>${esc(error)}</p><button onclick="loadEssay()" class="btn btn-primary">Try Again</button></div>`;
  } else if (p) {
    const cards = [
      { key:'leq', label:'LEQ — Long Essay Question', color:'#6D28D9', icon:'📜',
        html: `<p class="essay-prompt">${esc(p.leq.prompt)}</p>
               <div class="essay-meta" style="background:#F5F3FF;color:#5B21B6;margin-bottom:6px"><strong>Thinking Skill:</strong> ${esc(p.leq.skill)}</div>
               <div class="essay-meta" style="background:#FFF8ED;color:#6B5A3A"><strong>Argument tip:</strong> ${esc(p.leq.tip)}</div>` },
      { key:'saq', label:'SAQ — Short Answer Question', color:'#059669', icon:'✍️',
        html: `<p class="essay-prompt">${esc(p.saq.prompt)}</p>
               <div class="essay-meta" style="background:#F0FDF4;color:#14532D"><strong>Context needed:</strong> ${esc(p.saq.context)}</div>` },
      { key:'dbq', label:'DBQ — Document Based Question Angle', color:'#D97706', icon:'📂',
        html: `<p style="font-size:14px;color:var(--navy);margin-bottom:10px"><strong>Theme:</strong> ${esc(p.dbq.theme)}</p>
               <div class="doc-tags">${(p.dbq.document_types||[]).map(d=>`<span class="doc-tag">${esc(d)}</span>`).join('')}</div>
               <div class="essay-meta" style="background:#FFF8ED;color:#6B5A3A;margin-top:8px"><strong>Argument approach:</strong> ${esc(p.dbq.argument_tip)}</div>` },
    ];
    content = `<div class="essay-cards">${cards.map(c=>`
      <div class="essay-card" style="border-left-color:${c.color}">
        <div class="essay-card-type" style="color:${c.color}">${c.icon} ${c.label}</div>
        ${c.html}
      </div>`).join('')}</div>`;
  }

  return `
    <div class="unit-header" style="background:${u.color};padding:14px 22px">
      <button onclick="goUnit(${u.id})" class="btn btn-ghost" style="margin-bottom:10px;font-size:12px">← Back to Unit</button>
      <div style="font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.65);text-transform:uppercase">${u.period}</div>
      <h2 style="font-family:'Lora',serif;font-size:22px;margin:4px 0 0">Essay Prompts</h2>
    </div>
    <div style="max-width:740px;margin:0 auto;padding:20px 18px">${content}</div>`;
}

function renderMissed() {
  const { missed } = state;
  if (!missed.length) return `
    <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px;text-align:center">
      <div style="font-size:40px;margin-bottom:16px">🎉</div>
      <h2 style="font-family:'Lora',serif;color:var(--navy);margin-bottom:8px">No missed questions!</h2>
      <p style="color:var(--muted);margin-bottom:20px">Keep drilling to build more questions.</p>
      <button onclick="goHome()" class="btn btn-primary">← Back to Home</button>
    </div>`;

  const items = missed.map((m, i) => `
    <div class="missed-item">
      <div class="missed-label" style="color:${m.unit?.color||'#EF4444'}">${esc(m.unit?.period||'?')} — ${esc(m.topic?.title||'?')}</div>
      <p class="missed-question">${esc((m.question?.question||'').slice(0,150))}…</p>
      <div class="missed-answer">Correct: <strong>${esc(m.question?.correct||'?')}</strong></div>
    </div>`).join('');

  return `
    <div style="background:var(--navy);color:white;padding:14px 22px">
      <button onclick="goHome()" class="btn btn-ghost" style="margin-bottom:10px;font-size:12px">← Home</button>
      <h2 style="font-family:'Lora',serif;font-size:22px;margin:0">🔄 Missed Questions (${missed.length})</h2>
      <p style="margin:4px 0 0;opacity:0.7;font-size:13px">Drill what you got wrong until it sticks.</p>
    </div>
    <div style="max-width:720px;margin:0 auto;padding:18px 16px">
      <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
        <button onclick="drillMissed()" class="btn" style="background:#EF4444;color:white;font-size:14px">Drill Missed Questions →</button>
        <button onclick="clearMissed()" class="btn btn-outline" style="color:var(--muted);border-color:var(--muted);font-size:13px">Clear All</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px">${items}</div>
    </div>`;
}

// ─── Main render ───────────────────────────────────────────────────────────
function render() {
  const app = document.getElementById('app');
  if (!app) return;
  switch (state.view) {
    case 'home':   app.innerHTML = renderHome(); break;
    case 'unit':   app.innerHTML = renderUnit(); break;
    case 'quiz':   app.innerHTML = renderQuiz(); break;
    case 'essay':  app.innerHTML = renderEssay(); break;
    case 'missed': app.innerHTML = renderMissed(); break;
    case 'history': app.innerHTML = renderHistory(); break;
    default: app.innerHTML = renderHome();
  }
}

// ─── Navigation ────────────────────────────────────────────────────────────
window.goHome = () => { state.view = 'home'; state.selectedUnit = null; state.selectedTopic = null; render(); };
window.goUnit = (id) => {
  state.selectedUnit = state.units.find(u => u.id === id);
  if (!state.selectedUnit) return;
  state.view = 'unit';
  render();
};
window.toggleOverview = (id) => {
  const body = document.getElementById(`overview-body-${id}`);
  const btn = document.getElementById(`overview-toggle-${id}`);
  if (!body || !btn) return;
  const collapsed = body.style.maxHeight === '80px';
  body.style.maxHeight = collapsed ? '1000px' : '80px';
  btn.textContent = collapsed ? 'Show less ▴' : 'Show more ▾';
};
window.toggleOverview = window.toggleOverview;
window.goTopic = async (topicId, mode = 'drill') => {
  const topic = state.selectedUnit?.topics.find(t => t.id === topicId);
  if (!topic) return;
  state.selectedTopic = topic;
  state.topicView = mode;
  state.view = 'quiz';
  state.question = null;
  state.selected = null;
  state.revealed = false;
  state.error = null;
  state.showNotes = true;

  if (mode === 'notes') { render(); return; }

  state.loading = true;
  render();
  try {
    state.question = await generateQuestion(state.selectedUnit, topic);
    state.loading = false;
  } catch(e) {
    state.loading = false;
    state.error = e.message.includes('No API key')
      ? 'Please set your API key (gear icon)' : e.message;
  }
  render();
};
window.goEssay = () => {
  state.view = 'essay';
  state.essayPrompts = null;
  state.error = null;
  state.loading = true;
  render();
  loadEssay();
};
window.loadEssay = async () => {
  state.loading = true; state.error = null; render();
  try {
    state.essayPrompts = await generateEssayPrompts(state.selectedUnit);
    state.loading = false;
  } catch(e) {
    state.loading = false;
    state.error = e.message;
  }
  render();
};
window.goMissed = () => { state.view = 'missed'; render(); };
window.goHistory = () => { state.view = 'history'; state.historyFilter = 'all'; render(); };
window.chooseAnswer = (letter) => {
  if (state.revealed || !state.question) return;
  state.selected = letter;
  state.revealed = true;
  const correct = letter === state.question.correct;
  state.sessionScore.c += correct ? 1 : 0;
  state.sessionScore.t += 1;
  updateProgress(state.selectedUnit.id, state.selectedTopic.id, correct);
  if (!correct) addMissed(state.selectedUnit, state.selectedTopic, state.question);

  // Save to history
  const histEntry = {
    topicId: state.selectedTopic.id,
    unitId: state.selectedUnit.id,
    topicTitle: state.selectedTopic.title,
    unitPeriod: state.selectedUnit.period,
    unitColor: state.selectedUnit.color,
    question: state.question,
    selected: letter,
    correct,
    timestamp: Date.now(),
  };
  state.questionHistory = [histEntry, ...state.questionHistory].slice(0, 200);
  save('apush_q_history', state.questionHistory);

  render();
};

window.drillSame = () => goTopic(state.selectedTopic.id);
window.retryQuestion = () => goTopic(state.selectedTopic.id);
window.toggleNotes = () => { state.showNotes = !state.showNotes; render(); };

window.startFullDrill = () => {
  const pool = []; state.units.forEach(u => { for(let i=0;i<u.weight;i++) pool.push(u); });
  const u = pool[Math.floor(Math.random()*pool.length)];
  const t = u.topics[Math.floor(Math.random()*u.topics.length)];
  state.selectedUnit = u;
  goTopic(t.id);
};

window.drillMissed = () => {
  if (!state.missed.length) return;
  const m = state.missed[Math.floor(Math.random()*state.missed.length)];
  const u = state.units.find(x=>x.id===m.unit.id);
  if (!u) return;
  const t = u.topics.find(x=>x.id===m.topic.id);
  if (!t) return;
  state.selectedUnit = u;
  goTopic(t.id);
};

window.clearMissed = () => {
  if (!confirm('Clear all missed questions?')) return;
  state.missed = []; save('apush_missed', []);
  render();
};

// ─── Settings ──────────────────────────────────────────────────────────────
const settingsBtn = document.createElement('button');
settingsBtn.className = 'settings-btn';
settingsBtn.textContent = '⚙';
settingsBtn.title = 'API Key Settings';
settingsBtn.onclick = () => {
  document.getElementById('apiKeyModal').style.display = 'flex';
  const inp = document.getElementById('apiKeyInput');
  if (inp) inp.value = getApiKey();
};
document.body.appendChild(settingsBtn);

// ─── Init ──────────────────────────────────────────────────────────────────
async function init() {
  // Load units data
  try {
    const r = await fetch('src/data/fiveable_raw.json');
    if (r.ok) state.fiveableRaw = await r.json();
  } catch {}
  try {
    const r = await fetch('src/data/heimler_raw.json');
    if (r.ok) state.heimlerRaw = await r.json();
  } catch {}
  try {
    const r = await fetch('src/data/question_bank.json');
    if (r.ok) state.questionBank = await r.json();
  } catch {}
  try {
    const r = await fetch('src/data/unit_overviews.json');
    if (r.ok) state.unitOverviews = await r.json();
  } catch {}
  try {
    const res = await fetch('src/data/units.json');
    const data = await res.json();
    state.units = data.units;
  } catch(e) {
    document.getElementById('app').innerHTML = `<div style="padding:40px;text-align:center;color:red">
      <h2>Failed to load units.json</h2><p>${e.message}</p>
      <p>Make sure you are running from a local server or GitHub Pages, not directly from the filesystem.</p>
    </div>`;
    return;
  }

  // Load optional pre-fetched notes
  try {
    const r = await fetch('src/data/fiveable_notes.json');
    if (r.ok) state.fiveableNotes = await r.json();
  } catch {}
  try {
    const r = await fetch('src/data/heimler_notes.json');
    if (r.ok) state.heimlerNotes = await r.json();
  } catch {}

  // Check API key
  if (!getApiKey()) {
    document.getElementById('apiKeyModal').style.display = 'flex';
  }

  render();
}

function renderHistory() {
  const { questionHistory } = state;
  if (!questionHistory.length) return `
    <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px;text-align:center">
      <div style="font-size:40px;margin-bottom:16px">📭</div>
      <h2 style="font-family:'Lora',serif;color:var(--navy);margin-bottom:8px">No history yet</h2>
      <p style="color:var(--muted);margin-bottom:20px">Start drilling to build your question history.</p>
      <button onclick="goHome()" class="btn btn-primary">← Back to Home</button>
    </div>`;

  const wrongOnly = state.historyFilter === 'wrong';
  const filtered = wrongOnly ? questionHistory.filter(h => !h.correct) : questionHistory;

  const items = filtered.slice(0, 100).map(h => {
    const date = new Date(h.timestamp).toLocaleDateString();
    const correctChoice = h.question?.choices?.find(c => c.letter === h.question?.correct);
    const selectedChoice = h.question?.choices?.find(c => c.letter === h.selected);
    return `
      <div style="background:var(--surface);border:1px solid ${h.correct?'var(--ok-border)':'var(--err-border)'};
                  border-left:5px solid ${h.correct?'var(--ok-border)':'var(--err-border)'};
                  border-radius:8px;padding:14px 16px;margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span style="font-size:10px;color:${h.unitColor};font-weight:700;text-transform:uppercase;letter-spacing:1px">
            ${esc(h.unitPeriod)} — Topic ${h.topicId}: ${esc(h.topicTitle)}
          </span>
          <span style="font-size:11px;color:var(--muted)">${date}</span>
        </div>
        <p style="font-family:'Lora',serif;font-size:13px;color:var(--navy);line-height:1.6;margin-bottom:8px">
          ${esc((h.question?.question||'').slice(0,180))}…
        </p>
        <div style="font-size:12px;color:${h.correct?'var(--ok)':'var(--err)'}">
          ${h.correct ? '✓ Correct' : `✗ You chose ${h.selected}: "${esc(selectedChoice?.text?.slice(0,60))}…"`}
        </div>
        ${!h.correct && correctChoice ? `
          <div style="font-size:12px;color:var(--ok);margin-top:3px">
            ✓ Answer was ${h.question.correct}: "${esc(correctChoice.text.slice(0,70))}…"
          </div>` : ''}
      </div>`;
  }).join('');

  return `
    <div style="background:var(--navy);color:white;padding:14px 22px">
      <button onclick="goHome()" class="btn btn-ghost" style="margin-bottom:10px;font-size:12px">← Home</button>
      <h2 style="font-family:'Lora',serif;font-size:22px;margin:0">📚 Question History</h2>
      <p style="margin:4px 0 0;opacity:0.7;font-size:13px">${questionHistory.length} questions answered</p>
    </div>
    <div style="max-width:720px;margin:0 auto;padding:18px 16px">
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <button onclick="state.historyFilter='all';render()" class="btn"
          style="background:${!wrongOnly?'var(--navy)':'white'};color:${!wrongOnly?'white':'var(--navy)'};border:2px solid var(--navy)">
          All (${questionHistory.length})
        </button>
        <button onclick="state.historyFilter='wrong';render()" class="btn"
          style="background:${wrongOnly?'#DC2626':'white'};color:${wrongOnly?'white':'#DC2626'};border:2px solid #DC2626">
          Wrong only (${questionHistory.filter(h=>!h.correct).length})
        </button>
        <button onclick="if(confirm('Clear history?')){state.questionHistory=[];save('apush_q_history',[]);render()}" 
          class="btn btn-outline" style="color:var(--muted);border-color:var(--muted);font-size:12px;margin-left:auto">
          Clear
        </button>
      </div>
      ${items || '<p style="color:var(--muted);text-align:center;padding:32px">No questions match this filter.</p>'}
    </div>`;
}

init();
