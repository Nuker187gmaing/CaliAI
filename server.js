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
  // ---- SADPS / DPS ----
  { file: 'sadps_sop.txt',   label: 'San Andreas Department of Public Safety (SADPS / DPS) - SOP',
    keywords: ['sadps', ' dps ', 'public safety', 'constable'],
    url: 'https://docs.google.com/document/d/14aP3J0sQuwZo5QrRv-oEveneSoyDeSezABjM6YFF0mk/export?format=txt' },
  { file: 'sadps_promo.txt', label: 'San Andreas Department of Public Safety (SADPS / DPS) - Promotional Guidelines',
    keywords: ['sadps', ' dps ', 'public safety', 'constable'],
    url: 'https://docs.google.com/document/d/1jlu2LdqBWW81o35fvlrghIWt5d50UazP2QFeZOKp2v0/export?format=txt' },
  { file: 'sadps_roster.txt', fallback: false, maxChars: 120000, label: 'San Andreas Department of Public Safety (SADPS / DPS) - Roster',
    keywords: ['sadps', ' dps ', 'public safety', 'constable'],
    url: 'https://docs.google.com/spreadsheets/d/1ogQQ0wwUbl53e9tNcKUvO0xC5eVXtdeR3WjzA73nzeQ/export?format=csv&gid=0' },

  // ---- Global / staff-wide (replace repo files) ----
  { file: 'gsop.txt',       label: 'Global Standard Operating Procedures (GSOP)',
    url: 'https://docs.google.com/document/d/1ZfhE0RDj036Y6b56QJq_0KF0r-fl0dbNF7FZvyk5H64/export?format=txt' },
  { file: 'staff_handbook.txt', label: 'CaliRP Staff Handbook',
    keywords: ['staff handbook', 'staff member', 'staff'],
    url: 'https://docs.google.com/document/d/1gRgax7wtt841W349AckvrFn-tVtjaa4mQ9k52Fn_1o8/export?format=txt' },
  { file: 'staff.txt',      label: 'Staff Punishment Guidelines',
    url: 'https://docs.google.com/spreadsheets/d/1APREBIhQvvf3QaYDRiwfWuUYuWiqAih258WMutGK7Hg/export?format=csv&gid=0' },
  { file: 'civilian.txt',   label: 'Civilian Punishment Guidelines',
    url: 'https://docs.google.com/spreadsheets/d/1KqE5hLDxYykBlFMe3lXYFAVAILgL-jmETlFCEB_8dMk/export?format=csv&gid=0' },

  // ---- NSB ----
  { file: 'nsb.txt',        label: 'National Security Bureau (NSB) - Promotion & Activity Guidelines',
    url: 'https://docs.google.com/document/d/1LUDucT2vL1_kWwv93l1xXgIKzIMr2JzOeCaerI6EoZg/export?format=txt' },
  { file: 'nsb_roster.txt', fallback: false, maxChars: 120000, label: 'National Security Bureau (NSB) - Main Roster',
    keywords: ['nsb', 'national security bureau'],
    url: 'https://docs.google.com/spreadsheets/d/18DwC2kvAiiMGuJJXVUbFMd2Y8bqVJcVr8nWNWdUaP8E/gviz/tq?tqx=out:csv' },
  { file: 'sahp_roster.txt', fallback: false, maxChars: 120000, label: 'San Andreas Highway Patrol (SAHP) - Roster',
    keywords: ['sahp', 'highway patrol', 'trooper'],
    url: 'https://docs.google.com/spreadsheets/d/1cXoXqaQhEudManLVSfAVIxy6v5Z5lZ0pLgU_9kDdL68/export?format=csv&gid=1752215197' },
  { file: 'nsb_air_coastal.txt', label: 'NSB Air and Coastal Division - Training SOP',
    keywords: ['nsb', 'air and coastal', 'air coastal', 'acd'],
    url: 'https://docs.google.com/document/d/1GLzfQI3A4_IKHlVClNV7c7CxQrKTroDaTUpbXfUijRM/export?format=txt' },
  { file: 'cid.txt',        label: 'Criminal Investigation Division (CID) - GSOP',
    keywords: ['cid', 'criminal investigation'],
    url: 'https://docs.google.com/document/d/1AMJ8Nfu6Tq5IVk-wJ6KS4gc2C7rZ32KS5AZXDtW9baI/export?format=txt' },
  { file: 'trt.txt',        label: 'Tactical Response Team (TRT) - SOP',
    keywords: ['trt', 'tactical response'],
    url: 'https://docs.google.com/document/d/1qbiftXTI1Og4nu1t_DtJmcg7qYm7frWsGM8TOfZ7m3s/export?format=txt' },

  // ---- Armed Forces / Army ----
  { file: 'armed_forces.txt', label: 'Armed Forces - SOP',
    url: 'https://docs.google.com/document/d/1kLt1NQTLFFUaCF34VkT2Wb7jMsC-gPk83BmI1Nzt1jU/export?format=txt' },
  { file: 'armed_forces_db.txt', fallback: false, maxChars: 120000, label: 'Armed Forces - Database / Roster',
    keywords: ['armed forces'],
    url: 'https://docs.google.com/spreadsheets/d/14Kdwo4iBKtYtq2xWVGllmlTc7-MDnk_Zc5I4pAV3fqw/export?format=csv&gid=0' },
  { file: 'armed_forces_unicom.txt', label: 'Armed Forces - UNICOM Etiquette, Flight Paths & ATC',
    keywords: ['unicom', 'armed forces', 'flight path'],
    url: 'https://docs.google.com/document/d/1eVbXKAvbihdJ829T1n0ZcRPnVBj1uYYsJNigVEhzB9A/export?format=txt' },
  { file: 'army.txt',       label: 'Department of the Army (UCMJ) - SOP',
    url: 'https://docs.google.com/document/d/1qVviRjz2qf_-jeMAxuWY7Qopdohx-fIh1w1Mv8S7vvA/export?format=txt' },
  { file: 'army_roster.txt', fallback: false, maxChars: 120000, label: 'Army - Master Roster',
    keywords: ['army'],
    url: 'https://docs.google.com/spreadsheets/d/1draMpzn6AdEk5TNehK1qAspy0cu4-Fm_2vHkTPB_iBc/export?format=csv&gid=0' },

  // ---- Departments / civilian side ----
  { file: 'safr.txt',       label: 'SAFR / EMS - SOP',
    url: 'https://docs.google.com/document/d/1wVxSGfzpJjydkQfsqdw4eyOsK3aF0ObVfjdgVh-vfaQ/export?format=txt' },
  { file: 'pilots.txt',     label: 'Pilots License, Vehicle Roster & Rules',
    url: 'https://docs.google.com/spreadsheets/d/1eOX2MSJAzl1iMqR49Q8DN4K6GhEV9UJgP5x20kEh0sU/gviz/tq?tqx=out:csv' },
  { file: 'verified_civilian.txt', label: 'Verified Civilian - SOP',
    url: 'https://docs.google.com/document/d/1KNv8SCut5xhF5kXj8ayuBJ9RyQVG64-bqZse1jXrG8Y/export?format=txt' },
  { file: 'verified_civilian_roster.txt', fallback: false, maxChars: 120000, label: 'Verified Civilian - Master Roster',
    keywords: ['verified civilian', 'verified civ'],
    url: 'https://docs.google.com/spreadsheets/d/1qLFIxJi6Ua-dcdAAI9OONFQBA5fuHWesXK88-h1prDk/gviz/tq?tqx=out:csv' },
  { file: 'overdrive.txt',  label: 'Overdrive - SOP',
    url: 'https://docs.google.com/document/d/1DZ8rIEY8f1sf7iwBIFLmz4gnCCrgbdYq-dFUkK265oc/export?format=txt' },
  { file: 'overdrive_roster.txt', fallback: false, maxChars: 120000, label: 'Overdrive - Master Roster',
    keywords: ['overdrive'],
    url: 'https://docs.google.com/spreadsheets/d/1kPo5m04BeLpMQ7Qcr_N0uXBq7HZEYqYEXmff0yfAnnw/export?format=csv&gid=0' },
  { file: 'business.txt',   label: 'CaliRP Businesses - SOP',
    url: 'https://docs.google.com/document/d/1h_ApQ8NrCFR59cLZbc_w0UfOHkrQ7wyPa0CA7ac3mIo/export?format=txt' },
  { file: 'business_promo.txt', label: 'CaliRP Businesses - Promotional Guidelines',
    keywords: ['business', 'businesses'],
    url: 'https://docs.google.com/document/d/1FNOAzOd6M23vtGO34q72T3HijHv_Gm1hRlvkTiaHUoM/export?format=txt' },
  { file: 'atc_roster.txt', fallback: false, maxChars: 120000, label: 'American Trucking Company (ATC) - Master Roster',
    keywords: ['trucking', 'american trucking', ' atc '],
    url: 'https://docs.google.com/spreadsheets/d/1EjdPcvoAt3lNJutY4uq5ToCnA7waK3FcmvPlyuOU7so/gviz/tq?tqx=out:csv' },
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
let CALLSIGN_MAP = {};   // "1J-10" -> { name, rank, department, ... }
let SYSTEM_BLOCKS = [];

// Parse roster lines for callsigns like 1J-10, 2J-01, DPS-72, LA-01.
// Works on CSV (sheets) and space-separated (txt) roster rows.
const CALLSIGN_RE = /^(?:\d{1,2}[A-Z]{1,3}|[A-Z]{2,5})-\d{1,3}$/i;
function buildCallsigns(docFiles) {
  const map = {};
  for (const [file, wrapped] of Object.entries(docFiles)) {
    const label = DOC_LABELS[file] || file.replace('.txt', '');
    for (const raw of wrapped.split('\n')) {
      const cells = (raw.includes(',') ? raw.split(',') : raw.split(/\s{2,}|\t/))
        .map(c => c.trim().replace(/^"+|"+$/g, '').trim()).filter(Boolean);
      if (!cells.length || !CALLSIGN_RE.test(cells[0])) continue;
      const callsign = cells[0].toUpperCase();
      // find the name: first cell after the callsign that isn't a pure
      // number (badge/discord id) or a date
      const rest = cells.slice(1).filter(c => !/^\d+$/.test(c) && !/^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$/.test(c));
      if (!rest.length) continue; // completely empty roster slot
      // a filled row has an ID/badge number; a row with only a rank and
      // no numeric cells is an unassigned slot
      const hasId = cells.slice(1).some(c => /^\d+$/.test(c));
      const details = hasId ? rest.join(' - ') : `${rest.join(' - ')} - position currently VACANT`;
      map[callsign] = { department: label, details };
    }
  }
  return map;
}

function callsignLookup(query) {
  const m = query.toUpperCase().match(/\b((?:\d{1,2}[A-Z]{1,3}|[A-Z]{2,5})-\d{1,3})\b/);
  if (!m) return null;
  const cs = m[1];
  if (/^1[01]-/.test(cs)) return null; // 10-xx / 11-xx are radio codes, not callsigns
  const hit = CALLSIGN_MAP[cs];
  if (hit) return `${cs} (${hit.department}): ${hit.details}`;
  return null; // unknown callsign -> let Claude handle it
}

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
  // The full-docs fallback prompt excludes routing-only docs (rosters),
  // so generic questions can't blow past the model's context window.
  // Rosters are still reachable via the department router and the
  // deterministic callsign lookup.
  const routingOnly = new Set(REMOTE_DOCS.filter(r => r.fallback === false).map(r => r.file));
  const fallbackDocs = Object.keys(newFiles).sort()
    .filter(f => !routingOnly.has(f)).map(f => newFiles[f]).join('');
  CODE_MAP = buildCodeMap(DOCS);
  NATO_MAP = buildNatoMap(DOCS);
  PUNISHMENTS = buildPunishments(DOCS);
  CALLSIGN_MAP = buildCallsigns(newFiles);
  SYSTEM_BLOCKS = [
    { type: 'text', text: INSTRUCTIONS },
    { type: 'text', text: `Reference text:\n${fallbackDocs}`, cache_control: { type: 'ephemeral' } }
  ];
  console.log(`Knowledge rebuilt: ${Object.keys(newFiles).length} docs, ~${Math.round(DOCS.length / 4)} tokens total, ~${Math.round(fallbackDocs.length / 4)} tokens in fallback prompt, ${Object.keys(CALLSIGN_MAP).length} callsigns`);
}

// Clean up fetched docs: normalize line endings, drop empty CSV rows
// and "Vacant" placeholder roster rows that would waste thousands of
// tokens (roster sheets often have 800+ empty pre-numbered rows).
function sanitizeRemote(text) {
  const out = [];
  for (let line of text.replace(/\r\n?/g, '\n').split('\n')) {
    const trimmed = line.replace(/[,\s]+$/g, ''); // strip trailing empty cells
    if (!trimmed) continue;
    const cells = trimmed.split(',').map(c => c.trim().replace(/^"+|"+$/g, '').trim()).filter(Boolean);
    if (!cells.length) continue;
    // vacant placeholder row: contains "Vacant" and almost no other data
    if (cells.length <= 3 && cells.some(c => /^vacant$/i.test(c))) continue;
    out.push(trimmed);
  }
  return out.join('\n');
}

async function refreshRemoteDocs() {
  let changed = false;
  for (const r of REMOTE_DOCS) {
    try {
      const resp = await fetch(r.url, { redirect: 'follow' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      let text = sanitizeRemote((await resp.text()).trim());
      if (!text) throw new Error('empty response');
      // hard cap so one runaway sheet can't blow up the prompt
      const cap = r.maxChars || 150000;
      if (text.length > cap) {
        console.warn(`${r.file} is ${text.length} chars - truncating to ${cap}. Check that the sheet's first tab is the right one.`);
        text = text.slice(0, cap) + '\n[... document truncated due to size ...]';
      }
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

// initial build from local files, then fetch remote docs BEFORE the
// server starts taking questions (the listen call at the bottom waits
// for this promise), then keep refreshing on a timer.
rebuild();
const firstRefresh = refreshRemoteDocs();
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

  // 1) Exact, no-AI answers first (codes, signals, phonetics, punishments,
  //    roster callsigns) - instant
  const direct = deterministicAnswer(message, CODE_MAP, NATO_MAP, PUNISHMENTS)
    || callsignLookup(message);
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

firstRefresh.finally(() => {
  app.listen(PORT, () => {
    console.log(`Proxy server running on port ${PORT}`);
    console.log(`Loaded docs from: ${DOCS_FOLDER}`);
    console.log(`Using Claude model: ${MODEL_NAME}`);
  });
});
