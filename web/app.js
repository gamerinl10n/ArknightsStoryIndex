const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const node = document.createElement(tag); node.textContent = text; if (cls) node.className = cls; return node; };
let offset = 0, last = null, suggestions = [], suggestionVersion = 0, requestVersion = 0, controller;
async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || '요청을 처리하지 못했어요. 다시 시도해주세요.');
  return data;
}
function guide() {
  const speaker = $('speaker').value.trim(), target = $('target').value.trim();
  const match = suggestions.find(row => row.value.toLocaleLowerCase() === speaker.toLocaleLowerCase());
  $('speaker').setCustomValidity('');
  $('speaker-help').textContent = match ? match.label : '이름 일부를 입력하면 자동완성 목록이 나타납니다.';
  $('target-help').textContent = target ? `‘${target}’의 이름·등록 별칭이 나오는 대사를 찾아요.` : '비워두면 말하는 인물의 전체 대사를 볼 수 있어요.';
  $('search-mode').textContent = !speaker ? '말하는 인물을 선택해 시작하세요.' : target ? `${speaker}의 대사에서 ${target} 찾기` : `${speaker}의 전체 대사 찾기`;
}
$('speaker').addEventListener('input', guide);
$('target').addEventListener('input', guide);
$('swap').onclick = () => { const speaker = $('speaker').value; $('speaker').value = $('target').value; $('target').value = speaker; guide(); $('speaker').focus(); };
api('/api/status').then(data => {
  if (data.dialogue_lines) $('data-status').textContent = `${data.dialogue_lines.toLocaleString()}개 대사`;
  else $('notice').textContent = '아직 수집된 데이터가 없습니다. 원본 동기화 후 검색할 수 있습니다.';
}).catch(() => {});
async function loadSpeakers() {
  const version = ++suggestionVersion;
  const params = new URLSearchParams({lang: $('lang').value, spoilers: $('spoilers').checked ? '1' : '0'});
  try {
    const rows = await api('/api/suggestions?' + params);
    if (version !== suggestionVersion) return;
    suggestions = rows;
    $('characters').replaceChildren();
    const fragment = document.createDocumentFragment();
    rows.forEach(row => { const option = el('option', ''); option.value = row.value; option.label = row.label; fragment.append(option); });
    $('characters').append(fragment);
    guide();
  } catch (error) {
    if (version !== suggestionVersion) return;
    suggestions = []; $('characters').replaceChildren();
    $('speaker-help').textContent = '자동완성을 불러오지 못했어요. 이름을 직접 입력해 검색할 수 있습니다.';
  }
}
$('lang').addEventListener('change', loadSpeakers);
$('spoilers').addEventListener('change', loadSpeakers);
loadSpeakers();
function render(item) {
  const card = el('article', '');
  card.append(el('h2', item.speaker));
  card.append(el('p', item.text, 'quote'));
  card.append(el('p', `${item.path} · 원본 ${item.ordinal + 1}행 · ${item.revision.slice(0, 12)}`, 'meta'));
  const context = el('details', ''); context.append(el('summary', '앞뒤 문맥 펼쳐보기'));
  item.context.forEach(row => {
    const paragraph = el('p', `${row.speaker || '이름 없음'}: ${row.text}`, row.ordinal === item.ordinal ? 'current-line' : '');
    if (row.branch !== 'main') paragraph.append(el('small', `\n분기: ${row.branch}`, 'branch-note'));
    context.append(paragraph);
  });
  card.append(context);
  if (item.parallel.length) {
    const parallel = el('details', ''); parallel.append(el('summary', '다른 언어 대사 · 같은 줄 위치의 대응 후보'));
    item.parallel.forEach(row => parallel.append(el('p', `${row.speaker}: ${row.text}`)));
    card.append(parallel);
  }
  const actions = el('div', '', 'result-actions');
  const copy = el('button', '대사·출처 복사'); copy.type = 'button';
  copy.onclick = async () => {
    try { await navigator.clipboard.writeText(`${item.speaker}: ${item.text}\n${item.source}@${item.revision} / ${item.lang}/${item.path}:${item.ordinal + 1}`); copy.textContent = '복사했어요 ✓'; }
    catch { copy.textContent = '복사하지 못했어요'; }
  };
  actions.append(copy); card.append(actions); $('results').append(card);
}
function empty(title, description) {
  $('empty-state').hidden = false;
  $('empty-state').querySelector('h3').textContent = title;
  $('empty-state').querySelector('p').textContent = description;
}
async function run(append = false) {
  const version = ++requestVersion, search = {...last};
  controller?.abort(); controller = new AbortController();
  $('more').disabled = true; $('submit-search').disabled = true; $('submit-search').textContent = '찾고 있어요…'; $('results').setAttribute('aria-busy', 'true');
  if (!append) { $('results').replaceChildren(); $('more').hidden = true; $('result-count').textContent = ''; $('empty-state').hidden = true; }
  $('notice').textContent = '대사를 찾고 있어요…';
  try {
    const params = new URLSearchParams(search); params.set('offset', offset);
    const data = await api('/api/search?' + params, {signal: controller.signal});
    if (version !== requestVersion) return;
    data.items.forEach(render); offset += data.items.length;
    $('more').hidden = offset >= data.total;
    $('results-title').textContent = search.target ? `${search.speaker}의 대사에서 ${search.target} 찾기` : `${search.speaker}의 전체 대사`;
    $('result-count').textContent = `${data.total.toLocaleString()}개 대사`;
    $('notice').textContent = '';
    if (!data.total) empty('조건에 맞는 대사를 찾지 못했어요', '자동완성에서 말하는 인물의 이름을 확인하거나, 찾을 인물·대사 속 표현을 지우고 다시 검색해보세요.');
  } catch (error) {
    if (version !== requestVersion || error.name === 'AbortError') return;
    $('notice').textContent = error.message;
    if (!append) empty('검색을 잠시 마치지 못했어요', '입력한 내용은 그대로 있어요. 검색 버튼을 눌러 다시 시도해주세요.');
  } finally {
    if (version === requestVersion) { $('more').disabled = false; $('submit-search').disabled = false; $('submit-search').textContent = '대사 검색 ↗'; $('results').setAttribute('aria-busy', 'false'); }
  }
}
function submit() {
  if (!$('speaker').value.trim()) { $('speaker').setCustomValidity('말하는 인물의 이름을 입력해주세요.'); $('speaker').reportValidity(); return; }
  offset = 0;
  last = {speaker: $('speaker').value.trim(), target: $('target').value.trim(), q: $('query').value.trim(), lang: $('lang').value, spoilers: $('spoilers').checked ? '1' : '0'};
  run();
}
$('search').onsubmit = event => { event.preventDefault(); submit(); };
$('more').onclick = () => run(true);
$('example-pair').onclick = () => { $('speaker').value = 'M3'; $('target').value = $('lang').value === 'ko_KR' ? '켈시' : '凯尔希'; $('query').value = ''; guide(); submit(); };
$('example-solo').onclick = () => { $('speaker').value = $('lang').value === 'ko_KR' ? '켈시' : '凯尔希'; $('target').value = ''; $('query').value = ''; guide(); submit(); };
