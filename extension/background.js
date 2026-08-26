/* FF Sidekick service worker.

   The old design POSTed scraped picks to a local Python helper on
   127.0.0.1:8787. There is no helper anymore: the picks live here, in
   chrome.storage.session, and the hosted board reads them back through
   extension messaging. Everything a stranger needs is the extension plus the
   website -- no install, no server, no cookies.

   Two message channels reach this worker:
     - chrome.runtime.onMessage         from our own content scripts
     - chrome.runtime.onMessageExternal from the board page (externally_connectable)
   Both are dispatched through handle(). */

const KEY = 'ff_draft';

function normName(n) {
  n = (n || '').toLowerCase();
  const junk = [' jr.', ' jr', ' sr.', ' sr', ' iii', ' ii', ' iv', "'", '.', '-'];
  for (const j of junk) n = n.split(j).join(j.startsWith(' ') ? ' ' : '');
  return n.split(/\s+/).filter(Boolean).join(' ');
}

function emptyStore(draftId) {
  const now = Date.now();
  return { draftId: draftId || '', started: now, updated: now, picks: {} };
}

async function getStore() {
  const o = await chrome.storage.session.get(KEY);
  return o[KEY] || null;
}

async function setStore(s) {
  await chrome.storage.session.set({ [KEY]: s });
}

/* Any message from the room -- even an empty pick list -- is a heartbeat that
   proves the draft is still open, so we always bump `updated`. A changed
   draftId means a new (back-to-back mock) draft: drop the old picks so draft
   two doesn't open showing draft one. */
async function addPicks(rows, draftId) {
  let s = await getStore();
  if (!s) s = emptyStore(draftId);
  if (draftId && s.draftId && draftId !== s.draftId) s = emptyStore(draftId);
  if (draftId && !s.draftId) s.draftId = draftId;

  let added = 0;
  for (const r of (rows || [])) {
    const rnd = parseInt(r.round, 10), pk = parseInt(r.pick, 10);
    if (!rnd || !pk) continue;
    const key = rnd + '.' + pk;
    if (s.picks[key]) {
      const same = normName(r.name) === normName(s.picks[key].name);
      // 1.01 replayed with a different player means the room restarted.
      if (same || key !== '1.1') continue;
      s.picks = {};
    }
    s.picks[key] = {
      round: rnd, pick: pk,
      name: (r.name || '').trim(),
      pos: r.pos || '',
      nfl: r.nfl || '',
      teamName: (r.team || '').trim()
    };
    added++;
  }
  s.updated = Date.now();
  await setStore(s);
  return { ok: true, total: Object.keys(s.picks).length, added };
}

async function getDraft() {
  const s = await getStore();
  if (!s) return { ok: true, draftId: '', updated: null, teamCount: null, rows: [] };
  return {
    ok: true,
    draftId: s.draftId,
    updated: s.updated,
    teamCount: null,            // no ESPN cookies here; the board infers size
    rows: Object.values(s.picks)
  };
}

async function resetDraft() {
  const s = await getStore();
  await setStore(emptyStore(s ? s.draftId : ''));
  return { ok: true, total: 0 };
}

function badge(text, color) {
  try {
    chrome.action.setBadgeText({ text: text });
    chrome.action.setBadgeBackgroundColor({ color: color });
  } catch (e) { /* action API can be unavailable during startup */ }
}

async function handle(msg) {
  if (!msg || !msg.type) return { ok: false, error: 'no type' };
  if (msg.type === 'ff-picks') {
    const res = await addPicks(msg.picks || [], msg.draftId);
    badge(String(res.total || 0), '#0a7d33');
    return res;
  }
  if (msg.type === 'get-draft') return getDraft();
  if (msg.type === 'reset') { badge('', '#0a7d33'); return resetDraft(); }
  return { ok: false, error: 'unknown type ' + msg.type };
}

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  handle(msg).then(reply).catch(err => reply({ ok: false, error: String(err && err.message || err) }));
  return true;                       // async reply
});

chrome.runtime.onMessageExternal.addListener((msg, sender, reply) => {
  handle(msg).then(reply).catch(err => reply({ ok: false, error: String(err && err.message || err) }));
  return true;
});
