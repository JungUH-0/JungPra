const todoInput = document.querySelector('#todoInput');
const addBtn = document.querySelector('#addBtn');

function printTodo() {
    const todoText = todoInput.value.trim();

    //입력창이 비어있는지 확인하는 코드를 아래에 작성하세요.
    if (!todoText){
        alert('할 일을 입력하세요!');
        return;
    }

    // console.log(`[새로운 할 일] ${todoText}`);
    document.write('<p>[새로운 할 일]${todoText}</p>');

    // 입력창을 비우고 포커스 주는 코드를 아래에 작성하세요.
    todoInput.value='';
    todoInput.focus();


}

// 웹 요소에 직접 함수 연결하기: 함수 이름 뒤에 괄호()를 붙이지 않고 연결한다.
addBtn.onclick = printTodo;