const {test} = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const html = execFileSync('python', ['-c', "from app import create_app; print(create_app(readonly=True).test_client().get('/').text)"], {encoding:'utf8'});
const uiCopy = execFileSync('python', ['-c', "from app import create_app; print(create_app(readonly=True).test_client().get('/i18n.js').text)"], {encoding:'utf8'});
const source = name => fs.readFileSync('web/' + name, 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const exampleItem = {story:'ko_KR:test.txt',speaker:'Mon3tr',text:'시험 대상의 시험 대사',path:'test.txt',ordinal:1,revision:'test-sha',source:'test/source',lang:'ko_KR',context:[{speaker:'Mon3tr',text:'시험 문맥',ordinal:1,branch:'main'}],parallel:[]};
function setup(options = {}) {
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
      data=[{value:'켈시',label:'10개 대사',count:10},{value:'M3',label:'Mon3tr · 5개 대사',count:5}];
    } else data=options.search ? await options.search(url,args) : {total:1,items:[exampleItem]};
    return {ok:true,json:async()=>data};
  };
  w.eval(uiCopy); w.eval(source('theme.js')); w.eval(source('chrome.js')); w.eval(source('app.js'));
  return {dom,w,calls,$:id=>w.document.getElementById(id)};
}
function enter(x,speaker='M3',target='켈시') {x.$('speaker').value=speaker;x.$('target').value=target;x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));}
test('attached completion supports keyboard selection, search and context', async()=>{
 const x=setup();try {
  await tick();await tick();x.$('speaker').focus();x.$('speaker').value='켈시';x.$('speaker').dispatchEvent(new x.w.Event('input'));
  assert.equal(x.$('speaker-options').hidden,false);assert.equal(x.$('speaker').getAttribute('aria-expanded'),'true');
  x.$('speaker').dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'ArrowDown',cancelable:true}));
  assert(x.$('speaker').getAttribute('aria-activedescendant'));
  x.$('speaker').dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'Enter',cancelable:true}));
  assert.equal(x.$('speaker').value,'켈시');assert.equal(x.$('speaker-options').hidden,true);
  enter(x);await tick();await tick();assert.match(x.w.location.search,/speaker=M3/);
  assert.equal(x.$('results').querySelectorAll('article').length,1);assert(x.$('results').querySelector('.current-line'));
  assert.equal(x.$('share-search').hidden,false);assert.equal(x.w.localStorage.length,0);
 }finally{x.dom.window.close();}
});
test('shared URLs restore corpus and search values independently',async()=>{
 const x=setup({query:'?speaker=M3&target=Kal%27tsit&lang=en_US&ui=ko&q=test&spoilers=1'});try {
  await tick();await tick();assert.equal(x.$('lang').value,'en_US');assert.equal(x.$('target').value,"Kal'tsit");assert.equal(x.$('query').value,'test');assert.equal(x.$('spoilers').checked,true);
  assert(x.calls.some(url=>url.startsWith('/api/search?')&&url.includes('lang=en_US')));
 }finally{x.dom.window.close();}
});
test('theme uses the same moon/sun control, persists and restores',()=>{
  const x=setup({theme:'dark'});try {
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
  const x=setup({noStorage:true,badSuggestions:true});try {
    await tick();x.$('themeButton').click();
    assert.equal(x.w.document.documentElement.dataset.theme,'dark');
    assert.equal(x.$('speaker-options').children.length,0);
    x.$('speaker').value='M3';x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));
    await tick();await tick();assert.equal(x.$('results').querySelectorAll('article').length,1);
  } finally{x.dom.window.close();}
});
test('empty search explains how to broaden results',async()=>{
  const x=setup({search:async()=>({total:0,items:[]})});try {
    enter(x,'켈시','');await tick();await tick();
    assert.equal(x.$('empty-state').hidden,false);
    assert.match(x.$('empty-state').textContent,/조건에 맞는 대사/);
    assert.equal(x.$('more').hidden,true);
    assert.equal(x.$('results').getAttribute('aria-busy'),'false');
  } finally{x.dom.window.close();}
});
test('late responses cannot replace a newer search',async()=>{
  const resolvers=[];const x=setup({search:()=>new Promise(resolve=>resolvers.push(resolve))});try {
    enter(x);enter(x,'켈시','');
    resolvers[1]({total:0,items:[]});await tick();await tick();
    resolvers[0]({total:1,items:[exampleItem]});await tick();await tick();
    assert.match(x.$('results-title').textContent,/켈시의 전체/);
    assert.equal(x.$('results').querySelectorAll('article').length,0);
  } finally{x.dom.window.close();}
});

test('expanded context loads a bounded window for the selected source',async()=>{
 const x=setup();try{enter(x);await tick();await tick();const button=x.$('results').querySelector('details button');button.click();await tick();await tick();assert(x.calls.some(url=>url.startsWith('/api/context?')&&url.includes('radius=18')&&url.includes('story=ko_KR')));assert.equal(button.disabled,false);}finally{x.dom.window.close();}
});

test('home and results are separate views; return and browser history preserve the draft',async()=>{
 const x=setup();x.w.scrollTo=()=>{};try {
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
 const a=setup({query:'search?speaker=M3&target=켈시&lang=ja_JP'}),b=setup({query:'?speaker=M3&target=켈시&view=home'});
 try{await tick();await tick();assert.equal(a.$('search-experience').dataset.view,'results');assert.equal(a.$('lang').value,'ja_JP');assert.equal(b.$('search-experience').dataset.view,'home');assert.equal(b.$('speaker').value,'M3');assert(!b.calls.some(url=>url.startsWith('/api/search?')));}finally{a.dom.window.close();b.dom.window.close();}
});
test('returning during a pending request prevents a late result from reopening the page',async()=>{
 let resolve;const x=setup({search:()=>new Promise(r=>resolve=r)});x.w.scrollTo=()=>{};
 try{enter(x);assert.equal(x.$('search-loading').hidden,false);x.$('back-search').click();resolve({total:1,items:[exampleItem]});await tick();await tick();assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results-panel').hidden,true);assert.equal(x.$('search-loading').hidden,true);assert.equal(x.$('submit-search').disabled,false);assert.equal(x.$('results').children.length,0);}finally{x.dom.window.close();}
});
test('reduced motion avoids native page transitions',async()=>{
 const x=setup();let transitions=0;x.w.matchMedia=()=>({matches:true});x.w.document.startViewTransition=()=>{transitions++;throw Error('not expected');};
 try{enter(x);await tick();await tick();assert.equal(transitions,0);assert.equal(x.$('search-experience').dataset.view,'results');}finally{x.dom.window.close();}
});

test('a delayed view transition cannot undo a newer navigation',async()=>{
 const x=setup();x.w.scrollTo=()=>{};const frames=[];
 x.w.document.startViewTransition=apply=>{frames.push(apply);return {finished:Promise.resolve(),skipTransition(){}};};
 try{enter(x);x.$('back-search').click();frames.forEach(apply=>apply());await tick();await tick();assert.equal(x.$('search-experience').dataset.view,'home');assert.equal(x.$('results-panel').hidden,true);}finally{x.dom.window.close();}
});
