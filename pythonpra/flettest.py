
import flet as ft
# def main(page: ft.Page):
#     # 1. 닫기 함수 (취소/확인 공통)
#     def close_dlg(e):
#         # 최신 방식: page.close()를 사용하면 현재 열린 다이얼로그를 닫습니다.
#         page.close(dlg)

#     # 2. 다이얼로그 정의
#     dlg = ft.AlertDialog(
#         modal=True,
#         title=ft.Text("팝업창"),
#         content=ft.Text("정말로 진행하시겠습니까?"), # 내용이 없으면 허전하므로 추가
#         actions=[
#             ft.TextButton("cancel", on_click=close_dlg),
#             ft.TextButton("confirm", on_click=close_dlg)
#         ],
#         actions_alignment=ft.MainAxisAlignment.END,
#     )

#     # 3. 열기 함수
#     def opendlg(e):
#         # 최신 방식: page.open()을 사용하세요.
#         page.open(dlg)
    
#     # 4. 화면 구성
#     page.add(ft.TextButton("창 실행", on_click=opendlg))

# ft.app(target=main)

# def main(page: ft.Page):
#     # page.title = "Flet Hello App"
#     # page.add(ft.Text(value="안녕하세요, Flet!"))
#     def cancel_dlg(e):
#         e.page.dialog.open =False
#         e.page.update()
#         pass

#     def confirm_dlg(e):
#         e.page.dialog.open = False
#         e.page.update()
#         pass

#     dlg =ft.AlertDialog(
#         modal=True,
#         title= ft.Text("팝업창"),
#         actions=[
#             ft.TextButton("cancel",on_click=cancel_dlg),
#             ft.TextButton("confirm",on_click=confirm_dlg)
#         ],
#         actions_alignment=ft.MainAxisAlignment.END,
#         actions_padding = 0,
#         content_padding = 0
#     )

#     def opendlg(e):
#         page.dialog=dlg
#         page.dialog.open = True
#         page.update()
    
#     page.add(ft.TextButton("창 실행", on_click=opendlg))
#     page.update()

# ft.app(target=main)
def main(page: ft.Page):
    
  
    # 닫기 함수
    def close_dlg(e):
        dlg.open = False  # page.close(dlg) 대신 직접 속성 변경
        page.update()

    # 다이얼로그 정의
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("팝업창"),
        content=ft.Text("이 방식은 모든 버전에서 작동합니다."),
        actions=[
            ft.TextButton("cancel", on_click=close_dlg),
            ft.TextButton("confirm", on_click=close_dlg)
        ]
    )
    page.overlay.append(dlg) # 페이지 레이어에 추가
    # 열기 함수
    def opendlg(e):
        # page.open(dlg)가 안 될 때 쓰는 표준 방식
        
        dlg.open = True          # 열기 상태로 변경
        page.update()            # 반영
    txt_name = ft.TextField(
        label="이름을 입력하세요", 
        width=300,
        height=100,  # 높이를 100으로 충분히 줍니다. (에러 메시지 공간)
        border=ft.InputBorder.OUTLINE # 테두리를 명확히 해서 빨간색 변화를 확인합니다.
    )

    def btn_click(e):
        if not txt_name.value:
            # 1. 에러 문구 설정
            txt_name.error_text = "이름 입력은 필수입니다!"
            # 2. 즉시 화면 갱신
            page.update() 
        else:
            txt_name.error_text = None
            # page.clean()
            page.add(ft.Text(f"안녕하세요, {txt_name.value}님!"))

    page.add(
        ft.Text("Flet 에러 테스트", size=25),
        txt_name,
        # 버튼과 입력창 사이에 간격을 줍니다.
        ft.Container(height=10), 
        ft.ElevatedButton("확인", on_click=btn_click, width=300)
    )
    
    # page.add(t,txt_name,ft.ElevatedButton("Say hello!", on_click=btn_click),ft.TextButton("창 실행", on_click=opendlg))

ft.app(target=main)

