/* Popup UI: shows season-pass status and opens the Stripe checkout.
   Must use the same ExtensionPay id as background.js. */
const EXTPAY_ID = 'ff-sidekick';
const extpay = ExtPay(EXTPAY_ID);

const dot = document.getElementById('dot');
const statusText = document.getElementById('statusText');
const sub = document.getElementById('sub');
const buy = document.getElementById('buy');
const anchor = document.getElementById('anchor');
const manage = document.getElementById('manage');

function ask(type) {
  return new Promise(resolve => {
    chrome.runtime.sendMessage({ type }, res => resolve(chrome.runtime.lastError ? null : res));
  });
}

function show(el, on) { el.classList.toggle('hide', !on); }

function paint(paid, freeUsed) {
  if (paid) {
    dot.className = 'dot ok';
    statusText.textContent = 'Season pass active';
    sub.textContent = 'Unlimited mock and real drafts for the 2026 season. Thanks for the support.';
    show(buy, false); show(anchor, false); show(manage, true);
    return;
  }
  if (!freeUsed) {
    dot.className = 'dot free';
    statusText.textContent = 'First draft free';
    sub.textContent = 'Your first draft (mock or real) syncs free. Grab the season pass any time to unlock the rest.';
  } else {
    dot.className = 'dot lock';
    statusText.textContent = 'Free draft used';
    sub.textContent = 'You have used your free draft. Unlock the season pass to sync unlimited drafts.';
  }
  show(buy, true); show(anchor, true); show(manage, true);
}

async function refresh() {
  const st = await ask('get-status');
  const paid = !!(st && st.paid);
  const freeUsed = !!(st && st.freeDraft !== null && st.freeDraft !== undefined);
  paint(paid, freeUsed);
}

buy.addEventListener('click', () => {
  try { extpay.openPaymentPage(); } catch (e) { ask('open-pay'); }
});
manage.addEventListener('click', e => {
  e.preventDefault();
  try { extpay.openPaymentPage(); } catch (e2) { ask('open-pay'); }
});

extpay.onPaid.addListener(refresh);
refresh();
