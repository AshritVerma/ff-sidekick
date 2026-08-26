/* FF Sidekick service worker.

   The old design POSTed scraped picks to a local Python helper on
   127.0.0.1:8787. There is no helper anymore: the picks live here, in
   chrome.storage.session, and the hosted board reads them back through
   extension messaging. Everything a stranger needs is the extension plus the
   website -- no install, no server, no cookies.

   Monetization: the FIRST draft a user opens (mock or real) is free. Any
   further distinct draft requires the $9.99 season pass, sold through
   ExtensionPay (Stripe-backed, no backend of our own). Picks for a locked
   draft are never stored, so the board simply shows an upgrade prompt.

   Two message channels reach this worker:
     - chrome.runtime.onMessage         from our own content scripts
     - chrome.runtime.onMessageExternal from the board page (externally_connectable)
   Both are dispatched through handle(). */

importScripts('ExtPay.js');

/* Must match the extension id you register at https://extensionpay.com.
   Create a product there named this slug, priced $9.99 one-time. */
const EXTPAY_ID = 'ff-sidekick';
const extpay = ExtPay(EXTPAY_ID);
extpay.startBackground();

/* When the user pays, cache it and clear the lock badge immediately. */
extpay.onPaid.addListener(async () => {
  await chrome.storage.local.set({ ff_paid_cache: true });
  badge('', '#0a7d33');
});

const KEY = 'ff_draft';
const FREE_KEY = 'ff_free_draft';     // the one draftId that is free (local, persists)
const PAID_KEY = 'ff_paid_cache';     // last known pass state, survives a network blip

function normName(n) {
  n = (n || '').toLowerCase();
  const junk = [' jr.', ' jr', ' sr.', ' sr', ' iii', ' ii', ' iv', "'", '.', '-'];
  for (const j of junk) n = n.split(j).join(j.startsWith(' ') ? ' ' : '');
  return n.split(/\s+/).filter(Boolean).join(' ');
}

function emptyStore(draftId) {
  const now = Date.now();
  return { draftId: draftId || '', started: now, updated: now, picks: {}, locked: false };
}

async function getStore() {
  const o = await chrome.storage.session.get(KEY);
  return o[KEY] || null;
}

async function setStore(s) {
  await chrome.storage.session.set({ [KEY]: s });
}

/* ---- Season pass gate ------------------------------------------------- */

/* Ask ExtensionPay if the user has paid, caching the answer. If ExtensionPay
   is unreachable mid-draft we fall back to the cached value so a paying user
   is never locked out by a hiccup. */
async function isPaid() {
  try {
    const user = await extpay.getUser();
    const paid = !!user.paid;
    await chrome.storage.local.set({ [PAID_KEY]: paid });
    return paid;
  } catch (e) {
    const o = await chrome.storage.local.get(PAID_KEY);
    return !!o[PAID_KEY];
  }
}

/* First distinct draftId is free forever; anything else needs the pass.
   Empty draftId (a room with no leagueId) all share one free bucket. */
async function gateForDraft(draftId) {
  if (await isPaid()) return { allowed: true, paid: true };
  const o = await chrome.storage.local.get(FREE_KEY);
  const free = o[FREE_KEY];
  if (free === undefined || free === null) {
    await chrome.storage.local.set({ [FREE_KEY]: draftId || '' });
    return { allowed: true, paid: false, free: true };
  }
  if ((free || '') === (draftId || '')) return { allowed: true, paid: false, free: true };
  return { allowed: false, paid: false };
}

async function lockStore(draftId) {
  const s = await getStore();
  // Wipe any previous (free) draft's picks so the board can't show them for a
  // draft the user hasn't paid to see.
  if (!s || (s.draftId || '') !== (draftId || '') || !s.locked) {
    const e = emptyStore(draftId);
    e.locked = true;
    await setStore(e);
  }
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
  s.locked = false;

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
  const paid = await cachedPaid();
  if (!s) return { ok: true, draftId: '', updated: null, teamCount: null, rows: [], locked: false, paid };
  return {
    ok: true,
    draftId: s.draftId,
    updated: s.updated,
    teamCount: null,            // no ESPN cookies here; the board infers size
    rows: s.locked ? [] : Object.values(s.picks),
    locked: !!s.locked,
    paid
  };
}

async function cachedPaid() {
  const o = await chrome.storage.local.get(PAID_KEY);
  return !!o[PAID_KEY];
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
    const gate = await gateForDraft(msg.draftId);
    if (!gate.allowed) {
      await lockStore(msg.draftId);
      badge('PRO', '#b45309');
      return { ok: true, locked: true, paid: false, total: 0 };
    }
    const res = await addPicks(msg.picks || [], msg.draftId);
    badge(String(res.total || 0), '#0a7d33');
    return { ...res, locked: false, paid: gate.paid };
  }
  if (msg.type === 'get-draft') return getDraft();
  if (msg.type === 'get-status') {
    const paid = await isPaid();
    const o = await chrome.storage.local.get(FREE_KEY);
    return { ok: true, paid, freeDraft: o[FREE_KEY] ?? null };
  }
  if (msg.type === 'open-pay') { try { extpay.openPaymentPage(); } catch (e) {} return { ok: true }; }
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
