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

     # 1. 최신 방식인 ft.Button 사용 (ElevatedButton 대신)
     #     m_btn = [
     #         ft.Button("매장 페이지", data="매장", width=200, height=50),
     #         ft.Button("관리 페이지", data="관리", width=200, height=50),
     #         ft.Button("할인 페이지", data="할인", width=200, height=50),
     #         ft.Button("종료", data="종료", width=200, height=50, color="red"),
     #     ]
# def main(page: ft.Page):  
#      page.title = "마켓 프로그램"
#      # 화면 중앙 정렬 설정
#      page.vertical_alignment = "center"
#      page.horizontal_alignment = "center"

#      def exit_app(e):
#           page.window.close() # 창 닫기
#           sys.exit()
     
#      def manager_page(e): #관리자페이지
#           page.clean()
#           page.add(ft.Text("관리자 페이지",size = 30),
#                    ft.Button("매출확인",data="매출",width=200, height=50,style=btn_style , ),
#                    ft.Button("재고확인",data="재고",width=200, height=50,style=btn_style , ),
#                    ft.Button("가격확인",data="가격",width=200, height=50,style=btn_style , ),
#                    ft.Button("돌아가기",data="메인", width=200, height=50,style=btn_style , on_click=main_page))
          
#      def store_page(e): #관리자페이지
#           page.clean()
#           page.add(ft.Text("매장",size = 30),
#                    ft.Column([
#                    ft.Row(
#                    ft.Button("구매",data="재고",width=200, height=50,style=btn_style , ),
#                    ft.Button("선택취소",data="가격",width=200, height=50,style=btn_style , ))]),
#                    ft.Button("돌아가기",data="메인", width=200, height=50,style=btn_style , on_click=main_page))

#      main_title_text = ft.Text(f"정마트관장보기",color = "purple",size = 30)
#      btn_style=ft.ButtonStyle(bgcolor="#C8BFE7",color="black",
#                               shape=ft.RoundedRectangleBorder(radius=5))
     
#      m_btn = [
#     ft.Button("구매 페이지", data="매장", width=200, height=50,style=btn_style ,on_click = store_page),
#     ft.Button("관리 페이지", data="관리", width=200, height=50,style=btn_style ,on_click = manager_page),
#     ft.Button("할인 페이지", data="할인", width=200, height=50,style=btn_style),
#     # 종료 버튼만  개별 설정
#     ft.Button("종료", data="종료", width=200, height=50, bgcolor="red", color="white", on_click = exit_app )
# ]
#      def main_page(e=None):
#           page.clean()
#           # 2. 버튼들구현할 위치 잡기
#           main_ui = ft.Column([main_title_text,
#                ft.Row(m_btn, alignment="center"),
#                ft.Divider(),
#           ], alignment="center", horizontal_alignment="center")

#           # Stack으로 이미지 위에 UI 쌓기
#           layout_stack = ft.Stack([
#                ft.Container(
#                     content=main_ui,
#                     expand=True,
#                     padding=50
#                )
#           ], expand=True)

#           page.add(layout_stack)
#           page.update()

#      main_page()


# ft.app(target=main)


def main(page: ft.Page):
    page.title = "정마트 관장보기"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    
    # 공통 버튼 스타일
    btn_style = ft.ButtonStyle(
        bgcolor="#C8BFE7", color="black",
        shape=ft.RoundedRectangleBorder(radius=5)
    )
    

    # --- [공통 기능: 종료] ---
    def exit_app(e):
        page.window.close()
        sys.exit()

    # --- [보안 기능: F12를 눌러야 돌아가기 활성화] ---
    def on_keyboard(e):
        if e.key == "F12":
            # 매장 페이지에 있는 back_btn을 찾아서 토글
            try:
                back_btn.disabled = not back_btn.disabled
                page.update()
            except NameError:
                pass

    page.on_keyboard_event = on_keyboard

    # --- [페이지 1: 관리자 페이지] ---
    def manager_page(e):
        page.clean()
        page.add(
            ft.Column([
                ft.Text("관리자 페이지", size=30, weight="bold"),
                ft.Button("매출확인", width=200, height=50, style=btn_style),
                ft.Button("재고확인", width=200, height=50, style=btn_style),
                ft.Button("가격확인", width=200, height=50, style=btn_style),
                ft.Button("돌아가기", width=200, height=50, style=btn_style, on_click=main_page)
            ], horizontal_alignment="center", alignment="center")
        )
        page.update()

    # --- [페이지 2: 매장 페이지 (스케치 반영)] ---
    def store_page(e):
        page.clean()
        global back_btn # 키보드 이벤트에서 제어하기 위해 전역 선언
        
        # 상품 선택 시 입력창에 이름 넣어주는 함수
        def select_item(e):
            product_input.value = e.control.data
            page.update()

        # 왼쪽 리스트 영역
        product_list = ft.ListView(
            expand=True,
            controls=[
                ft.ListTile(title=ft.Text("상품 A"), data="상품 A", on_click=select_item),
                ft.ListTile(title=ft.Text("상품 B"), data="상품 B", on_click=select_item),
                ft.ListTile(title=ft.Text("상품 C"), data="상품 C", on_click=select_item),
            ]
        )

        product_input = ft.TextField(label="상품명", width=300)
        count_input = ft.TextField(label="개수", width=150, value="1")
        back_btn = ft.Button("메인", width=100, height=30,color="blue", bgcolor="yellow", disabled=True, on_click=main_page)

        # 전체 레이아웃 (Row 안에 3단 구성)
        page.add(
            ft.Row([ # 1단: 리스트
                ft.Container(content=product_list, border=ft.border.all(1), width=200, height=500),
                
                # 2단: 입력창 및 장바구니 영역
                ft.Column([
                    product_input,
                    count_input,
                    ft.Container(ft.Text("장바구니 목록 (표)"), border=ft.border.all(1), width=400, height=300)
                ], alignment="center"),
                
                # 3단: 버튼들
                ft.Column([
                    ft.Button("추가", width=200, height=60, bgcolor="blue", color="white"),
                    ft.Button("선택취소", width=200, height=50, style=btn_style),
                    ft.Button("구매",width = 250, height = 70 , bgcolor="white",color="green"),
                    ft.Divider(height=50),
                    ft.Text("관리자 전용", size=10, color="blue" ,bgcolor= "red"),
                    back_btn
                ], alignment="end", height=500)
            ], alignment="center", spacing=30)
        )
        
        page.update()

    def manager_page(e): # 관리자 페이지
        page.clean()
        global back_btn

        product_input = ft.TextField(label="상품명", width=300)
        # back_btn = ft.Button("메인", width=100, height=30,color="blue", bgcolor="yellow", disabled=False, on_click=main_page)

        def select_item(e):
            product_input.value = e.control.data
            page.update()

        # 왼쪽 리스트 영역
        product_list = ft.ListView(
            expand=True,
            controls=[
                ft.ListTile(title=ft.Text("상품 A"), data="상품 A", on_click=select_item),
                ft.ListTile(title=ft.Text("상품 B"), data="상품 B", on_click=select_item),
                ft.ListTile(title=ft.Text("상품 C"), data="상품 C", on_click=select_item),
            ]
        )
        item_text =ft.TextField(label="상품명",width = 300)
        cost_text =ft.TextField(label="원가",value="10000",suffix="원",width = 300,input_filter=ft.NumbersOnlyInputFilter(),read_only=True)
        inven_text= ft.TextField(label="재고",value="100",suffix="개",width = 300,input_filter=ft.NumbersOnlyInputFilter())
        currentcost_text =ft.TextField(label="현재가격",value="8000",suffix="원",width = 300,input_filter=ft.NumbersOnlyInputFilter()) 
        discount_text=  ft.TextField(label="할인율",value=f"{(1 - (float(currentcost_text.value)/float(cost_text.value)))* 100 :.1f}",suffix="%" ,width = 300,input_filter=ft.NumbersOnlyInputFilter())

        def change_price(e=None):
            try:
                # 1. 입력창에서 값 가져오기 (숫자로 변환)
                # 만약 빈칸이면 0으로 처리하도록 예외처리 합니다.
                original_cost = float(cost_text.value) if cost_text.value else 0
                current_price = float(currentcost_text.value) if currentcost_text.value else 0

                if original_cost > 0:
                    # 2. 할인율 계산 공식 적용
                    # (1 - 현재가/원가) * 100
                    discount_rate = (1 - (current_price / original_cost)) * 100
                    
                    # 3. 결과값 입력창에 업데이트 (소수점 첫째자리까지 표시)
                    discount_text.value = f"{discount_rate:.1f}"
                else:
                    discount_text.value = "0"

                # 4. 성공 메시지 (선택 사항)
                page.snack_bar = ft.SnackBar(ft.Text("가격 및 할인율이 갱신되었습니다."))
                page.snack_bar.open = True
                
            except ValueError:
                # 숫자가 아닌 값이 들어왔을 경우 에러 처리
                page.snack_bar = ft.SnackBar(ft.Text("숫자만 입력해주세요!"))
                page.snack_bar.open = True
            
            page.update()

        def discount_price(e) :
            #원하는 할인율 0%~ 최대 50% 까지만 적용하게
            try :
                
                discount_per = float(discount_text.value) if discount_text.value else 0
                original_cost = float(cost_text.value) if cost_text.value else 0

                if discount_per > 50:
                    discount_per = 50
                    discount_text.value = "50"

                if discount_per > 0:
            # 2. 계산 (입력창.value가 아니라 변환한 숫자 변수를 써야 합니다)
                    discount_rate = discount_per * 0.01
                    
                    # 현재가격 = 원가 - (원가 * 할인율)
                    calc_current_price = original_cost * (1 - discount_rate)
                    
                    # 3. 결과값 업데이트
                    currentcost_text.value = f"{int(calc_current_price)}" # 소수점 없이 정수로 표시
                    discount_text.value = f"{discount_per:.1f}"
                else:
                    currentcost_text.value = str(int(original_cost))
                    discount_text.value = "0"

                page.snack_bar = ft.SnackBar(ft.Text("할인율이 적용되었습니다. (최대 50%)"))
                page.snack_bar.open = True

            except Exception as ex:
                # 에러 발생 시 터미널에 이유 출력 (디버깅용)
                print(f"Error: {ex}")
                page.snack_bar = ft.SnackBar(ft.Text("숫자만 입력해주세요!"))
                page.snack_bar.open = True
            
            page.update()


        page.add(
            ft.Row([
                ft.Container(content=product_list, border=ft.border.all(1),#왼쪽 리스트
                                       width=200, height=500),
                # 중간 상품정보
                ft.Column([item_text,
                           cost_text,
                           inven_text,
                           currentcost_text,
                           discount_text
                           ],alignment="center"),

                ft.Column([ft.Button("재고변경", width=200, height=50, style=btn_style),#버튼
                    ft.Button("가격변경", width=200, height=50, style=btn_style,on_click=change_price),
                    ft.Button("할인율 적용",width = 200, height = 50 , bgcolor="white",color="green",on_click=discount_price),
                    ft.Button("메인", width=100, height=30,color="blue", bgcolor="yellow", disabled=False, on_click=main_page)
                    ], alignment="end", height=500
                )
            ])
        )
        def change_price(e):
            try:
                # 1. 입력창에서 값 가져오기 (숫자로 변환)
                # 만약 빈칸이면 0으로 처리하도록 예외처리 합니다.
                original_cost = float(cost_text.value) if cost_text.value else 0
                current_price = float(currentcost_text.value) if currentcost_text.value else 0

                if original_cost > 0:
                    # 2. 할인율 계산 공식 적용
                    # (1 - 현재가/원가) * 100
                    discount_rate = (1 - (current_price / original_cost)) * 100
                    
                    # 3. 결과값 입력창에 업데이트 (소수점 첫째자리까지 표시)
                    discount_text.value = f"{discount_rate:.1f}"
                else:
                    discount_text.value = "0"

                # 4. 성공 메시지 (선택 사항)
                page.snack_bar = ft.SnackBar(ft.Text("가격 및 할인율이 갱신되었습니다."))
                page.snack_bar.open = True
                
            except ValueError:
                # 숫자가 아닌 값이 들어왔을 경우 에러 처리
                page.snack_bar = ft.SnackBar(ft.Text("숫자만 입력해주세요!"))
                page.snack_bar.open = True
            
            page.update()
        
        
    # --- [페이지 3: 메인 페이지] ---
    def main_page(e=None):
        page.clean()
        main_title_text = ft.Text("정마트 관장보기", color="purple", size=30, weight="bold")
        
        m_btn = [
            ft.Button("구매 페이지", width=200, height=50, style=btn_style, on_click=store_page),
            ft.Button("관리 페이지", width=200, height=50, style=btn_style, on_click=manager_page),
            ft.Button("할인 페이지", width=200, height=50, style=btn_style),
            ft.Button("종료", width=200, height=50, bgcolor="red", color="white", on_click=exit_app)
        ]

        main_ui = ft.Column([
            main_title_text,
            ft.Divider(),
            ft.Row(m_btn, alignment="center"),
            
        ], alignment="center", horizontal_alignment="center")

        page.add(
            ft.Container(content=main_ui, expand=True, padding=50)
        )
        page.update()

    # 시작 시 메인 페이지 호출
    main_page()

ft.app(target=main)

