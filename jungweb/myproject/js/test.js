// ===================== test.js =====================
// test.html 전용 JS
// [chap16] 조건문, 변수 선언
// [chap17] 함수 선언, 이벤트 처리
// [chap19] DOM - querySelectorAll, classList, dataset
// [chap20] LocalStorage - 이전 테스트 결과 기억

// 3단계 선택 결과를 저장하는 객체 (초기값 null = 미선택)
const state = {
  genre: null,
  place: null,
  mood:  null
};

// 영어 값을 화면에 표시할 한글 이름으로 변환하는 매핑 객체
const labels = {
  genre: {
    lofi: '로파이', pop: '팝', jazz: '재즈', indie: '인디',
    rnb: 'R&B', hiphop: '힙합', classical: '클래식', electronic: '일렉트로닉'
  },
  place: {
    cafe: '카페', home: '집', drive: '드라이브',
    gym: '헬스장', study: '공부방/도서관', outdoor: '야외'
  },
  mood: {
    focus: '집중하고 싶어', excited: '신나고 에너지 넘쳐',
    healing: '쉬고 싶어, 힐링', romantic: '감성적이야',
    sad: '우울하거나 쓸쓸해', motivated: '의욕이 넘쳐'
  }
};

// 이전 테스트 결과를 LocalStorage에서 불러와 배너로 안내
const lastResult = JSON.parse(localStorage.getItem('lastTestResult') || 'null');
if (lastResult) {
  const banner = document.getElementById('lastResultBanner');
  if (banner) {
    banner.textContent =
      `지난번엔 "${labels.genre[lastResult.genre] || lastResult.genre}" 장르를 선택했어요 🎵`;
    banner.classList.remove('hidden');
  }
}

// 선택 버튼 클릭 시 선택 상태 업데이트 및 다음 버튼 활성화
document.querySelectorAll('.choice-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const step  = btn.dataset.step;
    const value = btn.dataset.value;

    // 같은 단계의 다른 버튼 selected 해제 후 클릭한 버튼만 selected 적용
    document.querySelectorAll(`[data-step="${step}"]`).forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');

    // state 객체에 선택값 저장
    state[step] = value;

    // 하단 요약 바 텍스트 업데이트
    updateSummary(step, value);

    // 다음 버튼 disabled 해제
    const nextBtnMap = { genre: 'next1', place: 'next2', mood: 'next3' };
    const nextBtn = document.getElementById(nextBtnMap[step]);
    if (nextBtn) nextBtn.disabled = false;
  });
});

// 하단 고정 요약 바에 선택된 값을 한글로 표시하는 함수
function updateSummary(step, value) {
  const textEl = document.getElementById(`text-${step}`);
  if (textEl) {
    textEl.textContent = labels[step][value] || value;
    textEl.classList.add('selected');
  }
}

// 단계에 따라 상단 진행 바(progress-bar) 너비를 변경하는 함수
function updateProgress(step) {
  const bar = document.getElementById('progressBar');
  const pct = { 1: '33.33%', 2: '66.66%', 3: '100%' };
  bar.style.width = pct[step] || '33.33%';
}

// 현재 단계를 숨기고 다음 단계를 보여주는 함수
function nextStep(stepNum) {
  document.querySelectorAll('.step').forEach(s => s.classList.add('hidden'));
  document.getElementById(`step${stepNum}`).classList.remove('hidden');
  updateProgress(stepNum);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 현재 단계를 숨기고 이전 단계로 돌아가는 함수
function prevStep(stepNum) {
  nextStep(stepNum);
}

// 3단계 선택 완료 후 선택값을 Query String으로 변환해 list.html로 이동하는 함수
function goToResult() {
  if (!state.genre || !state.place || !state.mood) {
    alert('모든 항목을 선택해주세요!');
    return;
  }

  // 다음 방문 때 배너로 안내하기 위해 결과 저장
  localStorage.setItem('lastTestResult', JSON.stringify({
    genre: state.genre,
    place: state.place,
    mood:  state.mood
  }));

  // 선택값을 Query String으로 변환 후 list.html로 페이지 이동
  const params = new URLSearchParams({
    genre: state.genre,
    place: state.place,
    mood:  state.mood
  });
  window.location.href = `list.html?${params.toString()}`;
}
