import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createUpdateMonitor } from '../web/update-monitor.mjs';

const settle = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
function harness({ storageError = false, saved = null, response = null } = {}) {
  let time = 0, id = 0, remote = 'v1', calls = 0, failure = false, aborted = false;
  const timers = new Map(), snapshots = [];
  const win = new EventTarget(), doc = new EventTarget();
  win.location = { href: 'https://example.com/ko?x=1#work' };
  win.navigator = { onLine: true };
  win.sessionStorage = {
    getItem: () => { if (storageError) throw Error('blocked'); return saved; },
    setItem: (_, value) => { if (storageError) throw Error('blocked'); saved = value; },
  };
  win.setTimeout = (fn, ms) => { timers.set(++id, { fn, at: time + ms }); return id; };
  win.clearTimeout = key => timers.delete(key);
  win.setInterval = (fn, ms) => { timers.set(++id, { fn, at: time + ms, repeat: ms }); return id; };
  win.clearInterval = win.clearTimeout;
  doc.visibilityState = 'visible';
  const monitor = createUpdateMonitor({
    currentVersion: 'v1', win, doc, now: () => time, onChange: state => snapshots.push(state),
    request: async (url, options) => {
      calls++;
      assert.equal(new URL(url).pathname, '/version.json');
      assert.equal(options.cache, 'no-store');
      options.signal.addEventListener('abort', () => { aborted = true; });
      if (response) return response(options.signal);
      if (failure) throw Error('offline');
      return { ok: true, json: async () => ({ version: remote }) };
    },
  });
  return {
    monitor, win, doc, timers, snapshots,
    setRemote: value => { remote = value; },
    setFailure: () => { failure = true; },
    get calls() { return calls; }, get aborted() { return aborted; },
    get state() { return snapshots.at(-1); },
    async advance(ms) {
      const end = time + ms;
      while (true) {
        const next = [...timers].filter(([,t]) => t.at <= end).sort((a,b)=>a[1].at-b[1].at)[0];
        if (!next) break;
        const [key, timer] = next;
        time = timer.at;
        if (timer.repeat) timer.at += timer.repeat; else timers.delete(key);
        timer.fn(); await settle();
      }
      time = end; await settle();
    },
  };
}
test('checks every minute, resume and network recovery; never navigates', async () => {
  const h = harness(); await settle();
  assert.equal(h.state.available, false);
  h.setRemote('v2'); await h.advance(60000);
  assert.equal(h.state.available, true);
  for (const event of ['focus','pageshow','online']) { h.win.dispatchEvent(new Event(event)); await settle(); }
  h.doc.dispatchEvent(new Event('visibilitychange')); await settle();
  assert.equal(h.calls, 6);
  h.monitor.stop();
});
test('same version returns after 30 minutes, not after one poll', async () => {
  const h = harness(); await settle(); h.setRemote('v2'); await h.advance(60000);
  h.monitor.remindLater();
  assert.equal(h.state.available, false);
  await h.advance(29 * 60000); assert.equal(h.state.available, false);
  await h.advance(60000); assert.equal(h.state.available, true);
  h.monitor.stop();
});
test('a newer deployment bypasses the previous reminder', async () => {
  const h = harness(); await settle(); h.setRemote('v2'); await h.advance(60000);
  h.monitor.remindLater(); h.setRemote('v3'); await h.advance(60000);
  assert.deepEqual(h.state, { version: 'v3', available: true });
  h.monitor.stop();
});
test('storage denial still supports a timed reminder', async () => {
  const h = harness({ storageError: true }); await settle(); h.setRemote('v2'); await h.advance(60000);
  h.monitor.remindLater(); assert.equal(h.state.available, false);
  h.setFailure(); await h.advance(30 * 60000); assert.equal(h.state.available, true);
  h.monitor.stop();
});
test('restores a reminder for this version only', async () => {
  const h = harness({ saved: JSON.stringify({ version: 'v2', until: 120000 }) });
  await settle(); h.setRemote('v2'); await h.advance(60000);
  assert.equal(h.state.available, false);
  await h.advance(60000); assert.equal(h.state.available, true);
  h.monitor.stop();
});
test('hidden/offline pages pause requests and a rollback clears the notice', async () => {
  const h = harness(); await settle(); h.setRemote('v2');
  h.doc.visibilityState = 'hidden'; await h.advance(60000); assert.equal(h.calls,1);
  h.doc.visibilityState = 'visible'; h.win.navigator.onLine = false;
  await h.advance(60000); assert.equal(h.calls,1);
  h.win.navigator.onLine = true; h.win.dispatchEvent(new Event('online')); await settle();
  assert.equal(h.state.available,true);
  h.setRemote('v1'); await h.advance(60000); assert.equal(h.state.available,false);
  h.monitor.stop();
});
test('aborts hung requests and removes timers/listeners on stop', async () => {
  const h = harness({ response: signal => new Promise((_,reject) => signal.addEventListener('abort',()=>reject(Error('aborted')))) });
  await h.advance(10000); assert.equal(h.aborted,true);
  h.monitor.stop(); assert.equal(h.timers.size,0);
  const before = h.calls;
  h.win.dispatchEvent(new Event('focus')); h.doc.dispatchEvent(new Event('visibilitychange'));
  await settle(); assert.equal(h.calls,before);
});

