/* Runs automatically in any ESPN draft room. Reads the pick feed and hands new
   picks to the service worker, which stores them for the FF Sidekick board. */
(function () {
  var EVERY = 1500;                  // how often to read the room
  var BEAT = 5000;                   // record activity at least this often
  var seen = Object.create(null), sent = 0, lastPing = 0, dead = 0;
  // The league id identifies the draft. Back-to-back mocks each get their own,
  // so sending it lets the worker drop the previous draft's picks by itself.
  var DRAFT_ID = new URLSearchParams(location.search).get('leagueId') || '';

  var box = document.createElement('div');
  box.style.cssText = 'position:fixed;z-index:2147483647;right:12px;bottom:12px;' +
    'background:#17181a;color:#fff;font:600 12px/1.35 -apple-system,Segoe UI,sans-serif;' +
    'padding:8px 11px;border-radius:7px;box-shadow:0 4px 14px rgba(0,0,0,.35);' +
    'pointer-events:none;opacity:.92';
  function paint(msg, c) {
    box.innerHTML = '<span style="color:' + (c || '#4ade80') + '">●</span> FF Sidekick · ' + msg;
  }
  function mount() { if (!box.isConnected && document.body) document.body.appendChild(box); }

  function parse(li) {
    var t = (li.innerText || '').replace(/ /g, ' ').trim();
    var m = t.match(/^([^\/\n]+?)\s*\/\s*([A-Z]{2,4})\s+([A-Z\/]+(?:\s*,\s*[A-Z\/]+)*)\s*\n\s*R(\d+)\s*,\s*P(\d+)\s*[-–]\s*(.+)$/);
    if (!m) return null;
    return { name: m[1].trim(), nfl: m[2], pos: m[3].split(',')[0].trim(),
             round: +m[4], pick: +m[5], team: m[6].trim() };
  }

  function post(rows) {
    lastPing = Date.now();
    try {
      chrome.runtime.sendMessage({ type: 'ff-picks', picks: rows, draftId: DRAFT_ID }, function (res) {
        if (chrome.runtime.lastError || !res || !res.ok) {
          dead++;
          // let anything we failed to deliver be picked up on the next sweep
          for (var i = 0; i < rows.length; i++) delete seen[rows[i].round + '.' + rows[i].pick];
          paint('extension reloaded — refresh this page', '#facc15');
          return;
        }
        dead = 0;
        if (res.locked) {
          // Free draft already used and no season pass: stop tracking this one.
          // Re-queue so nothing is silently dropped if they upgrade mid-draft.
          for (var j = 0; j < rows.length; j++) delete seen[rows[j].round + '.' + rows[j].pick];
          paint('season pass needed — click the FF Sidekick icon', '#f59e0b');
          return;
        }
        sent += rows.length;
        paint(res.total + ' picks tracked', '#4ade80');
      });
    } catch (e) {
      paint('extension reloaded — refresh this page', '#facc15');
    }
  }

  function scan() {
    mount();
    var rows = document.querySelectorAll('li.pick-message__container');
    if (!rows.length) rows = document.querySelectorAll('[class*="pick-message__container"]');
    var fresh = [];
    for (var i = 0; i < rows.length; i++) {
      var p = parse(rows[i]);
      if (!p) continue;
      var k = p.round + '.' + p.pick;
      if (seen[k]) continue;
      seen[k] = 1;
      fresh.push(p);
    }
    if (fresh.length) post(fresh);
    else if (Date.now() - lastPing > BEAT) post([]);   // heartbeat proves the room is open
  }

  paint('starting…', '#facc15');
  mount();
  setInterval(scan, EVERY);
  scan();
})();
