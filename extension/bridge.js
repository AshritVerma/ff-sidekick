/* Bridges the FF Sidekick board page to the extension.

   A web page can't call chrome.runtime directly (unless it hardcodes the
   published extension id via externally_connectable). This content script runs
   in the board's tab, shares its window, and relays messages both ways with
   window.postMessage. The board asks {type:'get-draft'} / {type:'reset'} and
   gets the same shape the old Python helper returned. */
(function () {
  window.addEventListener('message', function (ev) {
    if (ev.source !== window) return;
    var d = ev.data;
    if (!d || !d.__ffReq) return;
    try {
      chrome.runtime.sendMessage(d.__ffReq, function (res) {
        var payload = chrome.runtime.lastError ? null : res;
        window.postMessage({ __ffRes: true, __id: d.__id, payload: payload }, '*');
      });
    } catch (e) {
      window.postMessage({ __ffRes: true, __id: d.__id, payload: null }, '*');
    }
  });

  // Announce presence so the board can show "live sync ready" instead of the
  // install prompt. __id 0 is reserved for these unsolicited hellos.
  function hello() {
    window.postMessage({ __ffRes: true, __id: 0, payload: { installed: true } }, '*');
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hello);
  } else {
    hello();
  }
  hello();
})();
