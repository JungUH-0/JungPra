// 1. 요소 가져오기
const container = document.querySelector('#container');
const imgNameInput = document.querySelector('#imgName');
const addBtn = document.querySelector('#addBtn');

// 2. 카드 추가 함수 정의
function createCard() {
    const nameValue = imgNameInput.value.trim();

    // 예외 처리: 빈 입력값 차단
    if (nameValue === '') {
        alert('이미지 이름을 입력해주세요!');
        imgNameInput.focus();
        return;
    }

    // div DOM 요소 생성
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card'; // CSS 디자인 입히기

    const imgEl = document.createElement('img');
    // 사용자가 입력한 이름을 바탕으로 이미지 경로 설정 (예: images/tree-1.jpg)
    imgEl.src = `images/${nameValue}.jpg`; 
    imgEl.alt = nameValue;

    const pEl = document.createElement('p');
    pEl.textContent = nameValue; // 설명 글로 이름 넣기

    // cardDiv 안에 이미지와 글자 집어 넣기
    cardDiv.appendChild(imgEl);
    cardDiv.appendChild(pEl);

    // cardDiv에 클릭하면 삭제되는 기능 붙이기
    cardDiv.addEventListener('click', function() {
        // confirm창은 '확인'을 누르면 true, '취소'를 누르면 false를 반환
        const isDelete = confirm(`"${nameValue}" 카드를 정말 삭제하시겠습니까?`);
        
        // 확인을 눌렀을 때만 나 자신(card)을 삭제!
        if (isDelete === true) {
            this.remove(); 
        }
    });

    // cardDiv 요소를 container 부모요소에 붙이기
    container.appendChild(cardDiv);

    // 입력창 비우고 포커스 주기
    imgNameInput.value = '';
    imgNameInput.focus();
}

// 이벤트 연결
addBtn.addEventListener('click', createCard);

// 엔터키를 눌러도 카드가 추가되도록 편의 기능 추가
imgNameInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        createCard();
    }
});