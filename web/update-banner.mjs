import {preserveForm} from './ui/form-state.mjs';
import { createUpdateMonitor } from './update-monitor.mjs';

const currentVersion = document.querySelector('meta[name="deployment-version"]')?.content;
if (currentVersion && currentVersion !== 'development') {
  const labels = () => ({ready:window.ASI.strings.update_ready,later:window.ASI.strings.update_later,update:window.ASI.strings.update_now,hint:window.ASI.strings.update_hint});
  const banner = document.createElement('aside');
  banner.className = 'site-update';
  banner.hidden = true;
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  const message = document.createElement('div');
  message.className = 'site-update-message';
  const icon = document.createElement('img');
  icon.className='brand-logo';icon.src=new URL('brand/operator-96.png',import.meta.url).href;icon.width=40;icon.height=40;icon.alt='';
  const text = document.createElement('p');
  message.append(icon, text);
  const actions = document.createElement('div');
  actions.className = 'site-update-actions';
  const later = document.createElement('button');
  later.type = 'button';
  later.className = 'site-update-later';
  const update = document.createElement('button');
  update.type = 'button';
  update.className = 'site-update-now';
  actions.append(later, update);
  banner.append(message, actions);
  document.body.append(banner);
  const refreshCopy = () => {
    const t = labels();
    text.textContent = t.ready;
    later.textContent = t.later;
    later.title = t.hint;
    update.textContent = t.update;
  };
  refreshCopy();
  const languageObserver = new MutationObserver(refreshCopy);
  languageObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

  const monitor = createUpdateMonitor({
    currentVersion,
    onChange: ({ available }) => { banner.hidden = !available; },
  });
  later.addEventListener('click', () => monitor.remindLater());
  update.addEventListener('click', () => {
    const url = preserveForm();
    url.searchParams.set('updated', Date.now().toString());
    window.location.replace(url.toString());
  });
  const url = new URL(window.location.href);
  if (url.searchParams.has('updated')) {
    url.searchParams.delete('updated');
    window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
  }
}

