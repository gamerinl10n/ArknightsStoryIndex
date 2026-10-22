const $ = id => document.getElementById(id);
const t = (key, values={}) => Object.entries(values).reduce((s,[k,v])=>s.replaceAll('{'+k+'}',String(v)), window.ASI.strings[key] || key);
const el = (tag, text, cls) => { const node=document.createElement(tag); node.textContent=text; if(cls) node.className=cls; return node; };
let offset=0, last=null, suggestions=[], suggestionVersion=0, requestVersion=0, controller, renderedKey=null, viewTransition, viewVersion=0;
const experience=$('search-experience');
const reducedMotion=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
function setView(view, animate=true) {
  const token=++viewVersion,changed=experience.dataset.view!==view;
  const apply=()=>{if(token!==viewVersion)return;experience.dataset.view=view;document.title=t(view==='home'?'search':'results')+' · Arknights Story Index';$('results-panel').hidden=view==='home';$('back-search').parentElement.hidden=view==='home';if(changed && view==='results')$('results-title').focus({preventScroll:true});};
  if(!changed || !animate || reducedMotion()){viewTransition?.skipTransition();apply();return;}
  if(document.startViewTransition){try{viewTransition?.skipTransition();viewTransition=document.startViewTransition(apply);viewTransition.finished.catch(()=>{});return;}catch{ /* Use the CSS entry transition on unsupported surfaces. */ }}
  apply();experience.classList.remove('view-enter');void experience.offsetWidth;experience.classList.add('view-enter');
}
experience.addEventListener('animationend',()=>experience.classList.remove('view-enter'));
function readForm(){return {speaker:$('speaker').value.trim(),target:$('target').value.trim(),q:$('query').value.trim(),lang:$('lang').value,spoilers:$('spoilers').checked?'1':'0'};}
function stopSearch(){++requestVersion;controller?.abort();$('submit-search').disabled=false;$('submit-search').textContent=t('search');$('results').setAttribute('aria-busy','false');$('search-loading').hidden=true;}
function goHome(event){event?.preventDefault();const draft=readForm();history.pushState({draft},'','/?'+new URLSearchParams({ui:window.ASI.ui}));stopSearch();completions.forEach(c=>c.close());setView('home');$('speaker').focus({preventScroll:true});window.scrollTo?.({top:0,behavior:reducedMotion()?'instant':'smooth'});}
$('back-search').onclick=goHome;
document.querySelector('.brand').addEventListener('click',event=>{if(event.button===0&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey)goHome(event);});
async function api(url, options) { const response=await fetch(url,options); const data=await response.json(); if(!response.ok) throw Error(t('failed')); return data; }
function completion(id) {
  const input=$(id), list=$(id+'-options'); let active=-1, rows=[];
  const close=()=>{list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;};
  function draw() {
    const query=input.value.trim().toLocaleLowerCase();
    rows=suggestions.filter(row=>!query || (row.value+' '+row.label).toLocaleLowerCase().includes(query)).sort((a,b)=>(b.value.toLocaleLowerCase()===query)-(a.value.toLocaleLowerCase()===query) || b.count-a.count).slice(0,12);
    active=-1;list.replaceChildren();input.removeAttribute('aria-activedescendant');
    rows.forEach((row,index)=>{
      const option=el('div','', 'suggestion'); option.id=id+'-option-'+index; option.setAttribute('role','option');option.setAttribute('aria-selected','false');
      option.append(el('span',row.value)); if(row.label!==row.value) option.append(el('small',row.label));
      option.addEventListener('pointerdown',event=>event.preventDefault());
      option.addEventListener('click',()=>{input.value=row.value;input.setCustomValidity('');close();input.focus();});list.append(option);
    });
    list.hidden=!rows.length;input.setAttribute('aria-expanded',String(rows.length>0));
  }
  input.addEventListener('input',()=>{input.setCustomValidity('');draw();});input.addEventListener('focus',draw);
  input.addEventListener('blur',close);
  input.addEventListener('keydown',event=>{
    if(event.key==='Escape') {event.preventDefault();close();return;}
    if(event.key==='ArrowDown'||event.key==='ArrowUp') {
      event.preventDefault();if(list.hidden)draw();if(!rows.length)return;
      active=(active+(event.key==='ArrowDown'?1:-1)+rows.length)%rows.length;
      [...list.children].forEach((node,i)=>node.setAttribute('aria-selected',String(i===active)));
      input.setAttribute('aria-activedescendant',list.children[active].id);list.children[active].scrollIntoView?.({block:'nearest'});
    } else if(event.key==='Enter' && !list.hidden && active>=0) {event.preventDefault();input.value=rows[active].value;close();}
  });
  return {refresh:()=>{if(document.activeElement===input)draw();},close};
}
const completions=[completion('speaker'),completion('target')];
$('swap').onclick=()=>{const a=$('speaker').value;$('speaker').value=$('target').value;$('target').value=a;completions.forEach(c=>c.close());};
async function loadSpeakers() {
  const version=++suggestionVersion;suggestions=[];completions.forEach(c=>c.close());
  try {const params=new URLSearchParams({lang:$('lang').value,spoilers:$('spoilers').checked?'1':'0'});const rows=await api('/api/suggestions?'+params);if(version!==suggestionVersion)return;suggestions=rows;completions.forEach(c=>c.refresh());}
  catch {if(version===suggestionVersion)suggestions=[];}
}
$('lang').addEventListener('change',loadSpeakers);$('spoilers').addEventListener('change',loadSpeakers);
function contextRows(container,rows,ordinal) {
  container.replaceChildren();rows.forEach(row=>{const p=el('p',`${row.speaker||t('unnamed')}: ${row.text}`,row.ordinal===ordinal?'current-line':'');if(row.branch!=='main')p.append(el('small',`\n${t('branch')}: ${row.branch}`,'branch-note'));container.append(p);});
}
function render(item) {
  const card=el('article','','result-card');card.style.setProperty('--enter-delay',Math.min($('results').children.length,5)*35+'ms');card.append(el('h2',item.speaker),el('p',item.text,'quote'),el('p',`${item.path} · ${t('line',{n:item.ordinal+1})} · ${item.revision.slice(0,12)}`,'meta'));
  const context=el('details','');context.append(el('summary',t('context')));const lines=el('div','');contextRows(lines,item.context,item.ordinal);context.append(lines);
  const expand=el('button',t('context_more'));expand.type='button';let radius=3;
  expand.onclick=async()=>{expand.disabled=true;try {const next=Math.min(radius+15,100);const data=await api('/api/context?'+new URLSearchParams({story:item.story,ordinal:item.ordinal,radius:next}));contextRows(lines,data.items,item.ordinal);radius=next;expand.hidden=!data.has_more||radius>=100;}catch{expand.textContent=t('retry');}finally{expand.disabled=false;}};
  context.append(expand);card.append(context);
  if(item.parallel.length) {const parallel=el('details','');parallel.append(el('summary',t('parallel')));item.parallel.forEach(row=>parallel.append(el('p',`[${row.lang}] ${row.speaker}: ${row.text}`)));card.append(parallel);}
  const actions=el('div','','result-actions'),copy=el('button',t('copy'));copy.type='button';copy.onclick=async()=>{try{await navigator.clipboard.writeText(`${item.speaker}: ${item.text}\n${item.source}@${item.revision} / ${item.lang}/${item.path}:${item.ordinal+1}`);copy.textContent=t('copied');}catch{copy.textContent=t('copy_failed');}};actions.append(copy);card.append(actions);$('results').append(card);
}
function empty(title,description) {$('empty-state').hidden=false;$('empty-state').querySelector('h3').textContent=title;$('empty-state').querySelector('p').textContent=description;}
async function run(append=false) {
  const version=++requestVersion,search={...last};controller?.abort();controller=new AbortController();
  $('more').disabled=true;$('submit-search').disabled=true;$('submit-search').textContent=t('loading');$('results').setAttribute('aria-busy','true');
  if(!append){$('results').replaceChildren();$('more').hidden=true;$('result-count').textContent='';$('empty-state').hidden=true;}
  $('notice').textContent=t('loading');$('search-loading').hidden=false;$('search-loading').dataset.append=String(append);renderedKey=null;
  try {const params=new URLSearchParams(search);params.set('offset',offset);const data=await api('/api/search?'+params,{signal:controller.signal});if(version!==requestVersion)return;
    data.items.forEach(render);offset+=data.items.length;renderedKey=JSON.stringify(search);$('more').hidden=offset>=data.total;
    $('results-title').textContent=search.target?t('search_pair',{a:search.speaker,b:search.target}):t('search_solo',{a:search.speaker});$('result-count').textContent=t('count',{n:data.total.toLocaleString()});$('notice').textContent='';$('share-search').hidden=false;
    if(!data.total)empty(t('no_results'),t('broaden'));
  }catch(error){if(version!==requestVersion||error.name==='AbortError')return;$('notice').textContent=t('failed');if(!append)empty(t('failed'),t('retry'));}
  finally{if(version===requestVersion){$('more').disabled=false;$('submit-search').disabled=false;$('submit-search').textContent=t('search');$('results').setAttribute('aria-busy','false');$('search-loading').hidden=true;}}
}
function submit(updateUrl=true) {
  if(!$('speaker').value.trim()){$('speaker').setCustomValidity(t('search_error'));$('speaker').reportValidity();return;}
  const draft=readForm();
  if(updateUrl){history.replaceState({...history.state,draft},'',location.href);const params=new URLSearchParams(draft);params.set('ui',window.ASI.ui);history.pushState({draft},'','/search?'+params);}
  offset=0;last=draft;completions.forEach(c=>c.close());setView('results');run();
}
function restore(initial=false) {
  const params=new URLSearchParams(location.search),draft=history.state?.draft||{};
  for(const key of ['speaker','target'])$(key).value=(params.get(key)??draft[key]??'').slice(0,300);
  $('query').value=(params.get('q')??draft.q??'').slice(0,300);
  const lang=params.get('lang')||draft.lang;
  $('lang').value=[...$('lang').options].some(o=>o.value===lang)?lang:({ko:'ko_KR',zh:'zh_CN',ja:'ja_JP',en:'en_US'})[window.ASI.ui];
  $('spoilers').checked=(params.get('spoilers')??draft.spoilers)==='1';loadSpeakers();
  const showResults=$('speaker').value && params.get('view')!=='home' && (location.pathname==='/search'||params.has('speaker'));
  if(showResults){const search=readForm();setView('results',!initial);if(renderedKey!==JSON.stringify(search)){offset=0;last=search;run();}}
  else{stopSearch();setView('home',!initial);}
}
$('search').onsubmit=event=>{event.preventDefault();submit();};$('more').onclick=()=>run(true);
$('share-search').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);$('share-search').textContent=t('shared');}catch{$('share-search').textContent=t('copy_failed');}};
window.addEventListener('popstate',()=>restore(false));restore(true);
