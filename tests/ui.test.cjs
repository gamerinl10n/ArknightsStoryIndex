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
      data=options.suggestions || [{value:'켈시',label:'10개 대사',count:10,character_id:'char_003_kalts',portrait:'/portraits/fixture.webp'},{value:'M3',label:'Mon3tr · 5개 대사',count:5}];
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

test('language links select matching corpus and preserve draft',async()=>{
 const x=await setup({query:'?speaker=M3&lang=ja_JP&story=test.txt&view=home'});try{await tick();const link=x.w.document.querySelector('[data-ui="en"]');link.dispatchEvent(new x.w.Event('pointerdown'));const url=new URL(link.href);assert.equal(url.searchParams.get('ui'),'en');assert.equal(url.searchParams.get('lang'),'en_US');assert.equal(url.searchParams.get('speaker'),'M3');assert.equal(url.searchParams.get('story'),'test.txt');assert.equal(url.searchParams.get('view'),'home');}finally{x.dom.window.close();}
});
test('expression highlights preserve raw text and never execute markup',async()=>{
 const text='<img src=x onerror=alert(1)> 시험 시험';const x=await setup({search:async()=>({total:1,items:[{...exampleItem,text}]})});
 try{x.$('query').value='시험';enter(x);await tick();await tick();const quote=x.$('results').querySelector('.quote');assert.equal(quote.textContent,text);assert.equal(quote.querySelectorAll('mark').length,2);assert.equal(quote.querySelector('img'),null);}finally{x.dom.window.close();}
});

test('light results fetch only context and omit cross-language candidates',async()=>{
 const item={...exampleItem};delete item.context;delete item.parallel;
 const x=await setup({search:async url=>String(url).startsWith('/api/context?')?{items:exampleItem.context,parallel:[{lang:'en_US',speaker:'Mon3tr',text:'Fixture'}],has_more:true}:{total:1,items:[item]}});
 try{enter(x);await tick();await tick();assert(x.calls.some(url=>url.includes('details=0')));assert.equal(x.$('results').querySelector('.context-line'),null);assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,0);
 const panels=x.$('results').querySelectorAll('details');panels[0].open=true;panels[0].dispatchEvent(new x.w.Event('toggle'));await tick();await tick();assert(x.$('results').querySelector('.current-line'));
 assert.equal(panels.length,1);assert(!x.calls.some(url=>url.includes('parallel=')));assert(!x.$('results').textContent.includes('Fixture'));assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,1);
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

test('Korean names find localized English and Japanese suggestions without foreign display rows',async()=>{
 for(const [lang,name] of [['en_US','Amiya'],['ja_JP','アーミヤ']]){
  const x=await setup({query:'?lang='+lang,suggestions:[{value:name,label:name,count:12,lookup:['아미야','Amiya','アーミヤ','阿米娅']}]});
  try{await tick();await tick();x.$('speaker').focus();x.$('speaker').value='아미';x.$('speaker').dispatchEvent(new x.w.Event('input'));
   assert.equal(x.$('speaker-options').children.length,1);assert.equal(x.$('speaker-options').textContent,name);
   x.$('speaker-options').querySelector('[role=option]').click();assert.equal(x.$('speaker').value,name);
   x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));await tick();await tick();assert(x.calls.some(url=>url.startsWith('/api/search?')&&new URL(url,'https://asi.test').searchParams.get('speaker')===name&&url.includes('lang='+lang)));
  }finally{x.dom.window.close();}
 }
});

test('tab title stays the brand through search and return',async()=>{
 const x=await setup();try{assert.equal(x.w.document.title,'Arknights Index');enter(x);await tick();await tick();assert.equal(x.w.document.title,'Arknights Index');x.$('back-search').click();assert.equal(x.w.document.title,'Arknights Index');}finally{x.dom.window.close();}
});

test('search uses native task-order tabbing without positive tabindex or focus traps',async()=>{
 const x=await setup();try{const controls=[...x.$('search').querySelectorAll('input,select,button')].filter(node=>node.tabIndex>=0&&!node.disabled&&!node.closest('[hidden]'));assert.deepEqual(controls.map(node=>node.id),['query','speaker','target','submit-search','reset-search','corpus-button','swap','compare','spoilers']);assert.equal(x.$('search').querySelector('[tabindex]:not([tabindex="-1"])'),null);}finally{x.dom.window.close();}
});

test('styled corpus picker supports selection, Escape and Tab without trapping focus',async()=>{
 const x=await setup();try{await tick();const button=x.$('corpus-button');button.click();assert.equal(x.$('corpus-options').hidden,false);button.dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'ArrowDown',cancelable:true}));button.dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'Enter',cancelable:true}));assert.equal(x.$('lang').value,'zh_CN');assert.equal(x.$('corpus-value').textContent,'中文');assert.equal(x.$('corpus-options').hidden,true);await tick();assert(x.calls.some(url=>url.startsWith('/api/suggestions?')&&url.includes('lang=zh_CN')));
 button.click();button.dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'Escape',cancelable:true}));assert.equal(x.$('corpus-options').hidden,true);assert.equal(x.$('lang').value,'zh_CN');button.click();const tab=new x.w.KeyboardEvent('keydown',{key:'Tab',cancelable:true});button.dispatchEvent(tab);assert.equal(tab.defaultPrevented,false);assert.equal(x.$('corpus-options').hidden,true);
 }finally{x.dom.window.close();}
});
test('nearby matches share lazy context without merging a different branch',async()=>{
 const first={...exampleItem,context:undefined,nearby_turns:2};
 const second={...first,ordinal:3,text:'둘째 일치'};
 const third={...first,ordinal:4,branch:'other',text:'다른 분기'};
 const x=await setup({search:async url=>String(url).startsWith('/api/context?')?{items:[first,second],has_more:false}:{total:3,items:[first,second,third]}});try{
  enter(x);await tick();await tick();
  assert.equal(x.$('results').querySelectorAll('article').length,2);
  assert.equal(x.$('results').querySelectorAll('article')[0].querySelectorAll('.card-heading').length,2);
  assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,0);
  const panel=x.$('results').querySelector('details');panel.open=true;panel.dispatchEvent(new x.w.Event('toggle'));
  await tick();await tick();
  assert.equal(x.calls.filter(url=>url.startsWith('/api/context?')).length,1);
  assert.equal(panel.querySelectorAll('.current-line').length,2);
  assert.match(x.$('result-count').textContent,/3/);
 }finally{x.dom.window.close();}
});

test('brand navigation returns home without focusing a search field or reopening suggestions',async()=>{
 const x=await setup();try{
  await tick();await tick();enter(x);await tick();await tick();
  x.$('speaker').focus();
  const brand=x.w.document.querySelector('.brand');brand.click();
  assert.equal(x.w.location.pathname,'/');
  assert.equal(x.$('search-experience').dataset.view,'home');
  assert.equal(x.w.document.activeElement,brand);
  assert.equal(x.$('speaker-options').hidden,true);
  assert.equal(x.$('target-options').hidden,true);
  assert.equal(x.$('speaker').value,'M3');
  assert.equal(x.$('target').value,'켈시');
 }finally{x.dom.window.close();}
});

test('clear inputs button clears text, portraits and validity while preserving language settings',async()=>{
 const x=await setup();try{await tick();x.$('query').value='test';x.$('speaker').value='켈시';x.$('target').value='M3';x.$('lang').value='en_US';x.$('spoilers').checked=true;x.$('query').setCustomValidity('error');x.$('speaker').focus();x.$('reset-search').click();for(const id of ['query','speaker','target'])assert.equal(x.$(id).value,'');assert.equal(x.$('query').validationMessage,'');assert.equal(x.$('speaker-options').hidden,true);assert.equal(x.$('lang').value,'en_US');assert.equal(x.$('spoilers').checked,true);assert.equal(x.w.history.state.draft.q,'');assert.equal(x.w.history.state.draft.speaker,'');assert.equal(x.calls.filter(url=>url.startsWith('/api/search?')).length,0);}finally{x.dom.window.close();}
});

async function transitionHarness({reduced=false,denied=false,pending=null,counter=null}={}){
 const x=await setup();const dom=new JSDOM('<html lang="ko"><body><nav class="language-switch"><a href="/?ui=ko" data-ui="ko" aria-current="page">KR</a><a href="/?ui=en" data-ui="en">EN</a></nav><div id="languageSplash"></div></body></html>',{url:'https://asi.test/'});
 const timers=new Map(),saved=new Map(),destinations=[];let clock=0,next=0;
 if(pending)saved.set('asi-language-transition',JSON.stringify(pending));if(counter)saved.set('asi-language-splash-variant',String(counter));
 const events=new dom.window.EventTarget();
 const w={location:dom.window.location,matchMedia:()=>({matches:reduced}),get sessionStorage(){if(denied)throw Error('disabled');return {getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v),removeItem:k=>saved.delete(k)};},setTimeout:(fn,delay)=>{timers.set(++next,{fn,at:clock+delay});return next;},clearTimeout:id=>timers.delete(id),addEventListener:(...args)=>events.addEventListener(...args),removeEventListener:(...args)=>events.removeEventListener(...args)};
 const controller=(await x.loadModule('ui/language-splash.mjs')).namespace.createLanguageSplashController({documentRef:dom.window.document});
 const stop=(await x.loadModule('ui/language-transition.mjs')).namespace.setupLanguageTransitions({documentRef:dom.window.document,windowRef:w,splashController:controller,navigate:url=>destinations.push(url)});
 return {dom,saved,destinations,root:dom.window.document.documentElement,splash:dom.window.document.getElementById('languageSplash'),click:(ui='en',opts={})=>{const e=new dom.window.MouseEvent('click',{button:0,cancelable:true,...opts});dom.window.document.querySelector(`[data-ui="${ui}"]`).dispatchEvent(e);return e;},advance:ms=>{const end=clock+ms;for(;;){const entry=[...timers].sort((a,b)=>a[1].at-b[1].at).find(([,t])=>t.at<=end);if(!entry)break;clock=entry[1].at;timers.delete(entry[0]);entry[1].fn();}clock=end;},restore:()=>events.dispatchEvent(new dom.window.PageTransitionEvent('pageshow',{persisted:true})),close:()=>{stop();dom.window.close();x.dom.window.close();}};
}
test('language splash leaves, preserves ordinary link semantics and navigates once',async()=>{
 const h=await transitionHarness();try{assert.equal(h.click().defaultPrevented,true);assert.equal(h.splash.dataset.phase,'leave');assert.equal(h.root.classList.contains('is-language-leaving'),true);assert.equal(JSON.parse(h.saved.get('asi-language-transition')).ui,'en');assert.equal(h.click().defaultPrevented,true);assert.equal(h.click('en',{ctrlKey:true}).defaultPrevented,false);h.advance(379);assert.equal(h.destinations.length,0);h.advance(1);assert.equal(h.destinations.length,1);assert.match(h.destinations[0],/ui=en/);h.restore();assert.equal(h.splash.dataset.phase,undefined);assert.equal(h.root.classList.contains('is-language-leaving'),false);}finally{h.close();}
});
test('language splash consumes valid arrival marker and rejects expired or wrong-language markers',async()=>{
 for(const pending of [{variant:2,ui:'ko',expires:Date.now()+10000},{variant:2,ui:'en',expires:Date.now()+10000},{variant:2,ui:'ko',expires:1}]){const h=await transitionHarness({pending});try{const valid=pending.ui==='ko'&&pending.expires>1;assert.equal(h.splash.dataset.phase,valid?'enter':undefined);assert.equal(h.saved.has('asi-language-transition'),false);h.advance(300);assert.equal(h.splash.dataset.phase,undefined);assert.equal(h.root.classList.contains('is-language-entering'),false);}finally{h.close();}}
});
test('language splash skips current language and reduced motion, tolerates storage denial',async()=>{
 const a=await transitionHarness({reduced:true});try{assert.equal(a.click('ko').defaultPrevented,true);assert.equal(a.click().defaultPrevented,false);assert.equal(a.splash.dataset.phase,undefined);a.advance(6000);assert.equal(a.destinations.length,0);}finally{a.close();}
 const b=await transitionHarness({denied:true});try{b.click();b.advance(380);assert.equal(b.destinations.length,1);b.advance(5000);assert.equal(b.root.classList.contains('is-language-leaving'),false);assert.equal(b.splash.dataset.phase,undefined);}finally{b.close();}
});
test('language splash rotates three variants and recovers when navigation stalls',async()=>{
 for(const current of [1,2,3]){const h=await transitionHarness({counter:current});try{h.click();assert.equal(h.splash.dataset.variant,String(current%3+1));h.advance(5000);assert.equal(h.splash.dataset.phase,undefined);assert.equal(h.saved.has('asi-language-transition'),false);h.click();h.advance(380);assert.equal(h.destinations.length,2);}finally{h.close();}}
});
test('clearing a result page returns to an empty home with durable language settings',async()=>{
 const x=await setup({query:'search?ui=ko&q=test&speaker=M3&lang=en_US&spoilers=1'});try{await tick();await tick();assert.equal(x.$('results').children.length,1);x.$('reset-search').click();assert.equal(x.w.location.pathname,'/');assert.equal(x.w.location.search.includes('q='),false);assert.equal(x.w.location.search.includes('speaker='),false);assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results').children.length,0);assert.equal(x.$('lang').value,'en_US');assert.equal(x.$('spoilers').checked,true);assert.equal(x.w.document.querySelector('.home-brand'),null);}finally{x.dom.window.close();}
});

const pairedFixture=()=>({...exampleItem,story:'zh_CN:test.txt',lang:'zh_CN',speaker:'凯尔希',text:'你好，合成测试',context:undefined,comparison:{lang:'ko_KR',status:'matched',method:'strict-command-structure-v1',items:[{...exampleItem,ordinal:7,text:'합성 번역',speaker:'켈시',alignment_method:'strict-command-structure-v1'}]}});
test('comparison preset uses Chinese with current UI translation and survives language links',async()=>{
 const x=await setup();try{await tick();x.$('compare').checked=true;x.$('compare').dispatchEvent(new x.w.Event('change'));assert.equal(x.$('lang').value,'zh_CN');assert.equal(x.$('translation-languages').hidden,false);assert.equal(x.$('translation-lang').value,'ko_KR');x.w.document.querySelector('[data-translation-lang="ja_JP"]').click();assert.equal(x.$('translation-lang').value,'ja_JP');const en=x.w.document.querySelector('[data-ui="en"]');en.dispatchEvent(new x.w.Event('pointerdown'));const url=new URL(en.href);assert.equal(url.searchParams.get('compare'),'1');assert.equal(url.searchParams.get('lang'),'zh_CN');assert.equal(url.searchParams.get('translation_lang'),'en_US');x.$('compare').checked=false;x.$('compare').dispatchEvent(new x.w.Event('change'));assert.equal(x.$('lang').value,'ko_KR');assert.equal(x.$('translation-languages').hidden,true);}finally{x.dom.window.close();}
});
test('paired results show original before translation, preserve counterpart source and lazy context',async()=>{
 const item=pairedFixture();const x=await setup({query:'search?compare=1&lang=zh_CN&translation_lang=ko_KR&q=你好',search:async url=>String(url).startsWith('/api/context?')?{items:[item],has_more:false}:{total:1,items:[item]}});try{await tick();await tick();const card=x.$('results').querySelector('article');assert.deepEqual([...card.querySelectorAll('.paired-line')].map(el=>el.lang),['zh-CN','ko-KR']);assert.equal(card.querySelectorAll('mark').length,1);assert.equal(card.querySelector('mark').textContent,'你好');assert.equal(x.calls.filter(u=>u.startsWith('/api/context?')).length,0);card.querySelector('.paired-line:last-child .info-button').click();assert.match(x.$('info-content').textContent,/원본 행8/);assert.match(x.$('info-content').textContent,/명령·분기/);x.$('info-dialog').close();const panel=card.querySelector('details');panel.open=true;panel.dispatchEvent(new x.w.Event('toggle'));await tick();await tick();const request=x.calls.find(u=>u.startsWith('/api/context?'));assert.match(request,/compare=1/);assert.match(request,/translation_lang=ko_KR/);assert.equal(panel.querySelectorAll('.paired-line').length,2);}finally{x.dom.window.close();}
});
test('missing correspondences stay explicit and reverse search keeps Chinese above translation',async()=>{
 const item=pairedFixture();const missing={...item,comparison:{status:'unverified',lang:'ko_KR',items:[]}};const reverse={...exampleItem,comparison:{status:'matched',lang:'zh_CN',items:[{...item,comparison:undefined}]}};
 const x=await setup({query:'search?compare=1&lang=ko_KR&q=시험',search:async()=>({total:2,items:[missing,reverse]})});try{await tick();await tick();const cards=x.$('results').querySelectorAll('article');assert.match(cards[0].querySelector('.pair-status').textContent,/대응 대사를 확인하지 못/);assert.equal(cards[0].querySelectorAll('.paired-line').length,1);assert.deepEqual([...cards[1].querySelectorAll('.paired-line')].map(n=>n.lang),['zh-CN','ko-KR']);}finally{x.dom.window.close();}
});
test('no-result original action opts in explicitly; clear retains comparison settings',async()=>{
 const x=await setup({search:async url=>String(url).includes('lang=zh_CN')?{total:1,items:[pairedFixture()]}:{total:0,items:[]}});try{x.$('query').value='你好';x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));await tick();await tick();assert.equal(x.$('compare').checked,false);assert.equal(x.$('search-original').hidden,false);x.$('search-original').click();await tick();await tick();assert.equal(x.$('compare').checked,true);assert.equal(x.$('lang').value,'zh_CN');assert.equal(x.$('results').querySelectorAll('.paired-line').length,2);x.$('reset-search').click();const url=new URL(x.w.location.href);assert.equal(url.searchParams.get('compare'),'1');assert.equal(url.searchParams.get('translation_lang'),'ko_KR');assert.equal(x.$('compare').checked,true);assert.equal(x.$('query').value,'');}finally{x.dom.window.close();}
});
