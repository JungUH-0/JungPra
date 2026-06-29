// ===================== playlist.js =====================
// playlist.html 전용 JS
// [chap18] 배열 map(), filter()로 저장된 음악 데이터 처리
// [chap19] DOM - innerHTML 동적 렌더링, classList
// [chap20] LocalStorage - 플레이리스트/최근 본 음악 파싱 및 출력

// 장르별 썸네일 색상 CSS 클래스 매핑 객체
const thumbClass = {
  lofi: 'lofi-thumb', pop: 'drive-thumb', jazz: 'jazz-thumb',
  indie: 'indie-thumb', rnb: 'rnb-thumb', hiphop: 'hiphop-thumb',
  classical: 'classical-thumb', electronic: 'electronic-thumb', drive: 'drive-thumb'
};

// LocalStorage의 playlist 배열을 읽어 저장된 음악 카드를 렌더링하는 함수
function renderPlaylist() {
  const saved = JSON.parse(localStorage.getItem('playlist') || '[]');
  const grid  = document.getElementById('playlistGrid');
  const empty = document.getElementById('emptyState');

  if (saved.length === 0) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  // 저장된 id 배열을 musicData에서 찾아 음악 객체 배열로 변환
  const items = saved
    .map(id => musicData.find(m => m.id === id))
    .filter(Boolean);

  grid.innerHTML = items.map(item => `
    <div class="music-card" onclick="location.href='detail.html?id=${item.id}'">
      <div class="music-thumb ${thumbClass[item.thumb] || 'lofi-thumb'}">
        <span class="music-play">▶</span>
        <button class="heart-btn active"
          onclick="removeFromPlaylist(event, ${item.id})">♥</button>
      </div>
      <div class="music-info">
        <div class="music-tags">${item.tags.map(t => `<span>${t}</span>`).join('')}</div>
        <h4>${item.title}</h4>
        <p>${item.artist}</p>
        <button class="btn-sm"
          onclick="event.stopPropagation(); location.href='detail.html?id=${item.id}'">자세히 보기</button>
      </div>
    </div>
  `).join('');
}

// LocalStorage의 recentMusic 배열을 읽어 최근 본 음악 카드를 렌더링하는 함수
function renderRecentMusic() {
  const recent  = JSON.parse(localStorage.getItem('recentMusic') || '[]');
  const section = document.getElementById('recentSection');
  const grid    = document.getElementById('recentGrid');

  if (!section || recent.length === 0) return;

  section.classList.remove('hidden');

  const items = recent
    .map(id => musicData.find(m => m.id === id))
    .filter(Boolean);

  grid.innerHTML = items.map(item => `
    <div class="music-card" onclick="location.href='detail.html?id=${item.id}'">
      <div class="music-thumb ${thumbClass[item.thumb] || 'lofi-thumb'}">
        <span class="music-play">▶</span>
      </div>
      <div class="music-info">
        <div class="music-tags">${item.tags.map(t => `<span>${t}</span>`).join('')}</div>
        <h4>${item.title}</h4>
        <p>${item.artist}</p>
      </div>
    </div>
  `).join('');
}

// 하트 버튼 클릭 시 해당 음악을 playlist 배열에서 제거하고 화면을 재렌더링하는 함수
function removeFromPlaylist(event, id) {
  event.stopPropagation();
  const saved   = JSON.parse(localStorage.getItem('playlist') || '[]');
  const updated = saved.filter(savedId => savedId !== id);
  localStorage.setItem('playlist', JSON.stringify(updated));
  renderPlaylist();
}

// 확인 후 playlist 키를 전체 삭제하고 빈 상태 화면으로 재렌더링하는 함수
function clearPlaylist() {
  if (!confirm('플레이리스트를 전부 비울까요?')) return;
  localStorage.removeItem('playlist');
  renderPlaylist();
}

// 초기 실행: 페이지 로드 시 저장된 목록 출력
renderPlaylist();
renderRecentMusic();
