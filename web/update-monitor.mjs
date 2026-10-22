// Keep this dependency-free monitor aligned across the three sites.
const CHECK_INTERVAL = 60_000;
const REMIND_AFTER = 30 * 60_000;
const STORAGE_KEY = 'site-update-reminder-v1';

export function createUpdateMonitor({
  currentVersion,
  versionUrl = '/version.json',
  pollInterval = CHECK_INTERVAL,
  onChange,
  win = window,
  doc = document,
  request = (...args) => fetch(...args),
  now = () => Date.now(),
}) {
  let latest = null;
  let stopped = false;
  let activeRequest = null;
  let reminderTimer = null;
  let reminder = null;
  try {
    const saved = JSON.parse(win.sessionStorage.getItem(STORAGE_KEY) || 'null');
    if (typeof saved?.version === 'string' && Number.isFinite(saved.until) &&
        saved.until > now() && saved.until <= now() + REMIND_AFTER) reminder = saved;
  } catch { /* Storage may be unavailable; the in-memory reminder still works. */ }

  const publish = () => {
    if (stopped) return;
    win.clearTimeout(reminderTimer);
    const waiting = reminder?.version === latest && reminder.until > now();
    onChange({ version: latest, available: Boolean(latest && !waiting) });
    if (waiting) reminderTimer = win.setTimeout(publish, reminder.until - now());
  };

  const check = async () => {
    publish(); // An expired reminder reappears even if the next request fails.
    if (stopped || activeRequest || doc.visibilityState === 'hidden' || win.navigator?.onLine === false) return;
    const controller = new AbortController();
    activeRequest = controller;
    const timeout = win.setTimeout(() => controller.abort(), 10_000);
    try {
      const url = new URL(versionUrl, win.location.href);
      url.searchParams.set('t', String(now()));
      const response = await request(url.toString(), {
        cache: 'no-store', headers: { Accept: 'application/json' }, signal: controller.signal,
      });
      if (!response.ok) return;
      const payload = await response.json();
      if (!stopped && typeof payload?.version === 'string' && payload.version.trim()) {
        latest = payload.version === currentVersion ? null : payload.version;
        publish();
      }
    } catch { /* Offline or incomplete deployment: retain the current page and retry. */ }
    finally {
      win.clearTimeout(timeout);
      if (activeRequest === controller) activeRequest = null;
    }
  };

  const remindLater = () => {
    if (!latest || stopped) return;
    reminder = { version: latest, until: now() + REMIND_AFTER };
    try { win.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(reminder)); } catch { /* Memory fallback. */ }
    publish();
  };

  const interval = win.setInterval(check, pollInterval);
  doc.addEventListener('visibilitychange', check);
  for (const event of ['focus', 'pageshow', 'online']) win.addEventListener(event, check);
  void check();
  return {
    remindLater,
    stop() {
      stopped = true;
      activeRequest?.abort();
      win.clearInterval(interval);
      win.clearTimeout(reminderTimer);
      doc.removeEventListener('visibilitychange', check);
      for (const event of ['focus', 'pageshow', 'online']) win.removeEventListener(event, check);
    },
  };
}

