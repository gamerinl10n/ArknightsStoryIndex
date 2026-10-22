const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const html = execFileSync('python', ['-c', "from app import create_app; print(create_app(readonly=True).test_client().get('/').text)"], {encoding:'utf8'});
const uiCopy = execFileSync('python', ['-c', "from app import create_app; print(create_app(readonly=True).test_client().get('/i18n.js').text)"], {encoding:'utf8'});
const source = name => fs.readFileSync('web/' + name, 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const exampleItem = {story:'ko_KR:test.txt',speaker:'Mon3tr',text:'시험 대상의 시험 대사',path:'test.txt',branch:'predicate:test',ordinal:1,revision:'test-sha',source:'test/source',lang:'ko_KR',context:[{speaker:'Mon3tr',text:'시험 문맥',ordinal:1,branch:'main'}],parallel:[]};
async function setup(options = {}) {
  const dom = new JSDOM(html, {runScripts:'outside-only',url:'https://asi.test/'+(options.query||'')});
  const w = dom.window, calls = [];
  if (options.theme) w.localStorage.setItem('asi-theme-v1',options.theme);
  if (options.noStorage) Object.defineProperty(w,'localStorage',{get(){throw Error('disabled');}});
  w.fetch = async (url, args) => {
    calls.push(String(url));
    let data;
    if (String(url).startsWith('/api/status')) data={dialogue_lines:725401};
    else if(String(url).startsWith('/api/suggestions')) {
      if(options.badSuggestions) throw Error('offline');
      data=[{value:'켈시',label:'10개 대사',count:10,character_id:'char_003_kalts',portrait:'/portraits/fixture.webp'},{value:'M3',label:'Mon3tr · 5개 대사',count:5}];
    } else data=options.search ? await options.search(url,args) : {total:1,items:[exampleItem]};
    return {ok:true,json:async()=>data};
  };
  w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');this.querySelector('button')?.focus();};
  w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');this.dispatchEvent(new w.Event('close'));};
  w.eval(uiCopy); w.eval(source('theme.js'));
  const modules=new Map();
  async function moduleFor(name) {
    if(modules.has(name))return modules.get(name);
    const mod=new vm.SourceTextModule(source(name),{context:dom.getInternalVMContext(),identifier:name});modules.set(name,mod);
    await mod.link((specifier,parent)=>moduleFor(path.posix.normalize(path.posix.join(path.posix.dirname(parent.identifier),specifier))));
    return mod;
  }
  await (await moduleFor('chrome.js')).evaluate();
  await (await moduleFor('app.js')).evaluate();
  return {dom,w,calls,loadModule:moduleFor,$:id=>w.document.getElementById(id)};
}
function enter(x,speaker='M3',target='켈시') {x.$('speaker').value=speaker;x.$('target').value=target;x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));}
test('attached completion supports keyboard selection, search and context', async()=>{
 const x=await setup();try {
  await tick();await tick();x.$('speaker').focus();x.$('speaker').value='켈시';x.$('speaker').dispatchEvent(new x.w.Event('input'));
  assert.equal(x.$('speaker-options').hidden,false);assert.equal(x.$('speaker').getAttribute('aria-expanded'),'true');
  x.$('speaker').dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'ArrowDown',cancelable:true}));
  assert(x.$('speaker').getAttribute('aria-activedescendant'));
  x.$('speaker').dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'Enter',cancelable:true}));
  assert.equal(x.$('speaker').value,'켈시');assert.equal(x.$('speaker-options').hidden,true);
  enter(x);await tick();await tick();assert.match(x.w.location.search,/speaker=M3/);
  assert.equal(x.$('results').querySelectorAll('article').length,1);assert.equal(x.$('results').querySelector('.current-line'),null);
  assert.equal(x.$('share-search'),null);assert.equal(x.w.localStorage.length,0);
 }finally{x.dom.window.close();}
});
test('shared URLs restore corpus and search values independently',async()=>{
 const x=await setup({query:'?speaker=M3&target=Kal%27tsit&lang=en_US&ui=ko&q=test&spoilers=1'});try {
  await tick();await tick();assert.equal(x.$('lang').value,'en_US');assert.equal(x.$('target').value,"Kal'tsit");assert.equal(x.$('query').value,'test');assert.equal(x.$('spoilers').checked,true);
  assert(x.calls.some(url=>url.startsWith('/api/search?')&&url.includes('lang=en_US')));
 }finally{x.dom.window.close();}
});
test('theme uses the same moon/sun control, persists and restores',async()=>{
  const x=await setup({theme:'dark'});try {
    assert.equal(x.w.document.documentElement.dataset.theme,'dark');
    assert.equal(x.$('themeButton').getAttribute('aria-pressed'),'true');
    assert.equal(x.$('themeButton').querySelectorAll('svg.theme-icon').length,2);
    x.$('themeButton').click();
    assert.equal(x.w.document.documentElement.dataset.theme,undefined);
    assert.equal(x.w.localStorage.getItem('asi-theme-v1'),'light');
    assert.equal(x.$('themeButton').getAttribute('aria-label'),'다크 모드');
    x.w.dispatchEvent(new x.w.StorageEvent('storage',{key:'asi-theme-v1',newValue:'dark'}));
    assert.equal(x.w.document.documentElement.dataset.theme,'dark');
  } finally{x.dom.window.close();}
});
test('storage disabled and suggestion failure still allow typing and searching',async()=>{
  const x=await setup({noStorage:true,badSuggestions:true});try {
    await tick();x.$('themeButton').click();
    assert.equal(x.w.document.documentElement.dataset.theme,'dark');
    assert.equal(x.$('speaker-options').children.length,0);
    x.$('speaker').value='M3';x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));
    await tick();await tick();assert.equal(x.$('results').querySelectorAll('article').length,1);
  } finally{x.dom.window.close();}
});
test('empty search explains how to broaden results',async()=>{
  const x=await setup({search:async()=>({total:0,items:[]})});try {
    enter(x,'켈시','');await tick();await tick();
    assert.equal(x.$('empty-state').hidden,false);
    assert.match(x.$('empty-state').textContent,/조건에 맞는 대사/);
    assert.equal(x.$('more').hidden,true);
    assert.equal(x.$('results').getAttribute('aria-busy'),'false');
  } finally{x.dom.window.close();}
});
test('late responses cannot replace a newer search',async()=>{
  const resolvers=[];const x=await setup({search:()=>new Promise(resolve=>resolvers.push(resolve))});try {
    enter(x);enter(x,'켈시','');
    resolvers[1]({total:0,items:[]});await tick();await tick();
    resolvers[0]({total:1,items:[exampleItem]});await tick();await tick();
    assert.match(x.$('results-title').textContent,/켈시의 전체/);
    assert.equal(x.$('results').querySelectorAll('article').length,0);
  } finally{x.dom.window.close();}
});

test('expanded context loads a bounded window for the selected source',async()=>{
 const x=await setup();try{enter(x);await tick();await tick();const panel=x.$('results').querySelector('details');panel.open=true;panel.dispatchEvent(new x.w.Event('toggle'));await tick();await tick();const button=panel.querySelector('button:not(.info-button)');button.click();await tick();await tick();assert(x.calls.some(url=>url.startsWith('/api/context?')&&url.includes('radius=18')&&url.includes('story=ko_KR')));assert.equal(button.disabled,false);}finally{x.dom.window.close();}
});

test('home and results are separate views; return and browser history preserve the draft',async()=>{
 const x=await setup();x.w.scrollTo=()=>{};try {
  assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results-panel').hidden,true);
  enter(x);await tick();await tick();assert.equal(x.w.location.pathname,'/search');assert.equal(x.$('results-panel').hidden,false);
  const requests=x.calls.filter(url=>url.startsWith('/api/search?')).length;
  x.$('back-search').click();assert.equal(x.w.location.pathname,'/');assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('speaker').value,'M3');assert.equal(x.$('target').value,'켈시');
  const pop=new Promise(resolve=>x.w.addEventListener('popstate',resolve,{once:true}));x.w.history.back();await pop;await tick();
  assert.equal(x.w.location.pathname,'/search');assert.equal(x.$('results-panel').hidden,false);
  assert.equal(x.calls.filter(url=>url.startsWith('/api/search?')).length,requests);
 }finally{x.dom.window.close();}
});
test('result links reload directly; home draft links do not start a search',async()=>{
 const a=await setup({query:'search?speaker=M3&target=켈시&lang=ja_JP'}),b=await setup({query:'?speaker=M3&target=켈시&view=home'});
 try{await tick();await tick();assert.equal(a.$('search-experience').dataset.view,'results');assert.equal(a.$('lang').value,'ja_JP');assert.equal(b.$('search-experience').dataset.view,'home');assert.equal(b.$('speaker').value,'M3');assert(!b.calls.some(url=>url.startsWith('/api/search?')));}finally{a.dom.window.close();b.dom.window.close();}
});
test('returning during a pending request prevents a late result from reopening the page',async()=>{
 let resolve;const x=await setup({search:()=>new Promise(r=>resolve=r)});x.w.scrollTo=()=>{};
 try{enter(x);assert.equal(x.$('search-loading').hidden,false);x.$('back-search').click();resolve({total:1,items:[exampleItem]});await tick();await tick();assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results-panel').hidden,true);assert.equal(x.$('search-loading').hidden,true);assert.equal(x.$('submit-search').disabled,false);assert.equal(x.$('results').children.length,0);}finally{x.dom.window.close();}
});
test('reduced motion avoids native page transitions',async()=>{
 const x=await setup();let transitions=0;x.w.matchMedia=()=>({matches:true});x.w.document.startViewTransition=()=>{transitions++;throw Error('not expected');};
 try{enter(x);await tick();await tick();assert.equal(transitions,0);assert.equal(x.$('search-experience').dataset.view,'results');}finally{x.dom.window.close();}
});

test('a delayed view transition cannot undo a newer navigation',async()=>{
 const x=await setup();x.w.scrollTo=()=>{};const frames=[];
 x.w.document.startViewTransition=apply=>{frames.push(apply);return {finished:Promise.resolve(),skipTransition(){}};};
 try{enter(x);x.$('back-search').click();frames.forEach(apply=>apply());await tick();await tick();assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results-panel').hidden,true);}finally{x.dom.window.close();}
});

test('guide opens in place, closes and returns focus without clearing a draft',async()=>{
 const x=await setup();try{
  x.$('speaker').value='M3';const url=x.w.location.href;x.$('help-button').click();
  assert.equal(x.$('help-dialog').open,true);assert.equal(x.w.location.href,url);
  assert(x.w.document.documentElement.classList.contains('modal-open'));
  x.$('help-dialog').querySelector('[data-close-dialog]').click();
  assert.equal(x.$('help-dialog').open,false);assert.equal(x.w.document.activeElement,x.$('help-button'));assert.equal(x.$('speaker').value,'M3');
 }finally{x.dom.window.close();}
});
test('result and context metadata are available only through detail controls',async()=>{
 const x=await setup();try{
  enter(x);await tick();await tick();const card=x.$('results').querySelector('article');
  assert.equal(card.querySelector('.meta'),null);assert.equal(card.querySelector('.branch-note'),null);assert(!card.textContent.includes('predicate:test'));
  card.querySelector('.info-button').click();assert.equal(x.$('info-dialog').open,true);assert.match(x.$('info-content').textContent,/predicate:test/);assert.match(x.$('info-content').textContent,/test.txt/);
  x.$('info-dialog').close();const panel=card.querySelector('details');panel.open=true;panel.dispatchEvent(new x.w.Event('toggle'));await tick();await tick();card.querySelector('.context-line .info-button').click();assert.match(x.$('info-content').textContent,/기본 분기/);
 }finally{x.dom.window.close();}
});

test('language links preserve UI/corpus independence, draft and selected story',async()=>{
 const x=await setup({query:'?speaker=M3&lang=ja_JP&story=test.txt&view=home'});try{await tick();const link=x.w.document.querySelector('[data-ui="en"]');link.dispatchEvent(new x.w.Event('pointerdown'));const url=new URL(link.href);assert.equal(url.searchParams.get('ui'),'en');assert.equal(url.searchParams.get('lang'),'ja_JP');assert.equal(url.searchParams.get('speaker'),'M3');assert.equal(url.searchParams.get('story'),'test.txt');assert.equal(url.searchParams.get('view'),'home');}finally{x.dom.window.close();}
});
test('expression highlights preserve raw text and never execute markup',async()=>{
 const text='<img src=x onerror=alert(1)> 시험 시험';const x=await setup({search:async()=>({total:1,items:[{...exampleItem,text}]})});
 try{x.$('query').value='시험';enter(x);await tick();await tick();const quote=x.$('results').querySelector('.quote');assert.equal(quote.textContent,text);assert.equal(quote.querySelectorAll('mark').length,2);assert.equal(quote.querySelector('img'),null);}finally{x.dom.window.close();}
});

test('light results defer context DOM and fetch; context and parallel share one request',async()=>{
 const item={...exampleItem};delete item.context;delete item.parallel;
 const x=await setup({search:async url=>String(url).startsWith('/api/context?')?{items:exampleItem.context,parallel:[{lang:'en_US',speaker:'Mon3tr',text:'Fixture'}],has_more:true}:{total:1,items:[item]}});
 try{enter(x);await tick();await tick();assert(x.calls.some(url=>url.includes('details=0')));assert.equal(x.$('results').querySelector('.context-line'),null);assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,0);
 const panels=x.$('results').querySelectorAll('details');panels[0].open=true;panels[0].dispatchEvent(new x.w.Event('toggle'));await tick();await tick();assert(x.$('results').querySelector('.current-line'));
 panels[1].open=true;panels[1].dispatchEvent(new x.w.Event('toggle'));await tick();await tick();assert.match(panels[1].textContent,/Fixture/);assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,1);
 const count=x.calls.filter(url=>url.startsWith('/api/search?')).length;enter(x);await tick();await tick();assert.equal(x.calls.filter(url=>url.startsWith('/api/search?')).length,count);
 }finally{x.dom.window.close();}
});
test('API cache deduplicates pending requests, expires and evicts without caching failures',async()=>{
 const x=await setup();try{
 const {createClient}=(await x.loadModule('ui/api.mjs')).namespace;let clock=0,requests=0,fail=false;
 x.w.fetch=async()=>{requests++;if(fail)throw Error('offline');return {ok:true,json:async()=>({n:requests})};};
 const client=createClient({limit:2,ttl:10,now:()=>clock});
 await Promise.all([client('/a'),client('/a')]);assert.equal(requests,1);await client('/b');await client('/a');await client('/c');await client('/b');assert.equal(requests,4);
 clock=11;await client('/b');assert.equal(requests,5);
 fail=true;await assert.rejects(client('/error'));fail=false;await client('/error');assert.equal(requests,7);
 }finally{x.dom.window.close();}
});
test('aborted request responses never enter the shared API cache',async()=>{
 const x=await setup();try{
 const {createClient}=(await x.loadModule('ui/api.mjs')).namespace;const client=createClient();let resolve,calls=0;
 x.w.fetch=async()=>{calls++;await new Promise(r=>resolve=r);return {ok:true,json:async()=>({ok:true})};};
 const controller=new x.w.AbortController(),first=client('/cancel',{signal:controller.signal});controller.abort();resolve();await assert.rejects(first,{name:'AbortError'});
 const second=client('/cancel');resolve();await second;assert.equal(calls,2);
 }finally{x.dom.window.close();}
});

test('word-only search, shared URL and character selection preserve avatars and fallback', async()=>{
 const x=await setup({query:'search?q=%EC%BC%88%EC%8B%9C&lang=ko_KR'});try {
  await tick();await tick();assert.equal(x.$('speaker').value,'');
  assert.equal(x.$('query').value,'켈시');assert.equal(x.$('search-experience').dataset.view,'results');
  assert(x.calls.some(url=>url.startsWith('/api/search?')&&url.includes('q=')));
  assert.match(x.$('results-title').textContent,/켈시/);
  x.$('back-search').click();x.$('speaker').focus();x.$('speaker').value='켈시';x.$('speaker').dispatchEvent(new x.w.Event('input'));
  x.$('speaker-options').querySelector('[role=option]').click();
  assert.equal(x.$('speaker').closest('.field').querySelector('img').getAttribute('src'),'/portraits/fixture.webp');
  x.$('swap').click();assert(x.$('target').closest('.field').querySelector('img'));
  x.$('target').value='unknown';x.$('target').dispatchEvent(new x.w.Event('input'));
  assert.equal(x.$('target').closest('.field').querySelector('img'),null);
  const image=x.$('speaker-options').querySelector('img');image.dispatchEvent(new x.w.Event('error'));
  assert.equal(image.isConnected,false);
  assert(x.$('speaker-options').querySelector('svg'));
 }finally{x.dom.window.close();}
});

test('results omit copy actions and story picker',async()=>{
 const x=await setup();try{enter(x);await tick();await tick();assert.equal(x.$('share-search'),null);assert.equal(x.$('story-filter'),null);assert.equal(x.$('results').querySelector('.result-actions'),null);}finally{x.dom.window.close();}
});
