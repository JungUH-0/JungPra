import flet as ft
import random
import os


count = 0

def main(page: ft.Page):
    # 이미지 파일이 있는 폴더 경로 설정 (spring.jpg 인식용)
    page.assets_dir = os.path.dirname(__file__)
    page.padding = 0
    page.title = "가위바위보 게임"
    
    # 승리 횟수 저장
    win_count = {'user': 0, 'com': 0}

    # UI 요소 생성 
    play_cout_text = ft.Text(f"경기 횟수: {count}", color="black", size=30)
    wcount_text = ft.Text(f"com : 0 : user : 0", color="white", size=20, weight="bold")
    result_text = ft.Text("게임 시작", size=30, color="blue500", weight="bold")
    final_text = ft.Text("", color="white", size=18, text_align="center")
    
    results = {
        '가위': {'가위': '무승부', '바위': 'com', '보': 'user'},
        '바위': {'가위': 'user', '바위': '무승부', '보': 'com'},
        '보': {'가위': 'com', '바위': 'user', '보': '무승부'}
    }

    # 게임 플레이 함수 
    def play(e):
        global count
        nonlocal win_count
        
        user_choice = e.control.data 
        com_choice = random.choice(['가위', '바위', '보'])
     #    print(com_choice)
        winner = results[user_choice][com_choice]
        
        count += 1
        
        # 승자 체크 및 점수 합산
        if winner == 'com':
            win_count['com'] += 1
        elif winner == 'user':
            win_count['user'] += 1
            
        # 화면 텍스트 갱신
        play_cout_text.value = f"경기 횟수: {count}"
        wcount_text.value = f"com : {win_count['com']} : user : {win_count['user']}"
        
        if (winner == '무승부'):
            final_text.value = f"이번 판 결과: {winner}\n(나: {user_choice} vs 컴: {com_choice})"
        else:
            final_text.value = f"이번 판 결과: {winner} 승리!\n(나: {user_choice} vs 컴: {com_choice})"

        #  3승 종료
        if win_count['user'] == 3 or win_count['com'] == 3:
            for btn in buttons:
                btn.disabled = True
            winner_name = "사용자" if win_count['user'] == 3 else "컴퓨터"
            result_text.value = f"🏆 최종 승리: {winner_name} 🏆"
            final_text.value = "게임을 다시 하려면 리셋을 눌러주세요."
        
        #  5판 자동 초기화 
        elif count >= 5:
            count = 0  # 숫자 초기화
            win_count['com'] = 0
            win_count['user'] = 0
            play_cout_text.value = f"경기 횟수: {count}"
            wcount_text.value = f"com : 0 : user : 0"
            result_text.value = "5판 종료! 무승부 리셋"
            final_text.value = "다시 시작합니다!"

        page.update()

    # 리셋 함수
    def reset(e):
        global count
        nonlocal win_count
        count = 0
        win_count = {'user': 0, 'com': 0}
        play_cout_text.value = f"경기 횟수: {count}"
        wcount_text.value = "com : 0 : user : 0"
        final_text.value = ""
        result_text.value = "게임 시작"
        for btn in buttons:
            btn.disabled = False
        page.update()

    # 가위바위보 버튼
    buttons = [
        ft.ElevatedButton("가위",style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=1),
                                                    text_style=ft.TextStyle(size=20)), data="가위", on_click=play, bgcolor="yellow" ,color="green"),
        ft.ElevatedButton("바위", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=1),
                                                     text_style=ft.TextStyle(size=20)), data="바위", on_click=play, bgcolor="yellow", color="green"),
        ft.ElevatedButton("보", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=1),
                                                    text_style=ft.TextStyle(size=20)), data="보", on_click=play, bgcolor="yellow", color="green" ),
    ]

    # 배경 이미지 설정 
    # image_src 에러를 피하기 위해 Image 컨트롤을 직접 사용합니다.
    bg_image = ft.Image(
        src="spring.jpg",
        fit="cover",
        width=2000, # 배경이 잘리지 않게 넉넉히 설정
        height=2000
    )

    # 메인 UI 레이아웃
    main_ui = ft.Column([
        play_cout_text,
        ft.Row(buttons, alignment="center"), # 문자열 "center" 사용
        ft.Divider(),
        wcount_text,
        result_text,
        final_text,
        ft.ElevatedButton("리셋", on_click=reset, bgcolor="red", color="white")
    ], alignment="center", horizontal_alignment="center")

    # Stack으로 이미지 위에 UI 쌓기
    layout_stack = ft.Stack([
        bg_image,
        ft.Container(
            content=main_ui,
            expand=True,
            padding=50
        )
    ], expand=True)

    page.add(layout_stack)
     
# 앱 실행
ft.app(target=main)
