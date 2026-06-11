const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3000;


const MODEL_NAME = 'claude-haiku-4-5-20251001';
const ALLOWED_ORIGIN = '*';
const DOCS_FOLDER = __dirname;

const anthropic = new Anthropic();

// ============================================================
// BLOCKED IPS / PREFIXES - anyone whose IP equals OR starts with an
// entry here is denied. Watch the terminal to see each visitor's IP.
//   IPv4: use the full address, e.g. '203.0.113.45'
//   IPv6: use the first 4 groups (the /64) so it still works when the
//         address rotates, e.g. '2601:201:8a87:9d00'
// ============================================================
const BLOCKED_IPS = [
  
  // '203.0.113.45',
];

app.use(cors({ origin: ALLOWED_ORIGIN }));
app.use(express.json());

function clientIp(req) {
  const fwd = (req.headers['x-forwarded-for'] || '').split(',')[0].trim();
  return fwd || req.socket.remoteAddress || 'unknown';
}

// Log every visitor and block anyone on the BLOCKED_IPS list
app.use((req, res, next) => {
  const ip = clientIp(req);
  console.log(`[${new Date().toLocaleTimeString()}] ${ip}  ${req.method} ${req.path}`);
  if (BLOCKED_IPS.some(b => ip === b || ip.startsWith(b))) {
    console.log(`  -> blocked ${ip}`);
    res.status(403);
    return res.end('Access denied.');
  }
  next();
});

// Friendly names so Claude knows which department each file belongs to.
const DOC_LABELS = {
  'accendere.txt': 'Accendere Corporation',
  'armed_forces.txt': 'Armed Forces',
  'army.txt': 'Department of the Army (UCMJ)',
  'bb.txt': 'Boosted Boiz (BB)',
  'bse.txt': 'Bureau of Special Enforcement (BSE)',
  'business.txt': 'CALIRP Businesses',
  'cartel.txt': 'Cartel Coordination / Cartels Handbook',
  'civilian.txt': 'Civilian Punishment Guidelines',
  'codes.txt': '10-Codes and NATO Phonetic Alphabet',
  'gang.txt': 'Gang Management / Gang Community Handbook',
  'gsop.txt': 'Global Standard Operating Procedures (GSOP)',
  'leo.txt': 'LEO Member Punishment Guidelines',
  'metro.txt': 'Metro Police Department (MPD / Metro)',
  'ncea.txt': 'National Criminal Enforcement Agency (NCEA)',
  'nsb.txt': 'National Security Bureau (NSB)',
  'overdrive.txt': 'Overdrive',
  'pilots.txt': 'Pilots License & Vehicle Roster',
  'rhpd.txt': 'Rockford Hills Police Department (RHPD)',
  'safr.txt': 'SAFR / EMS',
  'sahp.txt': 'San Andreas Highway Patrol (SAHP)',
  'satf.txt': 'San Andreas Task Force (SATF)',
  'sbo.txt': 'Special Bureau Operations (SBO)',
  'sbpd.txt': 'South Beach Police Department (SBPD)',
  'staff.txt': 'Staff Punishment Guidelines',
  'talon_security.txt': 'Talon Security',
  'verified_civilian.txt': 'Verified Civilian',
  'vo.txt': 'Volunteer Officer (VO)',
  'weazel_news.txt': 'Weazel News'
};

function loadDocs() {
  try {
    const files = fs.readdirSync(DOCS_FOLDER).filter(f => f.endsWith('.txt')).sort();
    let combined = '';
    for (const file of files) {
      const content = fs.readFileSync(path.join(DOCS_FOLDER, file), 'utf8');
      const label = DOC_LABELS[file] || file.replace('.txt', '');
      combined += `\n\n<document department="${label}" file="${file}">\n${content}\n</document>`;
    }
    return combined;
  } catch (err) {
    console.error('Error loading docs:', err.message);
    return '';
  }
}

function buildCodeMap(docs) {
  const map = {};
  const re = /(?:^|\n)\s*((?:10|11)-\d+|CODE\s+\d+|SIGNAL\s+\d+)\s*-\s*([^\n]+)/gi;
  let m;
  while ((m = re.exec(docs)) !== null) {
    const key = m[1].toUpperCase().replace(/\s+/g, ' ').trim();
    map[key] = m[2].trim();
  }
  return map;
}

function buildNatoMap(docs) {
  const map = {};
  const re = /\b([A-Z])\s*-\s*([A-Z][a-z-]+)\b/g;
  let m;
  while ((m = re.exec(docs)) !== null) {
    map[m[1].toUpperCase()] = m[2];
  }
  return map;
}

// Parse "Offense: 1st ... -> 2nd ..." style punishment lines from every section.
function buildPunishments(docs) {
  const out = [];
  const lines = docs.split('\n');
  let section = 'General';
  const punish = /(perm|permanent|ban|strike|suspension|suspend|jail|kick|warning|mute|terminat|blacklist|strip|demot|revoked|global ban|→)/i;
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const fileMark = line.match(/^<document department="(.+?)"/i);
    if (fileMark) { section = fileMark[1]; continue; }
    if (/(OFFENSES|PUNISHMENTS|PUNISHMENT GUIDELINES)\b/i.test(line) && !/→/.test(line)) {
      const m2 = line.match(/^([A-Za-z][^:]{0,60}?):\s*(.+)$/);
      if (!(m2 && punish.test(m2[2]))) { section = line.replace(/[:]+$/, '').trim(); continue; }
    }
    const m = line.match(/^([A-Za-z][^:]{0,60}?):\s*(.+)$/);
    if (m && punish.test(m[2])) {
      out.push({ section, label: m[1].trim(), value: m[2].trim() });
    }
  }
  return out;
}

const STOP = new Set(['what','is','are','the','for','of','a','an','to','do','i','if','get','when','whats','punishment','punishments','penalty','penalties','rule','rules','against','happens','happen','you','your','my','me','will','can','about','consequence','consequences','in','on','and','or','it','that','this','how','long','much','many','there','any','s','does','being']);

function normWords(s) {
  return s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w && !STOP.has(w));
}

function wordMatch(a, b) {
  if (a === b) return true;
  if (a.length >= 5 && b.length >= 5 && a.slice(0, 5) === b.slice(0, 5)) return true;
  if (a.length >= 4 && (a.includes(b) || b.includes(a))) return true;
  return false;
}

function punishmentLookup(query, punishments) {
  const q = query.toLowerCase();
  const intent = /(punish|penalt|consequence|happen|ban|banned|in trouble|get for|\brule|strike|suspend|suspension|jail|kick|mute|demot|terminat|blacklist|offens|offenc|how long|trouble)/i.test(q);
  if (!intent) return null;
  const qWords = normWords(query);
  if (!qWords.length) return null;
  let best = [], bestScore = 0;
  for (const p of punishments) {
    const lw = normWords(p.label);
    if (!lw.length) continue;
    let hit = 0;
    for (const w of lw) if (qWords.some(qw => wordMatch(w, qw))) hit++;
    const ratio = hit / lw.length;
    if (hit > 0 && ratio >= 0.5) {
      if (hit > bestScore) { bestScore = hit; best = [p]; }
      else if (hit === bestScore) best.push(p);
    }
  }
  if (!best.length) return null;
  const seen = new Set(), uniq = [];
  for (const p of best) {
    const k = p.label + '|' + p.value;
    if (!seen.has(k)) { seen.add(k); uniq.push(p); }
  }
  return uniq.map(p => `${p.label}: ${p.value}`).join('\n');
}

function deterministicAnswer(query, codeMap, natoMap, punishments) {
  const q = query.toLowerCase();

  // Specific 10-/11- code
  let m = q.match(/\b(1[01])[-\s](\d{1,2})\b/);
  if (m) {
    const key = `${m[1]}-${m[2]}`;
    if (codeMap[key]) return `${key} means: ${codeMap[key]}`;
  }
  // CODE n
  m = q.match(/\bcode\s*(\d+)\b/);
  if (m) {
    const key = `CODE ${m[1]}`;
    if (codeMap[key]) return `${key} means: ${codeMap[key]}`;
  }
  // SIGNAL n
  m = q.match(/\bsignal\s*(\d+)\b/);
  if (m) {
    const key = `SIGNAL ${m[1]}`;
    if (codeMap[key]) return `${key} means: ${codeMap[key]}`;
  }

  // "List all" style questions
  const wantsList = /\b(all|list|every|each|show)\b/.test(q) || /\bwhat are the\b/.test(q);
  if (wantsList) {
    const entries = Object.entries(codeMap);
    if (/\bsignal/.test(q)) {
      const f = entries.filter(([k]) => k.startsWith('SIGNAL'));
      if (f.length) return f.map(([k, v]) => `${k} - ${v}`).join('\n');
    }
    if (/(nato|phonetic|alphabet)/.test(q)) {
      const f = Object.entries(natoMap);
      if (f.length) return f.map(([k, v]) => `${k} - ${v}`).join('\n');
    }
    if (/\bcodes?\b/.test(q)) {
      let f = entries;
      if (/\b(10|ten|11)\b/.test(q)) f = entries.filter(([k]) => k.startsWith('10-') || k.startsWith('11-'));
      if (f.length) return f.map(([k, v]) => `${k} - ${v}`).join('\n');
    }
  }

  // NATO phonetic, single letters, only when clearly asked
  if (/(nato|phonetic|alphabet|spell)/.test(q)) {
    const letters = (query.toUpperCase().match(/\b[A-Z]\b/g) || []);
    const hits = letters.filter(l => natoMap[l]).map(l => `${l} = ${natoMap[l]}`);
    if (hits.length) return `Phonetic alphabet: ${hits.join(', ')}`;
  }

  // Punishment / offense lookup
  const punish = punishmentLookup(query, punishments);
  if (punish) return punish;

  return null;
}

// ============================================================
// Load docs ONCE at startup. The docs text must be byte-identical
// on every request so Anthropic's prompt cache can be reused.
// (Render restarts the service on every deploy, so edits to the
// .txt files still get picked up - they just require a redeploy.)
// ============================================================
// ============================================================
// LIVE REMOTE DOCS - documents that staff edit in Google Docs /
// Google Sheets. The server re-downloads these on a timer, so
// edits show up in the bot automatically WITHOUT a GitHub push.
//
// Requirements: the Google Doc/Sheet must be shared as
// "Anyone with the link can view".
//
// URL formats:
//   Google Doc:   https://docs.google.com/document/d/DOC_ID/export?format=txt
//   Google Sheet: https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0
//     (gid is the tab id - it's in the sheet's URL after #gid=)
//
// 'file' is a virtual filename - if it matches a real .txt in the
// repo, the remote version REPLACES it. If it's new, it's added.
// ============================================================
const REMOTE_DOCS = [
  // Example - uncomment and fill in your real doc IDs:
  // {
  //   file: 'sadps.txt',
  //   label: 'San Andreas Department of Public Safety (SADPS / DPS)',
  //   keywords: ['sadps', 'dps', 'public safety', 'constable'],
  //   url: 'https://docs.google.com/document/d/YOUR_DOC_ID/export?format=txt'
  // },
];
const REFRESH_MINUTES = 15;

// ============================================================
// DEPARTMENT ROUTER keywords - if the question clearly mentions
// one or more departments, send Claude ONLY those docs (plus
// GSOP and codes, which always apply). Much faster and cheaper
// than the full ~85k token doc set.
// ============================================================
const DOC_KEYWORDS = {
  'accendere.txt':         ['accendere'],
  'armed_forces.txt':      ['armed forces', 'military police', ' afsoc', 'usaf', 'air force', 'navy', 'marines', 'coast guard'],
  'army.txt':              ['army', 'ucmj', 'court martial', 'court-martial'],
  'bb.txt':                ['boosted boiz', 'boosted boyz', ' bb '],
  'bse.txt':               ['bse', 'bureau of special enforcement'],
  'business.txt':          ['business', 'businesses', 'store owner', 'shop owner'],
  'cartel.txt':            ['cartel'],
  'civilian.txt':          ['civilian punishment', 'civ punishment'],
  'gang.txt':              ['gang'],
  'leo.txt':               ['leo punishment', 'officer punishment'],
  'metro.txt':             ['metro', 'mpd'],
  'ncea.txt':              ['ncea', 'criminal enforcement agency'],
  'nsb.txt':               ['nsb', 'national security bureau'],
  'overdrive.txt':         ['overdrive'],
  'pilots.txt':            ['pilot', 'aircraft', 'helicopter', 'airplane', 'plane', 'aviation'],
  'rhpd.txt':              ['rhpd', 'rockford'],
  'safr.txt':              ['safr', 'ems', 'fire', 'paramedic', 'medic', 'ambulance'],
  'sahp.txt':              ['sahp', 'highway patrol', 'trooper', 'state police'],
  'satf.txt':              ['satf', 'task force'],
  'sbo.txt':               ['sbo', 'special bureau'],
  'sbpd.txt':              ['sbpd', 'south beach'],
  'staff.txt':             ['staff'],
  'talon_security.txt':    ['talon'],
  'verified_civilian.txt': ['verified civilian', 'verified civ'],
  'vo.txt':                ['volunteer officer', ' vo ', 'vo charger'],
  'weazel_news.txt':       ['weazel', 'news', 'reporter', 'journalist'],
};
const ALWAYS_INCLUDE = ['gsop.txt', 'codes.txt']; // small, apply to everyone

// merge labels/keywords from REMOTE_DOCS into the maps
for (const r of REMOTE_DOCS) {
  if (r.label) DOC_LABELS[r.file] = r.label;
  if (r.keywords) DOC_KEYWORDS[r.file] = r.keywords;
}

// ============================================================
// Knowledge state - rebuilt at startup and whenever a remote
// doc changes. These are `let` because they get replaced.
// ============================================================
let DOC_FILES = {};      // file -> wrapped <document> text
let DOCS = '';           // all docs combined
let CODE_MAP = {};
let NATO_MAP = {};
let PUNISHMENTS = [];
let SYSTEM_BLOCKS = [];

const remoteCache = {};  // file -> last successfully fetched raw text

function wrapDoc(file, content) {
  const label = DOC_LABELS[file] || file.replace('.txt', '');
  return `\n\n<document department="${label}" file="${file}">\n${content}\n</document>`;
}

function rebuild() {
  const newFiles = {};
  // 1) local .txt files from the repo
  for (const file of fs.readdirSync(DOCS_FOLDER).filter(f => f.endsWith('.txt')).sort()) {
    newFiles[file] = wrapDoc(file, fs.readFileSync(path.join(DOCS_FOLDER, file), 'utf8'));
  }
  // 2) remote docs override/add (only ones that have fetched successfully)
  for (const r of REMOTE_DOCS) {
    if (remoteCache[r.file]) newFiles[r.file] = wrapDoc(r.file, remoteCache[r.file]);
  }
  DOC_FILES = newFiles;
  DOCS = Object.keys(newFiles).sort().map(f => newFiles[f]).join('');
  CODE_MAP = buildCodeMap(DOCS);
  NATO_MAP = buildNatoMap(DOCS);
  PUNISHMENTS = buildPunishments(DOCS);
  SYSTEM_BLOCKS = [
    { type: 'text', text: INSTRUCTIONS },
    { type: 'text', text: `Reference text:\n${DOCS}`, cache_control: { type: 'ephemeral' } }
  ];
  console.log(`Knowledge rebuilt: ${Object.keys(newFiles).length} docs, ~${Math.round(DOCS.length / 4)} tokens`);
}

async function refreshRemoteDocs() {
  let changed = false;
  for (const r of REMOTE_DOCS) {
    try {
      const resp = await fetch(r.url, { redirect: 'follow' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const text = (await resp.text()).trim();
      if (!text) throw new Error('empty response');
      if (text !== remoteCache[r.file]) {
        remoteCache[r.file] = text;
        changed = true;
        console.log(`Remote doc updated: ${r.file} (${text.length} chars)`);
      }
    } catch (err) {
      // keep the last good copy - never wipe knowledge on a failed fetch
      console.error(`Remote fetch failed for ${r.file}: ${err.message}`);
    }
  }
  if (changed) rebuild();
}

function routeDocs(query) {
  const q = ' ' + query.toLowerCase().replace(/[^a-z0-9 ]/g, ' ') + ' ';
  const hits = [];
  for (const [file, keys] of Object.entries(DOC_KEYWORDS)) {
    if (keys.some(k => q.includes(k))) hits.push(file);
  }
  if (!hits.length) return null; // no department detected -> use full docs
  const set = [...new Set([...ALWAYS_INCLUDE, ...hits])];
  return set.map(f => DOC_FILES[f]).filter(Boolean).join('');
}

const INSTRUCTIONS = 'You are an assistant for California Roleplay (CALIRP), a GTA roleplay server. Answer ONLY using the reference documents below. Do not use any real-world knowledge. Do not invent or add anything not written in the reference documents. If the answer is genuinely not in the reference documents, reply exactly: "That is not in our documents." Keep answers short and quote rules and definitions as written.\n\nIMPORTANT: Each document is wrapped in a <document> tag stating which department it belongs to. Many departments have sections with identical names (for example, VEHICLE STRUCTURE exists in RHPD, NCEA, SBO, VO, and Armed Forces). When the user mentions a department (by name or abbreviation like RHPD, SAHP, SBPD, NSB, NCEA, SBO, VO, BSE, SATF, MPD/Metro, SAFR, BB), you MUST answer only from that department\'s document and say which department you are quoting. If the question matches sections in multiple departments and the user did not specify one, list the departments that have that section and ask which one they mean.';

// initial build from local files, then start the remote refresh loop
rebuild();
refreshRemoteDocs();
setInterval(refreshRemoteDocs, REFRESH_MINUTES * 60 * 1000);

app.get('/status', (req, res) => {
  res.json({ status: 'Proxy is running', model: MODEL_NAME });
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.post('/chat', async (req, res) => {
  const { message } = req.body;

  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Missing or invalid message' });
  }

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache');

  // 1) Exact, no-AI answer first (codes, signals, phonetics, punishments) - instant
  const direct = deterministicAnswer(message, CODE_MAP, NATO_MAP, PUNISHMENTS);
  if (direct) {
    res.write(direct);
    return res.end();
  }

  // 2) Otherwise Claude answers, constrained to the docs, streamed token-by-token.
  //    If the question names a department, send only that department's docs
  //    (small + fast). Otherwise send the full cached document set.
  const routed = routeDocs(message);
  const system = routed
    ? [{ type: 'text', text: INSTRUCTIONS }, { type: 'text', text: `Reference text:\n${routed}` }]
    : SYSTEM_BLOCKS;
  console.log(`  -> ${routed ? `routed prompt (~${Math.round(routed.length / 4)} tokens)` : 'full docs (cached)'}`);

  try {
    const stream = anthropic.messages.stream({
      model: MODEL_NAME,
      max_tokens: 1024,
      system,
      messages: [{ role: 'user', content: message }]
    });

    stream.on('text', (text) => res.write(text));
    const final = await stream.finalMessage();
    console.log(`  -> cache: wrote ${final.usage.cache_creation_input_tokens || 0}, read ${final.usage.cache_read_input_tokens || 0}, input ${final.usage.input_tokens}`);
    res.end();

  } catch (err) {
    console.error('Claude error:', err.message);
    if (!res.headersSent) res.status(500);
    res.write('Could not reach the AI.');
    res.end();
  }
});

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`);
  console.log(`Loaded docs from: ${DOCS_FOLDER}`);
  console.log(`Using Claude model: ${MODEL_NAME}`);
});
