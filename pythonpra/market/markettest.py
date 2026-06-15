import flet as ft
import random
import os

def clear_screen():
    
    os.system('cls' if os.name == 'nt' else 'clear')

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

market={}
x=0; #while 나오기위한 임의 수
dis_item = 0; #이번 할인 품목개수
while x<len(물품명) :
    item = random.randint(1,50)
    id= random.randint(1,100)
    #중복검사
    if id in market:
        continue
    price = random.randint(10,100)*100
    market[id]={"품명":물품명[x],"재고":item,"가격":price,"판매현황":0}
    x+=1

discount=0
total_cash=0

#관리자 페이지 / 매장 계산 페이지 따로 보여주기
#{"품명":물품명,"재고":item,"가격":price}
while True :

    print("메인 화면")
    print("1. 관리자 페이지")
    print("2. 매장 페이지")
    print("3. 할인 적용")
    print("4. 종료")
    print(f"할인이 적용 된 수 : {discount}")
    sel_num = int(input("#원하는 페이지 이동 번호 입력 : "))
    if sel_num == 1 :
        #관리자 페이지 출력
        clear_screen()

        while True:
            print("1. 매출 확인")
            print("2. 품목 확인")
            print("3. 이전 화면")
            menu_move = int(input("#번호 입력 : "))

            if menu_move ==1 :
                clear_screen()
                # 매출확인 페이지

                print(f"총 판매 금액 {total_cash :,}원 입니다")
                input("\n계속하려면 엔터를 누르세요...")

            elif menu_move ==2:
                #품명 입력시 재고/가격 확인/수정
                clear_screen()

                print("q 입력시 이전 화면")
                find_name = input("#찾을 품목 입력 :")
                find_key = None
                for k1, v1 in market.items():
                        if isinstance(v1, dict):
                            for k2, v2 in v1.items():
                                if v2 == find_name :
                                    # print(f"key {k1} ")
                                    find_key = k1
                                    # print(type(find_key))
                                    break

                if find_name =='q' :
                    clear_screen()
                    break

                if find_key != None :
                    clear_screen()
                    print("찾은 물품 :",market[find_key]["품명"])
                    while True :
                        print("1. 재고 확인 및 변경")
                        print("2. 가격 확인 및 변경")
                        print("3. 이전 화면")
                        menu_move = int(input("#번호 입력 : "))

                        #재고페이지
                        if menu_move ==1 :
                            clear_screen()
                            print(f"{market[find_key]["품명"]} 의 재고는 \
                            {market[find_key]["재고"]} 개")
                            print("1. 재고 변경")
                            print("2. 이전 화면")
                            while True :
                                menu_move = int(input("#번호 입력 : "))
                                if menu_move ==1:
                                    ch_item = int(input("재고 변경 :"))
                                    market[find_key]["재고"]= ch_item
                                    # print(f"{market[find_key]["품명"]} 의 재고는 {market[find_key]["재고"]}")
                                    break
                                elif menu_move ==2 :
                                    break
                                else :
                                    print("번호 확인")

                        # 가격 페이지
                        elif menu_move ==2:
                            clear_screen()
                            print(f"{market[find_key]["품명"]} 의 가격은 \
                            {market[find_key]["가격"]:,} 원")
                            print("1. 가격 변경")
                            print("2. 이전 화면")
                            while True :
                                menu_move = int(input("#번호 입력 : "))
                                if menu_move ==1:
                                    ch_item = int(input("가격 변경 :"))
                                    market[find_key]["가격"]= ch_item
                                    # print(f"{market[find_key]["품명"]} 의 재고는 {market[find_key]["가격"]}")
                                    break
                                elif menu_move ==2 :
                                    break
                                else :
                                    print("번호 확인")

                        elif menu_move ==3 :
                            clear_screen()
                            break
                        else :
                            print("입력번호 확인")

                else :
                        print("품명 확인필요")

            elif menu_move ==3:
                clear_screen()
                break
            else :
                print("번호 확인")

    elif sel_num ==2 :
        clear_screen()

        ##################################################
        cart = 0
        total = 0
        buy_dic ={}
        while True:
            print(f"현재 구매한 품목수 {cart}")
            print(f"선택한 품목들의 가격 {total :,} 원")
            if len(buy_dic) != 0 :
                for i in buy_dic:
                    
                    # print(i)
                    print(f"물품명 : {buy_dic[i]["품명"]}\t 구매 개수 : \
                    {buy_dic[i]["개수"]}개 \t 개당 가격 : {buy_dic[i]["개당가격"]:,}원 \t \
                    합계 : {buy_dic[i]["총가격"]:,}원 ")

            print("q 입력시 이전 화면")
            sel_name = input("#구매할 품목 : ")
            

            if sel_name =='q':
                break
            find_key = None;
            for k1, v1 in market.items():
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if v2 == sel_name :
                            find_key = k1
                            break

            if find_key != None :
                print("구매하실 물품 :",market[find_key]["품명"])
                buy_item = int(input("#원하시는 개수를  선택 해주세요 : "))
                if buy_item > market[find_key]["재고"] :
                    print("재고 부족")
                else :
                    market[find_key]["재고"] -= buy_item
                    market[find_key]["판매현황"] += buy_item
                    cart+=1
                    total = total+ (market[find_key]["가격"]*buy_item)
                    clear_screen()
                    print(f"물품명 : {market[find_key]["품명"]}\n구매개수 : \
                    {buy_item} 개 \n가격 : {market[find_key]["가격"]*buy_item:,} 원 ")

                    buy_dic[cart] = {"품명":sel_name,"개수":buy_item,
                                     "개당가격":market[find_key]["가격"],
                                     "총가격":market[find_key]["가격"]*buy_item}
                    input("\n계속하려면 엔터를 누르세요...")
                    # print(buy_dic)
            else :
                print("없는 품목입니다. 죄송합니다")


    elif sel_num ==3 :
        clear_screen()

        # 할인 적용 페이지
        for i in range(5):
            dis_item = random.randint(1,100)
            if dis_item in market :
                print(f"{market[dis_item]["품명"]}의 할인 전 가격은 {market[dis_item]["가격"]:,} 원 입니다. ")
                discount_ran = random.randint(1,4)*10
                market[dis_item]["가격"]= market[dis_item]["가격"] - int((market[dis_item]["가격"]*(discount_ran*0.01)))
                print(f"{market[dis_item]["품명"]}의 할인 후 가격은 {market[dis_item]["가격"]:,} 원 입니다. ")
                discount +=1
            else :
                continue
        sel_num=0

    elif sel_num ==4 :
        print("종료합니다.")
        break
    else :
        print("번호 확인")
