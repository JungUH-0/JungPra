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
        ],
    )
    page.overlay.append(dlg) # 페이지 레이어에 추가
    # 열기 함수
    def opendlg(e):
        # page.open(dlg)가 안 될 때 쓰는 표준 방식
        
        dlg.open = True          # 열기 상태로 변경
        page.update()            # 반영
    
    page.add(ft.TextButton("창 실행", on_click=opendlg))

ft.app(target=main)

