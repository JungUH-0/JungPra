// ===================== detail.js =====================
// detail.html 전용 JS
// [chap17] 함수, find()로 데이터 검색
// [chap18] 배열 filter(), slice()로 관련 음악 추출
// [chap19] DOM - innerHTML로 동적 렌더링, classList
// [chap20] LocalStorage - 하트 상태 저장, 최근 본 음악 기록

// 장르별 썸네일 색상 CSS 클래스 매핑 객체
const thumbClass = {
  lofi: 'lofi-thumb', pop: 'drive-thumb', jazz: 'jazz-thumb',
  indie: 'indie-thumb', rnb: 'rnb-thumb', hiphop: 'hiphop-thumb',
  classical: 'classical-thumb', electronic: 'electronic-thumb', drive: 'drive-thumb'
};

// 상세 페이지 메타 정보를 한글로 표시하기 위한 매핑 객체
const genreLabel = { lofi:'로파이', pop:'팝', jazz:'재즈', indie:'인디', rnb:'R&B', hiphop:'힙합', classical:'클래식', electronic:'일렉트로닉' };
const placeLabel = { cafe:'카페', home:'집', drive:'드라이브', gym:'헬스장', study:'공부방/도서관', outdoor:'야외' };
const moodLabel  = { focus:'집중', excited:'신남', healing:'힐링', romantic:'설렘', sad:'우울', motivated:'의욕' };

// URL의 ?id= 값을 파싱해서 숫자로 변환
const params = new URLSearchParams(window.location.search);
const id = parseInt(params.get('id'));

// musicData 배열에서 id가 일치하는 음악 데이터 하나를 검색
const music = musicData.find(item => item.id === id);

// 음악 데이터가 없으면 에러 화면, 있으면 상세 정보를 렌더링
if (!music) {
  document.getElementById('detailContainer').innerHTML = `
    <div style="text-align:center; padding: 120px 24px;">
      <div style="font-size:3rem; margin-bottom:16px;">🎵</div>
      <h2>음악을 찾을 수 없어요</h2>
      <p style="color:var(--gray); margin: 12px 0 24px;">잘못된 주소이거나 삭제된 항목이에요.</p>
      <a href="list.html" class="btn-primary">목록으로 돌아가기</a>
    </div>
  `;
} else {
  document.title = `${music.title} — Moodify`;

  // LocalStorage에서 플레이리스트 배열을 읽어 현재 음악 저장 여부 확인
  const saved   = JSON.parse(localStorage.getItem('playlist') || '[]');
  const isLiked = saved.includes(music.id);

  // youtubeUrl에서 영상 ID 추출
  // "https://www.youtube.com/watch?v=jfKfPfyJRdk" → "jfKfPfyJRdk"
  const ytUrl   = new URL(music.youtubeUrl);
  const videoId = ytUrl.searchParams.get('v');

  // 임베드 URL 생성: watch?v= → embed/ 형태로 변환
  // autoplay=0: 자동재생 안 함 / rel=0: 관련 영상 숨김
  const embedUrl = `https://www.youtube.com/embed/${videoId}?rel=0`;

  // 상세 페이지 HTML 전체를 동적으로 렌더링
  document.getElementById('detailContainer').innerHTML = `
    <div class="detail-hero">
      <!-- 기존 색상 박스 대신 유튜브 iframe 플레이어 삽입 -->
      <div class="detail-thumb detail-iframe-wrap">
        <iframe
          src="${embedUrl}"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
          allowfullscreen
          style="width:100%; height:100%; border-radius:16px;">
        </iframe>
      </div>
      <div class="detail-info">
        <a href="list.html" class="back-link">← 목록으로</a>
        <div class="music-tags" style="margin-bottom:16px;">
          ${music.tags.map(t => `<span>${t}</span>`).join('')}
        </div>
        <h1 class="detail-title">${music.title}</h1>
        <p class="detail-artist">${music.artist}</p>
        <p class="detail-desc">${music.desc}</p>
        <div class="detail-meta">
          <div class="meta-item"><span class="meta-label">장르</span><span class="meta-val">${genreLabel[music.genre] || music.genre}</span></div>
          <div class="meta-item"><span class="meta-label">장소</span><span class="meta-val">${placeLabel[music.place] || music.place}</span></div>
          <div class="meta-item"><span class="meta-label">기분</span><span class="meta-val">${moodLabel[music.mood] || music.mood}</span></div>
        </div>
        <div class="detail-btns">
          <a href="${music.youtubeUrl}" target="_blank" class="btn-primary">▶ 유튜브에서 듣기</a>
          <button class="btn-outline heart-detail ${isLiked ? 'liked' : ''}"
            onclick="togglePlaylist(${music.id}, this)">
            ${isLiked ? '♥ 플레이리스트에서 제거' : '♡ 내 플레이리스트에 추가'}
          </button>
        </div>
      </div>
    </div>
  `;

  // 현재 음악을 최근 본 목록에 기록
  saveRecentMusic(music.id);

  // 같은 mood의 음악 중 현재 음악을 제외하고 최대 3개를 추출해 렌더링
  const related = musicData
    .filter(item => item.mood === music.mood && item.id !== music.id)
    .slice(0, 3);

  const relatedGrid = document.getElementById('relatedGrid');
  if (related.length === 0) {
    relatedGrid.innerHTML = '<p style="color:var(--gray)">비슷한 음악이 없어요.</p>';
  } else {
    relatedGrid.innerHTML = related.map(item => `
      <div class="music-card" onclick="location.href='detail.html?id=${item.id}'">
        <div class="music-thumb ${thumbClass[item.thumb] || 'lofi-thumb'}">
          <span class="music-play">▶</span>
        </div>
        <div class="music-info">
          <div class="music-tags">${item.tags.map(t => `<span>${t}</span>`).join('')}</div>
          <h4>${item.title}</h4>
          <p>${item.artist}</p>
          <button class="btn-sm">자세히 보기</button>
        </div>
      </div>
    `).join('');
  }
}

// 상세 페이지 방문 시 해당 음악 id를 최근 본 목록에 추가하고 최대 5개로 유지하는 함수
function saveRecentMusic(id) {
  let recent = JSON.parse(localStorage.getItem('recentMusic') || '[]');
  // 중복 제거 후 맨 앞에 추가
  recent = recent.filter(r => r !== id);
  recent.unshift(id);
  // 5개 초과 시 앞에서 5개만 유지
  recent = recent.slice(0, 5);
  localStorage.setItem('recentMusic', JSON.stringify(recent));
}

// 하트 버튼 클릭 시 LocalStorage playlist 배열에 해당 음악을 추가하거나 제거하는 함수
function togglePlaylist(id, btn) {
  const saved = JSON.parse(localStorage.getItem('playlist') || '[]');
  const idx   = saved.indexOf(id);

  if (idx === -1) {
    saved.push(id);
    btn.textContent = '♥ 플레이리스트에서 제거';
    btn.classList.add('liked');
  } else {
    saved.splice(idx, 1);
    btn.textContent = '♡ 내 플레이리스트에 추가';
    btn.classList.remove('liked');
  }
  localStorage.setItem('playlist', JSON.stringify(saved));
}