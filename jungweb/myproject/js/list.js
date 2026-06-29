// ===================== list.js =====================
// list.html 전용 JS
// [chap12] CSS Grid - 카드 뷰 레이아웃
// [chap16] 조건문, 논리 연산자
// [chap17] 함수, 고차함수 filter(), map()
// [chap18] 배열 메서드 활용
// [chap19] DOM - 동적 카드 렌더링, innerHTML
// [chap20] LocalStorage - 하트 상태 유지, 최근 필터 저장

// 장르/장소/기분 필터 선택값 저장 객체 (빈 문자열 = 전체)
const filters = { genre: '', place: '', mood: '' };

// 장르별로 다른 그라디언트 색상 CSS 클래스를 적용하기 위한 매핑 객체
const thumbClass = {
  lofi: 'lofi-thumb', pop: 'drive-thumb', jazz: 'jazz-thumb',
  indie: 'indie-thumb', rnb: 'rnb-thumb', hiphop: 'hiphop-thumb',
  classical: 'classical-thumb', electronic: 'electronic-thumb', drive: 'drive-thumb'
};

// test.html에서 넘어올 때 URL에 붙은 Query String을 읽어 반환하는 함수
function parseQueryString() {
  const params = new URLSearchParams(window.location.search);
  return {
    genre: params.get('genre') || '',
    place: params.get('place') || '',
    mood:  params.get('mood')  || ''
  };
}

// 선택된 필터 버튼에 active 클래스를 적용해 UI를 동기화하는 함수
function setFilterChip(type, value) {
  document.querySelectorAll(`[data-type="${type}"]`).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.value === value);
  });
  filters[type] = value;
}

// 영어 값을 한글 이름으로 변환하는 매핑 객체 (헤더 태그 표시용)
const labelMap = {
  genre: { lofi:'로파이', pop:'팝', jazz:'재즈', indie:'인디', rnb:'R&B', hiphop:'힙합', classical:'클래식', electronic:'일렉트로닉' },
  place: { cafe:'카페', home:'집', drive:'드라이브', gym:'헬스장', study:'공부방/도서관', outdoor:'야외' },
  mood:  { focus:'집중', excited:'신남', healing:'힐링', romantic:'감성', sad:'우울', motivated:'의욕' }
};

// test.html에서 넘어온 경우 헤더 제목과 활성 태그를 추천 결과 전용으로 변경하는 함수
function updateHeader(genre, place, mood) {
  if (!genre && !place && !mood) return;

  document.getElementById('headerEyebrow').textContent = '맞춤 추천 결과';
  document.getElementById('headerTitle').textContent   = '딱 맞는 음악을 찾았어요 🎵';
  document.getElementById('headerDesc').textContent    = '선택한 조건에 맞는 음악들이에요.';

  const container = document.getElementById('activeFilters');
  container.innerHTML = '';
  if (genre) container.innerHTML += `<span class="active-tag">${labelMap.genre[genre] || genre}</span>`;
  if (place) container.innerHTML += `<span class="active-tag">${labelMap.place[place] || place}</span>`;
  if (mood)  container.innerHTML += `<span class="active-tag">${labelMap.mood[mood]   || mood}</span>`;
}

// 필터링된 음악 배열을 카드 HTML로 변환해서 화면에 출력하는 함수
function renderCards(data) {
  const grid  = document.getElementById('musicGrid');
  const empty = document.getElementById('emptyState');

  // 결과가 없으면 빈 상태 메시지 표시
  if (data.length === 0) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    document.getElementById('resultCount').textContent = '0';
    return;
  }

  empty.classList.add('hidden');
  document.getElementById('resultCount').textContent = data.length;

  // 배열 map()으로 각 음악 데이터를 카드 HTML 문자열로 변환
  grid.innerHTML = data.map(item => `
    <div class="music-card" onclick="location.href='detail.html?id=${item.id}'">
      <div class="music-thumb ${thumbClass[item.thumb] || 'lofi-thumb'}">
        <span class="music-play">▶</span>
        <button class="heart-btn ${getSavedIds().includes(item.id) ? 'active' : ''}"
          onclick="togglePlaylist(event, ${item.id})">♥</button>
      </div>
      <div class="music-info">
        <div class="music-tags">${item.tags.map(t => `<span>${t}</span>`).join('')}</div>
        <h4>${item.title}</h4>
        <p>${item.artist}</p>
        <button class="btn-sm" onclick="event.stopPropagation(); location.href='detail.html?id=${item.id}'">자세히 보기</button>
      </div>
    </div>
  `).join('');
}

// LocalStorage에서 저장된 플레이리스트 ID 배열을 읽어 반환하는 함수
function getSavedIds() {
  return JSON.parse(localStorage.getItem('playlist') || '[]');
}

// filters 객체를 기준으로 musicData를 필터링해 카드를 재렌더링하는 함수
function applyFilters() {
  const result = musicData.filter(item => {
    const matchGenre = !filters.genre || item.genre === filters.genre;
    const matchPlace = !filters.place || item.place === filters.place;
    const matchMood  = !filters.mood  || item.mood  === filters.mood;
    return matchGenre && matchPlace && matchMood;
  });
  renderCards(result);
}

// 모든 필터를 초기 상태로 되돌리고 전체 목록을 다시 표시하는 함수
function resetFilters() {
  filters.genre = ''; filters.place = ''; filters.mood = '';
  document.querySelectorAll('.filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.value === '');
  });
  document.getElementById('activeFilters').innerHTML = '';
  document.getElementById('headerEyebrow').textContent = '전체 탐색';
  document.getElementById('headerTitle').textContent   = '모든 음악 둘러보기';
  document.getElementById('headerDesc').textContent    = '장르, 장소, 기분으로 필터링해보세요.';
  applyFilters();
  history.replaceState(null, '', 'list.html');
}

// 하트 버튼 클릭 시 LocalStorage playlist 배열에 해당 음악을 추가하거나 제거하는 함수
function togglePlaylist(event, id) {
  event.stopPropagation();
  const btn   = event.currentTarget;
  const saved = getSavedIds();
  const idx   = saved.indexOf(id);

  if (idx === -1) {
    saved.push(id);
    btn.classList.add('active');
  } else {
    saved.splice(idx, 1);
    btn.classList.remove('active');
  }
  localStorage.setItem('playlist', JSON.stringify(saved));
}

// 현재 필터 상태를 LocalStorage에 기록하는 함수
function saveRecentFilter() {
  if (filters.genre || filters.place || filters.mood) {
    localStorage.setItem('recentFilter', JSON.stringify({
      genre: filters.genre,
      place: filters.place,
      mood:  filters.mood
    }));
  }
}

// 필터 칩 버튼 클릭 이벤트 등록
document.querySelectorAll('.filter-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    const type  = btn.dataset.type;
    const value = btn.dataset.value;
    setFilterChip(type, value);
    saveRecentFilter();
    applyFilters();
  });
});

// 초기 실행: URL 파라미터를 파싱해 필터를 세팅하고 카드를 렌더링
const { genre, place, mood } = parseQueryString();
setFilterChip('genre', genre);
setFilterChip('place', place);
setFilterChip('mood',  mood);
updateHeader(genre, place, mood);
applyFilters();
