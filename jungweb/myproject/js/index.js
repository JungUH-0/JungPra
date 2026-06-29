// ===================== index.js =====================
// index.html 전용 JS
// [chap18] BOM - localStorage 활용
// [chap19] DOM - querySelector로 요소 선택 및 텍스트 조작
// [chap20] LocalStorage - 방문 시간, 플레이리스트 개수 저장/불러오기

// 재방문자 배너: 이전 방문 시간을 LocalStorage에서 읽어 화면에 표시
const lastVisit = localStorage.getItem('lastVisit');
const visitBanner = document.getElementById('visitBanner');

if (lastVisit && visitBanner) {
  const date = new Date(lastVisit);
  // padStart(2,'0') : 한 자리 숫자 앞에 0을 붙여 두 자리로 맞춤
  const formatted =
    `${date.getFullYear()}.${String(date.getMonth()+1).padStart(2,'0')}.${String(date.getDate()).padStart(2,'0')} ` +
    `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
  visitBanner.textContent = `🎵 지난 방문: ${formatted} — 다시 오셨네요!`;
  visitBanner.classList.remove('hidden');
}

// 현재 방문 시간을 LocalStorage에 저장 (다음 방문 때 배너로 사용)
localStorage.setItem('lastVisit', new Date().toISOString());

// nav의 플레이리스트 링크에 저장된 곡 수 표시
const saved = JSON.parse(localStorage.getItem('playlist') || '[]');
const playlistCount = document.getElementById('playlistCount');
if (playlistCount) {
  playlistCount.textContent = saved.length > 0
    ? `♥ 내 플레이리스트 ${saved.length}곡`
    : '♥ 내 플레이리스트';
}
