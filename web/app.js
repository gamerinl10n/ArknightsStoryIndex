const $=id=>document.getElementById(id);
let token='',offset=0,last=null;
const el=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;};
async function api(url,options){const r=await fetch(url,options);const data=await r.json();if(!r.ok)throw Error(data.error||'요청 실패');return data;}
$('admin').onclick=()=>{token=prompt('관리자 토큰을 입력하세요. 이 탭 메모리에만 유지됩니다.')||'';$('admin').textContent=token?'관리자 토큰 입력됨':'관리자 인증';};
$('swap').onclick=()=>{const a=$('speaker').value;$('speaker').value=$('target').value;$('target').value=a;};
api('/api/speakers').then(names=>names.forEach(n=>{const o=el('option','');o.value=n;$('characters').append(o);})).catch(e=>$('notice').textContent=e.message);
function render(item){
 const card=el('article','');
 const verified=item.reviews.filter(r=>r.status==='reviewed'&&r.kind!=='rejected');
 card.append(el('h2',item.speaker+' · '+(verified.length?'검토 완료 용례':item.reviews.some(r=>r.status==='needs_review')?'재검토 필요':'미검토 대사')));
 card.append(el('p',item.text,'quote'));
 verified.forEach(r=>card.append(el('p',`${r.target} → ${r.expression||'호칭 없음'} · ${{direct:'직접 호칭',reference:'제삼자 지칭',related:'관련 대사'}[r.kind]}`)));
 card.append(el('p',`${item.path} · 원본 ${item.ordinal+1}행 · ${item.revision.slice(0,12)}`,'meta'));
 const context=el('details','');context.append(el('summary','앞뒤 문맥 · 분기 표기 포함'));
 item.context.forEach(r=>context.append(el('p',`[${r.branch}] ${r.speaker}: ${r.text}`)));
 card.append(context);
 if(item.parallel.length){const d=el('details','');d.append(el('summary','다른 언어의 같은 줄 위치 · 대응 미확인'));item.parallel.forEach(r=>d.append(el('p',`${r.speaker}: ${r.text}`)));card.append(d);}
 const copy=el('button','대사·출처 복사');copy.onclick=async()=>{try{await navigator.clipboard.writeText(`${item.speaker}: ${item.text}\n${item.source}@${item.revision} / ${item.lang}/${item.path}:${item.ordinal+1}`);copy.textContent='복사됨';}catch{copy.textContent='복사 실패';}};card.append(copy);
 const d=el('details','');d.append(el('summary','관리자 검토'));
 const f=el('form','','review');const target=el('input','');target.placeholder='대상 인물';target.value=$('target').value;target.required=true;
 const exp=el('input','');exp.placeholder='원문 속 호칭 표현';const kind=el('select','');Object.entries({direct:'직접 호칭',reference:'제삼자 지칭',related:'관련 대사',rejected:'후보 제외'}).forEach(([v,t])=>{const o=el('option',t);o.value=v;kind.append(o);});
 const save=el('button','검토 저장');f.append(target,exp,kind,save);f.onsubmit=async e=>{e.preventDefault();try{await api('/api/review',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({line:item.id,hash:item.hash,target:target.value,expression:exp.value,kind:kind.value})});save.textContent='저장 완료 · 재검색 시 반영';}catch(err){$('notice').textContent=err.message;}};d.append(f);card.append(d);$('results').append(card);
}
async function run(append=false){$('more').disabled=true;try{const params=new URLSearchParams(last);params.set('offset',offset);const data=await api('/api/search?'+params);if(!append)$('results').replaceChildren();data.items.forEach(render);offset+=data.items.length;$('more').hidden=offset>=data.total;$('notice').textContent=`${data.total.toLocaleString()}개 대사 · ${last.target?'이름 포함 후보와 검토 기록을 검색했습니다. 대상 인물의 별칭·대명사는 검토 전 누락될 수 있습니다.':'화자 표기 기준 검색입니다.'}`;}catch(e){$('notice').textContent=e.message;}finally{$('more').disabled=false;}}
$('search').onsubmit=e=>{e.preventDefault();offset=0;last={speaker:$('speaker').value.trim(),target:$('target').value.trim(),q:$('query').value,lang:$('lang').value,spoilers:$('spoilers').checked?'1':'0'};run();};$('more').onclick=()=>run(true);
