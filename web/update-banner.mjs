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
  const icon = document.createElement('span');
  icon.className='brand-mark';icon.textContent='ASI';icon.setAttribute('aria-hidden','true');
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
  const spacer = document.createElement('div');
  spacer.setAttribute('aria-hidden', 'true');
  document.body.append(spacer, banner);
  const measure = () => {
    spacer.style.height = banner.hidden ? '0px' :
      'calc(' + (banner.getBoundingClientRect().height + 48) + 'px + env(safe-area-inset-bottom, 0px))';
  };
  const refreshCopy = () => {
    const t = labels();
    text.textContent = t.ready;
    later.textContent = t.later;
    later.title = t.hint;
    update.textContent = t.update;
    measure();
  };
  refreshCopy();
  const languageObserver = new MutationObserver(refreshCopy);
  languageObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  if ('ResizeObserver' in window) new ResizeObserver(measure).observe(banner);
  window.addEventListener('resize', measure);

  const monitor = createUpdateMonitor({
    currentVersion,
    onChange: ({ available }) => { banner.hidden = !available; measure(); },
  });
  later.addEventListener('click', () => monitor.remindLater());
  update.addEventListener('click', () => {
    const url = new URL(window.location.href);
    // Preserve even unsubmitted search fields before loading the new deployment.
    if (document.getElementById('speaker')) {
      url.searchParams.set('view',document.getElementById('search-experience').dataset.view==='home'?'home':'results');
      for (const id of ['speaker','target','lang']) url.searchParams.set(id,document.getElementById(id).value);
      url.searchParams.set('q',document.getElementById('query').value);url.searchParams.set('story',document.getElementById('story-filter')?.value||'');
      url.searchParams.set('spoilers',document.getElementById('spoilers').checked?'1':'0');
    }
    url.searchParams.set('updated', Date.now().toString());
    window.location.replace(url.toString());
  });
  const url = new URL(window.location.href);
  if (url.searchParams.has('updated')) {
    url.searchParams.delete('updated');
    window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
  }
}

