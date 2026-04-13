import flet as ft
import random
import os
import sys

#메인 창 버튼 (매장)(관리)(할인){할인적용중인 상품 수}(종료)
#매장 버튼 클릭시 고객이 원하는 상품을 검색 후 개수 선택(직접입력 혹은 리스트)
#ㄴ 할인 상품 우선 보이게***
#ㄴ 상품은 상품명으로 검색하게 하고 오입력이나 재고의 문제시 고객센터 문의 요청 창
#상품 구매시 매출액(연/월/일), 상품의 재고 변동
#ㄴ 
#관리 페이지 (매출확인)(품목확인)
#ㄴ 매출확인 버튼 클릭시 (연간)(월간)(일간) 
#ㄴ 품목 확인은 매장페이지랑 비슷하게 상품명과 리스트 
#품목확인 페이지 (재고)(가격)(할인적용)
#ㄴ 재고페이지 {재고:수량} (재고 변동)
#ㄴ 가격페이지 {현재가격}/{원가} (가격 변동) 
#ㄴ 할인적용 퍼센트



#메인
def main(page: ft.Page):
     page.title = "마켓 프로그램"
     # 화면 중앙 정렬 설정
     page.vertical_alignment = "center"
     page.horizontal_alignment = "center"

     # 1. 최신 방식인 ft.Button 사용 (ElevatedButton 대신)
     #     m_btn = [
     #         ft.Button("매장 페이지", data="매장", width=200, height=50),
     #         ft.Button("관리 페이지", data="관리", width=200, height=50),
     #         ft.Button("할인 페이지", data="할인", width=200, height=50),
     #         ft.Button("종료", data="종료", width=200, height=50, color="red"),
     #     ]
     
     def exit_app(e):
          page.window_close() # 창 닫기
          sys.exit()

     btn_style=ft.ButtonStyle(bgcolor="#C8BFE7",color="black",
                              shape=ft.RoundedRectangleBorder(radius=5))
     
     m_btn = [
    ft.Button("구매 페이지", data="매장", width=200, height=50,style=btn_style),
    ft.Button("관리 페이지", data="관리", width=200, height=50,style=btn_style),
    ft.Button("할인 페이지", data="할인", width=200, height=50,style=btn_style),
    # 종료 버튼만  개별 설정
    ft.Button("종료", data="종료", width=200, height=50, bgcolor="red", color="white", on_click = exit_app )
]
     

     # 2. 버튼들구현할 위치 잡기
     main_ui = ft.Column([
          ft.Row(m_btn, alignment="center"), # 문자열 "center" 사용
          ft.Divider(),
     ], alignment="center", horizontal_alignment="center")

     # Stack으로 이미지 위에 UI 쌓기
     layout_stack = ft.Stack([
          ft.Container(
               content=main_ui,
               expand=True,
               padding=50
          )
     ], expand=True)

     page.add(layout_stack)

ft.app(target=main)