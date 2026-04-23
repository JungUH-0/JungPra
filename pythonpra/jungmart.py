import flet as ft
import random
import sys
import datetime
import os

# --- [데이터 준비 영역] ---
물품명 = [
    "비누", "치약", "샴푸", "린스", "바디워시", "폼클렌징", "칫솔", "수건",
    "휴지", "물티슈", "세탁세제", "섬유유연제", "주방세제", "수세미", "고무장갑",
    "쌀", "라면", "햇반", "생수", "우유", "계란", "두부", "콩나물", "시금치",
    "양파", "감자", "고구마", "사과", "바나나", "오렌지", "귤", "토마토",
    "김치", "된장", "고추장", "간장", "식용유", "참기름", "소금", "설탕",
    "커피", "차", "과자", "빵", "젤리", "초콜릿", "음료수", "맥주", "소주",
    "고기(돼지고기)", "고기(소고기)", "닭고기", "생선", "오징어", "새우", "게",
    "쌀국수", "파스타", "잼", "버터", "치즈", "요거트", "아이스크림", "통조림",
    "냉동만두", "어묵", "햄", "소시지", "김", "미역", "다시마", "멸치",
    "밀가루", "부침가루", "튀김가루", "빵가루", "식초", "소스", "향신료",
    "양초", "성냥", "건전지", "전구", "쓰레기봉투", "지퍼백", "호일", "랩"
]


def market_dic_init(item_list):
    temp_dic = {}
    x = 0
    while x < len(item_list):
        id = random.randint(1, 1000) # ID 범위를 조금 늘림
        if id in temp_dic: continue
        price = random.randint(10, 100) * 100
        stock = random.randint(1, 50)
        temp_dic[id] = {
            "품명": item_list[x], 
            "재고": stock, 
            "원가": price, 
            "현재가격": price, 
            "할인율": 0
        }
        x += 1
    return temp_dic

# 전역 데이터 변수
market_data = market_dic_init(물품명)
sales_file="sales_data.txt"
sales_history = []
def loaddata():
    history = []
    if os.path.exists(sales_file):
        with open(sales_file, "r", encoding="utf-8") as f:
            for line in f:
                data = line.strip().split(",")
                if len(data) == 4:
                    # 핵심: 문자열 "2026-04-21"을 datetime.date 객체로 변환
                    # data[0] -> "2026-04-21"
                    date_obj = datetime.datetime.strptime(data[0], "%Y-%m-%d").date()
                    
                    history.append({
                        "date": date_obj, # 이제 datetime.date 객체가 담깁니다.
                        "item": data[1], 
                        "qty": int(data[2]), 
                        "total_price": int(data[3])
                    })
    return history

def savefile(item_name, qty, price):
    today = datetime.date.today().isoformat()
    with open(sales_file, "a", encoding="utf-8") as f:
        # 파일 끝에 한 줄씩 추가 (append 모드)
        f.write(f"{today},{item_name},{qty},{price}\n")

sales_history=loaddata()

def find_key_by_name(name):
    for k, v in market_data.items():
        if v["품명"] == name:
            return k
    return None
def surprise_discount():
    # 1. 전체 상품 중 최대 5개를 랜덤하게 선택
    all_keys = list(market_data.keys())
    sample_size = min(len(all_keys), 5)
    discount_targets = random.sample(all_keys, sample_size)
    
    for key in discount_targets:
        # 10% ~ 40% 사이의 할인율 랜덤 생성
        surprise_rate = random.randrange(10, 41, 10)
        
        
        if surprise_rate > market_data[key]["할인율"]:
            market_data[key]["할인율"] = surprise_rate
            orig = market_data[key]["원가"]
            # 현재가격을 할인율에 맞춰 즉시 갱신
            market_data[key]["현재가격"] = int(orig * (1 - surprise_rate * 0.01))

# 프로그램 시작 시점에 호출
surprise_discount()

# --- [메인 애플리케이션] ---
def main(page: ft.Page):
     page.title = "정마트 장보기 시스템"
     page.window.width = 1000
     page.window.height = 700
     page.theme_mode = ft.ThemeMode.LIGHT

     # 공통 버튼 스타일
     btn_style = ft.ButtonStyle(
          bgcolor="#C8BFE7", color="black",
          shape=ft.RoundedRectangleBorder(radius=5)
     )

     def exit_app(e):
        page.window.close()
        sys.exit()

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
     def manager_page(e=None):
        page.clean()

        # 입력 필드들
        item_text = ft.TextField(label="상품명", width=300)
        cost_text = ft.TextField(label="원가", suffix="원", width=300, read_only=True)
        inven_text = ft.TextField(label="재고", suffix="개", width=300)
        currentcost_text = ft.TextField(label="현재가격", suffix="원", width=300)
        discount_text = ft.TextField(label="할인율", suffix="%", width=300)

        # 알림창 관련 로직 
        def update_stock_confirmed(e):
            f_key = find_key_by_name(item_text.value)
            if f_key:
                try:
                    market_data[f_key]["재고"] = int(inven_text.value)
                    confirm_dialog.open = False  # 창 닫기
                    page.snack_bar = ft.SnackBar(ft.Text(f"'{item_text.value}' 재고가 수정되었습니다."))
                    page.snack_bar.open = True
                    page.update()
                except ValueError:
                    confirm_dialog.open = False
                    page.snack_bar = ft.SnackBar(ft.Text("숫자만 입력해주세요."), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()

        def close_dialog(e):
            f_key = find_key_by_name(item_text.value)
            if f_key:
                inven_text.value = str(market_data[f_key]["재고"])
            confirm_dialog.open = False
            page.update()

        # 알림창 정의
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("재고 수정 확인"),
            content=ft.Text("재고를 수정하시겠습니까?"),
            actions=[
                ft.TextButton("예", on_click=update_stock_confirmed),
                ft.TextButton("아니오", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        
        page.overlay.append(confirm_dialog)

        
        def on_select_item(e):
            f_key = find_key_by_name(e.control.data)
            if f_key:
                item = market_data[f_key]
                item_text.value = item["품명"]
                cost_text.value = str(item["원가"])
                inven_text.value = str(item["재고"])
                currentcost_text.value = str(item["현재가격"])
                discount_text.value = str(item["할인율"])
                page.update()

        def change_price_logic(e):
            f_key = find_key_by_name(item_text.value)
            if not f_key: return
            orig = float(cost_text.value)
            curr = float(currentcost_text.value)
            if orig > 0:
                rate = (1 - (curr / orig)) * 100
                discount_text.value = f"{rate:.1f}"
                market_data[f_key]["현재가격"] = int(curr)
                market_data[f_key]["할인율"] = round(rate, 1)
                page.snack_bar = ft.SnackBar(ft.Text("가격 및 할인율이 갱신되었습니다."))
                page.snack_bar.open = True
            page.update()

        def apply_discount_logic(e):
            f_key = find_key_by_name(item_text.value)
            if not f_key: return
            rate_val = float(discount_text.value) if discount_text.value else 0
            if rate_val > 50: 
                rate_val = 50
                discount_text.value = "50"
            orig = float(cost_text.value)
            new_price = orig * (1 - (rate_val * 0.01))
            currentcost_text.value = str(int(new_price))
            market_data[f_key]["현재가격"] = int(new_price)
            market_data[f_key]["할인율"] = rate_val
            page.snack_bar = ft.SnackBar(ft.Text(f"할인율 {rate_val}%가 적용되었습니다."))
            # print( market_data[f_key]["할인율"])
            page.snack_bar.open = True
            page.update()

        # 재고수정 버튼 누르면 알림창만 띄움
        def update_stock(e):
            if item_text.value:
                confirm_dialog.open = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("상품을 선택해주세요."))
                page.snack_bar.open = True
                page.update()

        product_list = ft.ListView(
            expand=True,
            controls=[ft.ListTile(title=ft.Text(v["품명"]), data=v["품명"], on_click=on_select_item) for v in market_data.values()]
        )

        def sales_report(e):
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday()) # 이번 주 월요일
            
            daily_total = 0
            weekly_total = 0
            
            for record in sales_history:
                record_date = record["date"]
                # 당일 매출
                if record_date == today:
                    daily_total += record["total_price"]
                # 이번 주 매출 (월요일 ~ 오늘)
                if start_of_week <= record_date <= today:
                    weekly_total += record["total_price"]
            
            # 매출 현황 알림창
            sales_dialog = ft.AlertDialog(
                title=ft.Text("매출 현황 보고"),
                content=ft.Text(
                    f"기준 날짜: {today}\n\n"
                    f"당일 매출: {daily_total:,}원\n"
                    f"이번 주 총 매출: {weekly_total:,}원"
                ),
                actions=[ft.TextButton("닫기", on_click=lambda _: setattr(sales_dialog, "open", False) or page.update())]
            )
            page.overlay.append(sales_dialog)
            sales_dialog.open = True
            page.update()

        # [4] 레이아웃 구성
        page.add(
            ft.Row([
                ft.Container(content=product_list, border=ft.border.all(1), width=250, height=550),
                ft.Column([item_text, cost_text, inven_text, currentcost_text, discount_text], alignment="center"),
                ft.Column([
                    ft.Button("재고수정", width=200, height=50, style=btn_style, on_click=update_stock),
                    ft.Button("가격변경", width=200, height=50, style=btn_style, on_click=change_price_logic),
                    ft.Button("할인율 적용", width=200, height=50, bgcolor="white", color="green", on_click=apply_discount_logic),
                    ft.Button("매출현황 확인", width=200, height=50, bgcolor="orange", color="black", on_click=sales_report),
                    ft.Button("메인으로", width=200, height=50, bgcolor="yellow", on_click=main_page)
                ], alignment="center")
            ], alignment="center", spacing=30)
        )
    # --- [페이지 2: 구매 페이지] ---
     def store_page(e=None):
        page.clean()
        global back_btn
        
        # 1. 상태 관리 변수
        cart_data = [] # 장바구니 데이터 저장용 리스트

        # 2. UI 요소 선언 (초기에는 수량과 담기 버튼을 비활성화)
        back_btn = ft.Button("메인", width=100, height=30, color="blue", bgcolor="yellow", disabled=True, on_click=main_page)
        search_input = ft.TextField(label="상품명 입력", width=300)
        price_info = ft.Text("가격을 확인하려면 상품을 선택하세요", size=16)
        qty_input = ft.TextField(label="수량", width=100, value="1", disabled=True)
        add_cart_btn = ft.Button("장바구니 담기", bgcolor="blue", color="white", width=150, disabled=True)
        cart_list_view = ft.ListView(expand=True, spacing=5) # 장바구니 목록창
        total_price_text = ft.Text("총 결제 금액: 0원", size=20, weight="bold", color="red")
        items = [
            f"{v['품명']}({v['현재가격']}원)" 
            for v in market_data.values() if v["할인율"] > 0
        ]

        info = " 할인 상품: " + (", ".join(items) if items else "없음")

        surprise_banner = ft.Container(
        content=ft.Text(info, color="white", weight="bold"),
        bgcolor="red" if items else "bluegrey",
        padding=10, 
        border_radius=5, 
        expand=True
        )

        # 3. 검색 로직 (활성화의 핵심)
        def on_search(e):
            name = search_input.value.strip()
            f_key = find_key_by_name(name)
            
            if f_key:
                item = market_data[f_key]
                # 검색 성공 시 수량 입력과 장바구니 버튼 활성화
                qty_input.disabled = False
                add_cart_btn.disabled = False
                price_info.value = f"상품: {item['품명']} | 가격: {item['현재가격']:,}원 )"
            else:
                # 검색 실패 시 다시 잠금
                qty_input.disabled = True
                add_cart_btn.disabled = True
                price_info.value = "없는 상품입니다."
                page.snack_bar = ft.SnackBar(ft.Text(f"'{name}' 상품을 찾을 수 없습니다."), bgcolor="red")
                page.snack_bar.open = True
            
            page.update() # 화면 갱신 필수

        # 4. 장바구니 담기 로직
        def add_to_cart(e):
            f_key = find_key_by_name(search_input.value)
            if not f_key: return

            item = market_data[f_key]
            try:
                buy_qty = int(qty_input.value)
                if buy_qty <= 0: raise ValueError
                
                # 1. 이미 장바구니에 있는지 확인
                existing_item = None
                for c in cart_data:
                    if c["품명"] == item["품명"]:
                        existing_item = c
                        break
                
                # 2. 재고 확인 
                current_in_cart = existing_item["수량"] if existing_item else 0
                if current_in_cart + buy_qty > item["재고"]:
                    page.snack_bar = ft.SnackBar(ft.Text(f"재고 부족! (이미 {current_in_cart}개 담겨있음 / 최대 {item['재고']}개)"), bgcolor="red")
                else:
                    if existing_item:
                        
                        existing_item["수량"] += buy_qty
                        existing_item["총합"] = existing_item["수량"] * item["현재가격"]
                        
                        
                        for control in cart_list_view.controls:
                            if control.title.value.startswith(item["품명"]):
                                control.title.value = f"{item['품명']} x {existing_item['수량']}개"
                                control.subtitle.value = f"금액: {existing_item['총합']:,}원"
                                break
                    else:
                        # 새로 담는 경우
                        total = item["현재가격"] * buy_qty
                        cart_data.append({"품명": item["품명"], "수량": buy_qty, "총합": total})
                        
                        cart_list_view.controls.append(
                            ft.ListTile(
                                title=ft.Text(f"{item['품명']} x {buy_qty}개"),
                                subtitle=ft.Text(f"금액: {total:,}원"),
                                # 아이콘 대신 사용자님 스타일의 텍스트 버튼 사용
                                trailing=ft.TextButton("삭제", on_click=lambda _: remove_from_cart(item['품명']))
                            )
                        )
                    
                    # 공통 업데이트
                    current_total = sum(c["총합"] for c in cart_data)
                    total_price_text.value = f"총 결제 금액: {current_total:,}원"
                    page.snack_bar = ft.SnackBar(ft.Text(f"'{item['품명']}' 수량이 업데이트되었습니다."))
                
                page.snack_bar.open = True
                page.update()
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("수량에 숫자를 입력해주세요."), bgcolor="orange")
                page.snack_bar.open = True
                page.update()

        # 5. 장바구니 개별 삭제
        def remove_from_cart(name):
            for i, c in enumerate(cart_data):
                if c["품명"] == name:
                    cart_data.pop(i)
                    cart_list_view.controls.pop(i)
                    break
            current_total = sum(c["총합"] for c in cart_data)
            total_price_text.value = f"총 결제 금액: {current_total:,}원"
            page.update()

        # 6. 리스트 클릭 시 자동 검색
        def select_to_search(e):
            search_input.value = e.control.data
            on_search(None) # 검색 함수 강제 호출하여 버튼 활성화

        # 7. 왼쪽 상품 리스트 생성
        product_list = ft.ListView(
            expand=True,
            controls=[ft.ListTile(title=ft.Text(v["품명"]), data=v["품명"], on_click=select_to_search) for v in market_data.values()]
        )

        # 8. 버튼 함수 연결
        add_cart_btn.on_click = add_to_cart
        def handle_payment(e):
            if not cart_data:
                page.snack_bar = ft.SnackBar(ft.Text("장바구니가 비어 있습니다."), bgcolor="orange")
                page.snack_bar.open = True
                page.update()
                return

            # 실제 결제 처리 (재고 반영 및 매출 기록)
            for cart_item in cart_data:
                f_key = find_key_by_name(cart_item["품명"])
                if f_key:
                    # 1. DB(market_data) 재고 차감
                    market_data[f_key]["재고"] -= cart_item["수량"]
                    
                    # 2. 매출 기록 등록
                    import datetime
                    sales_history.append({
                        "date": datetime.date.today(),
                        "item": cart_item["품명"],
                        "total_price": cart_item["총합"]
                    })

            # 3. 장바구니 초기화
            cart_data.clear()
            cart_list_view.controls.clear()
            total_price_text.value = "총 결제 금액: 0원"
            
            # 4. 결제 완료 알림
            payment_dialog = ft.AlertDialog(
                title=ft.Text("결제 완료"),
                content=ft.Text("정상적으로 결제되었습니다.\n이용해 주셔서 감사합니다!"),
                actions=[ft.TextButton("확인", on_click=lambda _: setattr(payment_dialog, "open", False) or page.update())]
            )
            page.overlay.append(payment_dialog)
            payment_dialog.open = True
            
            # 검색 정보 초기화 
            on_search(None) 
            page.update()

        # 11. 버튼 생성 및 연결 수정
        pay_btn = ft.Button("결제하기", bgcolor="green", color="white", width=150, on_click=handle_payment)

        # 9. 레이아웃 구성
        page.add(
            surprise_banner,#할인품목
            ft.Row([
                # 왼쪽: 전체 상품 리스트
                ft.Container(content=product_list, border=ft.border.all(1), width=250, height=550),
                
                # 오른쪽: 검색 및 장바구니 영역
                ft.Column([
                    ft.Text("구매 검색 및 장바구니", size=24, weight="bold"),
                    ft.Row([search_input, ft.Button("검색", on_click=on_search, style=btn_style)]),
                    price_info,
                    ft.Row([qty_input, add_cart_btn]),
                    ft.Divider(),
                    ft.Text("장바구니 목록", size=18, weight="bold"),
                    ft.Container(
                        content=cart_list_view, 
                        border=ft.border.all(1), 
                        width=450, 
                        height=200, 
                        border_radius=10
                    ),
                    total_price_text,
                    
                    ft.Row([
                        pay_btn,
                        back_btn # F12로 활성화되는 버튼
                    ])
                ], alignment="center", spacing=15)
            ], alignment="center")
        )
    # --- [페이지 3: 메인 페이지] ---
     def main_page(e=None):
        page.clean()
        page.add(
            ft.Column([
                ft.Text("정마트 시스템", size=40, weight="bold", color="purple"),
                ft.Divider(),
                ft.Row([
                    ft.Button("구매 페이지", width=200, height=60, style=btn_style, on_click=store_page),
                    ft.Button("관리 페이지", width=200, height=60, style=btn_style, on_click=manager_page),
                ], alignment="center"),
                ft.Button("종료", width=200, height=50, bgcolor="red", color="white", on_click=exit_app)
            ], horizontal_alignment="center", alignment="center", spacing=30)
        )

     main_page()

ft.app(target=main)