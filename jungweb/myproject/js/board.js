// ===================== board.js =====================
// board.html 전용 JS
// [chap05] HTML 폼 - input, select, button
// [chap16] 조건문으로 입력값 검증
// [chap17] 함수 선언, 이벤트 처리
// [chap18] 배열 push(), splice(), reverse()로 데이터 관리
// [chap19] DOM - innerHTML 동적 렌더링, createElement
// [chap20] LocalStorage - 감상평 배열 누적 저장

// musicData 배열을 순회하며 음악 선택 드롭다운에 option을 동적으로 추가
const selectEl = document.getElementById('inputMusic');
musicData.forEach(item => {
  const opt = document.createElement('option');
  opt.value       = item.id;
  opt.textContent = item.title;
  selectEl.appendChild(opt);
});

// LocalStorage의 boardComments 배열을 읽어 감상평 피드를 최신순으로 렌더링하는 함수
function renderBoard() {
  const comments = JSON.parse(localStorage.getItem('boardComments') || '[]');
  const feed  = document.getElementById('boardFeed');
  const empty = document.getElementById('emptyState');

  document.getElementById('commentCount').textContent = comments.length;

  if (comments.length === 0) {
    feed.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  // 원본 배열을 복사 후 뒤집어 최신 감상평이 위에 오도록 정렬
  const sorted = [...comments].reverse();

  feed.innerHTML = sorted.map((c, reversedIdx) => {
    // 삭제 시 원본 배열의 정확한 인덱스를 전달하기 위해 역산
    const realIdx = comments.length - 1 - reversedIdx;
    const music = musicData.find(m => m.id === parseInt(c.musicId));
    return `
      <div class="board-card">
        <div class="board-card-top">
          <div class="board-avatar">${c.nickname.charAt(0)}</div>
          <div class="board-meta">
            <span class="board-nickname">${c.nickname}</span>
            <span class="board-date">${c.date}</span>
          </div>
          <button class="board-delete" onclick="deleteComment(${realIdx})">✕</button>
        </div>
        ${music ? `<div class="board-music-ref">🎵 ${music.title}</div>` : ''}
        <p class="board-text">${c.comment}</p>
      </div>
    `;
  }).join('');
}

// 입력값을 검증하고 새 감상평을 LocalStorage 배열에 추가한 뒤 피드를 재렌더링하는 함수
function submitComment() {
  const nickname = document.getElementById('inputNickname').value.trim();
  const musicId  = document.getElementById('inputMusic').value;
  const comment  = document.getElementById('inputComment').value.trim();

  if (!nickname) { alert('닉네임을 입력해주세요.'); return; }
  if (!comment)  { alert('감상평을 입력해주세요.'); return; }

  const comments = JSON.parse(localStorage.getItem('boardComments') || '[]');

  // 현재 날짜를 포맷팅해서 감상평 객체에 포함
  const now  = new Date();
  const date = `${now.getFullYear()}.${String(now.getMonth()+1).padStart(2,'0')}.${String(now.getDate()).padStart(2,'0')}`;

  // 새 감상평 객체를 배열 끝에 추가
  comments.push({ nickname, musicId, comment, date });
  localStorage.setItem('boardComments', JSON.stringify(comments));

  document.getElementById('inputComment').value = '';
  renderBoard();
}

// 해당 인덱스의 감상평을 LocalStorage 배열에서 제거하고 피드를 재렌더링하는 함수
function deleteComment(idx) {
  if (!confirm('이 감상평을 삭제할까요?')) return;
  const comments = JSON.parse(localStorage.getItem('boardComments') || '[]');
  comments.splice(idx, 1);
  localStorage.setItem('boardComments', JSON.stringify(comments));
  renderBoard();
}

// 확인 후 boardComments 키를 전체 삭제하고 빈 상태 화면으로 재렌더링하는 함수
function clearBoard() {
  if (!confirm('감상평을 전부 삭제할까요?')) return;
  localStorage.removeItem('boardComments');
  renderBoard();
}

// 감상평 입력창에서 Enter 키를 누르면 등록 함수를 실행하는 이벤트
document.getElementById('inputComment').addEventListener('keydown', e => {
  if (e.key === 'Enter') submitComment();
});

// 초기 실행: 페이지 로드 시 저장된 감상평 출력
renderBoard();
