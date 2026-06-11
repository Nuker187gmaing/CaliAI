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
const DOCS = loadDocs();
const CODE_MAP = buildCodeMap(DOCS);
const NATO_MAP = buildNatoMap(DOCS);
const PUNISHMENTS = buildPunishments(DOCS);

const SYSTEM_BLOCKS = [
  {
    type: 'text',
    text: 'You are an assistant for California Roleplay (CALIRP), a GTA roleplay server. Answer ONLY using the reference documents below. Do not use any real-world knowledge. Do not invent or add anything not written in the reference documents. If the answer is genuinely not in the reference documents, reply exactly: "That is not in our documents." Keep answers short and quote rules and definitions as written.\n\nIMPORTANT: Each document is wrapped in a <document> tag stating which department it belongs to. Many departments have sections with identical names (for example, VEHICLE STRUCTURE exists in RHPD, NCEA, SBO, VO, and Armed Forces). When the user mentions a department (by name or abbreviation like RHPD, SAHP, SBPD, NSB, NCEA, SBO, VO, BSE, SATF, MPD/Metro, SAFR, BB), you MUST answer only from that department\'s document and say which department you are quoting. If the question matches sections in multiple departments and the user did not specify one, list the departments that have that section and ask which one they mean.'
  },
  {
    type: 'text',
    text: `Reference text:\n${DOCS}`,
    cache_control: { type: 'ephemeral' } // Claude processes the docs once, then reuses the cache
  }
];

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
  //    The docs block in SYSTEM_BLOCKS is cached server-side by Anthropic, so
  //    Claude does not re-read all ~85k tokens of documents on every question.
  try {
    const stream = anthropic.messages.stream({
      model: MODEL_NAME,
      max_tokens: 1024,
      system: SYSTEM_BLOCKS,
      messages: [{ role: 'user', content: message }]
    });

    stream.on('text', (text) => res.write(text));
    await stream.finalMessage();
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
