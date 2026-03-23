import flet as ft
import random

def main(page: ft.Page):
    page.title = "숫자 맞추기 게임"
    page.window_width = 400
    page.window_height = 600

    # 1. 메뉴 화면 보여주기
    def show_menu():
        page.clean() # 기존 화면 싹 지우기
        page.add(
            ft.Column(
                [
                    ft.Text("숫자 맞추기 게임", size=40, weight="bold"),
                    ft.Text("모드를 선택하세요", size=20),
                    ft.ElevatedButton(
                        "목숨 있는 버전 (10회)", 
                        on_click=lambda _: start_game(is_infinite=False),
                        width=250
                    ),
                    ft.ElevatedButton(
                        "무제한 버전", 
                        on_click=lambda _: start_game(is_infinite=True),
                        width=250
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        )
        page.update()

    # 2. 게임 실행 화면
    def start_game(is_infinite):
        page.clean()
        
        # 설정값 초기화
        count = 10
        ran = random.randint(1, 50)
        print(f"정답: {ran}")

        # UI 요소 생성
        title_txt = "무제한 모드" if is_infinite else "목숨 모드"
        txt_display = ft.Text("기회: ∞" if is_infinite else f"남은 목숨 : {count}", size=20)
        num_input = ft.TextField(label="1~50 입력", width=200)
        msg = ft.Text(" ")

        def num_chk(e):
            nonlocal count # 함수 밖의 변수를 수정하기 위해 사용
            
            try:
                if not num_input.value:
                    msg.value = "숫자를 입력하세요!"
                    page.update()
                    return
                val = int(num_input.value)
            except ValueError:
                msg.value = "숫자만 입력 가능합니다!"
                page.update()
                return

            if val == ran:
                msg.value = "🎉 정답입니다!"
                msg.color = "blue"
                # 정답 맞추면 메뉴로 돌아가는 버튼 추가
                page.add(ft.TextButton("메뉴로 돌아가기", on_click=lambda _: show_menu()))
            else:
                msg.value = "❌ 틀렸습니다!"
                msg.color = "orange"
                if not is_infinite:
                    count -= 1
                    txt_display.value = f"남은 목숨 : {count}"

            # 게임 오버 체크 (목숨 모드일 때만)
            if not is_infinite and count <= 0:
                page.clean()
                page.add(
                    ft.Text("💀 게임 오버!", size=40, color="red"),
                    ft.ElevatedButton("메뉴로 돌아가기", on_click=lambda _: show_menu())
                )
            
            page.update()

        # 게임 화면 구성
        page.add(
            ft.Text(title_txt, size=30, weight="bold"),
            txt_display,
            num_input,
            ft.ElevatedButton("확인", on_click=num_chk),
            msg,
            ft.TextButton("게임 포기하고 메뉴로", on_click=lambda _: show_menu())
        )
        page.update()

    # 처음 시작할 때 메뉴 보여주기
    show_menu()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)