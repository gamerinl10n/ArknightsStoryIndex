const {test} = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const html = execFileSync('python', ['-c', "from app import create_app; print(create_app(readonly=True).test_client().get('/').text)"], {encoding:'utf8'});
const source = name => fs.readFileSync('web/' + name, 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const exampleItem = {speaker:'Mon3tr',text:'시험 대상의 시험 대사',path:'test.txt',ordinal:1,revision:'test-sha',source:'test/source',lang:'ko_KR',context:[{speaker:'Mon3tr',text:'시험 문맥',ordinal:1,branch:'main'}],parallel:[]};
function setup(options = {}) {
  const dom = new JSDOM(html, {runScripts:'outside-only',url:'https://asi.test/'});
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
  w.eval(source('theme.js')); w.eval(source('chrome.js')); w.eval(source('app.js'));
  return {dom,w,calls,$:id=>w.document.getElementById(id)};
}
test('search guides retain native completion, aliases, example flow and context', async()=>{
  const x=setup();try {
    await tick();await tick();
    assert.equal(x.$('speaker').getAttribute('list'),'characters');
    assert.equal(x.$('target').getAttribute('list'),'characters');
    assert.equal(x.$('characters').options.length,2);
    x.$('speaker').value='켈시';x.$('speaker').dispatchEvent(new x.w.Event('input'));
    assert.match(x.$('speaker-help').textContent,/10개 대사/);
    x.$('example-pair').click();await tick();await tick();
    assert(x.calls.some(url=>url.includes('speaker=M3')&&url.includes('target=')));
    assert.match(x.$('results-title').textContent,/M3.*켈시/);
    assert.equal(x.$('results').querySelectorAll('article').length,1);
    assert(x.$('results').querySelector('.current-line'));
    assert.equal(x.w.localStorage.length,0);
    assert.equal(x.w.document.querySelectorAll('#admin').length,0);
  } finally{x.dom.window.close();}
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
    assert.match(x.$('speaker-help').textContent,/직접 입력/);
    x.$('speaker').value='M3';x.$('search').dispatchEvent(new x.w.Event('submit',{cancelable:true}));
    await tick();await tick();assert.equal(x.$('results').querySelectorAll('article').length,1);
  } finally{x.dom.window.close();}
});
test('empty search explains how to broaden results',async()=>{
  const x=setup({search:async()=>({total:0,items:[]})});try {
    x.$('example-solo').click();await tick();await tick();
    assert.equal(x.$('empty-state').hidden,false);
    assert.match(x.$('empty-state').textContent,/조건에 맞는 대사/);
    assert.equal(x.$('more').hidden,true);
    assert.equal(x.$('results').getAttribute('aria-busy'),'false');
  } finally{x.dom.window.close();}
});
test('late responses cannot replace a newer search',async()=>{
  const resolvers=[];const x=setup({search:()=>new Promise(resolve=>resolvers.push(resolve))});try {
    x.$('example-pair').click();x.$('example-solo').click();
    resolvers[1]({total:0,items:[]});await tick();await tick();
    resolvers[0]({total:1,items:[exampleItem]});await tick();await tick();
    assert.match(x.$('results-title').textContent,/켈시의 전체/);
    assert.equal(x.$('results').querySelectorAll('article').length,0);
  } finally{x.dom.window.close();}
});
