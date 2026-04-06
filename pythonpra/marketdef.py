# 함수로 모듈화 할때 while문의 위치는 어디가 좋은가?
# 함수 내부로 만들어서 또 다른 함수로 이어지게?
# while 중첩이 많을경우 함수에선 어떤 문제가 발생하는지?
# 이걸 flet에 적용 방법까지...
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

def find_key(market,find_item) : #물품명으로 키값 찾는 함수
     find_key = None;
     for k1, v1 in market.items():
          if isinstance(v1, dict):
               for k2, v2 in v1.items():
                    if v2 == find_item :
                         # print(f"key {k1} ")
                         find_key = k1
                         # print(type(find_key))
                         break
     return find_key

def market_dic(item_list) : #물품명 list를 랜덤 key 부여하고 dictionary 만들기
     temp_dic={}
     x=0; #while 나오기위한 임의 수
     
     while x<len(물품명) :
          item = random.randint(1,50)
          id= random.randint(1,100)
          #중복검사
          if id in temp_dic:
               continue
          price = random.randint(10,100)*100
          temp_dic[id]={"품명":물품명[x],"재고":int(item),"원가":int(price),"현재가격":int(price),"판매현황":int(0),"할인율":0}
          x+=1
     
     return temp_dic

def show_main(discount): #메인화면
     print("#"*3,"메인 화면","#"*3)
     print("1. 관리자 페이지")
     print("2. 매장 페이지")
     print("3. 할인 적용")
     print("4. 종료")
     print(f"할인이 적용 된 수 : {discount}")
     sel_num = int(input("#원하는 페이지 이동 번호 입력 : "))
     return sel_num

def show_admin_menu(market,total_cash) :# 관리자 페이지
     while True:
          clear_screen()
          print("#"*3,"관리자 페이지","#"*3)
          print("1. 매출 확인")
          print("2. 품목 확인")
          print("3. 이전 화면")
          menu_move = int(input("#번호 입력 : "))
          if menu_move == 1 :
              show_totalcash(total_cash)
          elif menu_move ==2:
               show_search_page(market)
               pass
          elif menu_move ==3:
               break
     return 0


def show_totalcash(total_cash) : #총 매출페이지
     clear_screen()
                
     print(f"총 판매 금액 {total_cash :,}원 입니다")
     input("\n계속하려면 엔터를 누르세요...")
     return 0

def show_search_page(market) : # 관리자페이지에서 물품찾는 페이지
     clear_screen()
     print("#"*8)
     print("q 입력시 이전 화면")
     find_name = input("#찾을 품목 입력 :")
     f_key = find_key(market,find_name)
     if find_name =='q' : # q입력시 종료
          clear_screen()
          return 0
     if f_key != None :     # 물품명이 정확할때 실행됨
          while True :
               clear_screen()
               print("#"*3,"물품","#"*3)
               print("찾은 물품 :",market[f_key]["품명"])
               print("1. 재고 확인 및 변경")
               print("2. 가격 확인 및 변경")
               print("3. 이전 화면")
               menu_move = int(input("#번호 입력 : "))
               if menu_move ==1 :
                    item_chk_page(market[f_key])
               elif menu_move ==2:
                    price_chk_page(market[f_key])
               elif menu_move ==3:
                    break
          return 0



def item_chk_page (item): #물품 재고 확인및 변경페이지
     while True :
          clear_screen()
          print("#"*8)
          print(f"찾은 {item["품명"]}의 재고는 {item["재고"]}개 입니다.")
          print("1. 재고 변경")
          print("2. 이전 화면")
          menu_move = int(input("#번호 입력 :"))
          if(menu_move==1):
               print("재고 변경")
               item["재고"]= chg_page(item["재고"])
          elif(menu_move == 2):
               print("enter 클릭시 이전 화면을 넘어갑니다.")
               input("\n계속하려면 엔터를 누르세요...")
               break
          else :
               print("번호 확인")
     return 0 
     
def chg_page (item) : # 변경 페이지 (재고/가격)
     chg_num = int(input("변경될 숫자를 입력해주세요 : "))
     item = chg_num
     return item

def price_chk_page(item): #  가격 확인/변경 페이지
     
     while True :
          clear_screen()
          print("#"*8)
          print(f"찾은 {item["품명"]}의 가격은 {item["현재가격"] :,}원 입니다.")
          print(f"찾은 {item["품명"]}의 원가는 {item["원가"] :,}원 입니다.")
          print("1. 가격 변경")
          print("2. 이전 화면")
          menu_move = int(input("#번호 입력 :"))
          if(menu_move==1):
               print("가격 변경")
               item["현재가격"]=chg_page(item["현재가격"])
          elif(menu_move == 2):
               print("enter 클릭시 이전 화면을 넘어갑니다.")
               input("\n계속하려면 엔터를 누르세요...")
               break
          else :
               print("번호 확인")
     return 0 

def buy_page (total_cash): # 손님의 구매 페이지
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
            f_key = find_key(market,sel_name)

            if sel_name =='q': #q 누르면 종료/종료시 총매출에 추가
                total_cash += total
                break
            
            if f_key != None :
                print("구매하실 물품 :",market[f_key]["품명"])
                buy_item = int(input("#원하시는 개수를  선택 해주세요 : "))
                if buy_item > market[f_key]["재고"] :
                    print("재고 부족")
                else :
                    market[f_key]["재고"] -= buy_item
                    market[f_key]["판매현황"] += buy_item
                    cart+=1
                    total = total+ (market[f_key]["현재가격"]*buy_item)
                    clear_screen()
                    print(f"물품명 : {market[f_key]["품명"]}\n구매개수 : \
                    {buy_item} 개 \n가격 : {market[f_key]["현재가격"]*buy_item:,} 원 ")

                    buy_dic[cart] = {"품명":sel_name,"개수":buy_item,
                                     "개당가격":market[f_key]["현재가격"],
                                     "총가격":market[f_key]["현재가격"]*buy_item}
                    input("\n계속하려면 엔터를 누르세요...")
                    # print(buy_dic)
            else :
                print("없는 품목입니다. 죄송합니다")
                input("\n계속하려면 엔터를 누르세요...")

     return total_cash

def discount_page (market,discount): #할인페이지
     
     while True :
          # clear_screen()
          print("1. 할인 품목 선택 ") #추가 분리가능할까?
          print("2. 깜짝 할인 진행 ")
          print("3. 이전 화면")
          sel_num = int(input("#번호 입력 :"))
          if sel_num == 1:
               clear_screen()
               print("q 입력시 이전 화면")
               sel_name = input("#할인할 품목 : ")
               f_key = find_key(market,sel_name)
               if sel_name =='q':
                    break
               if f_key != None :
                     print("할인적용할 물품 :",market[f_key]["품명"])
                     discount_num = int(input("원하는 할인율(10~40) : "))
                     if  10 <= discount_num <= 40 : 
                         print(f"{market[f_key]["품명"]}의 할인 전 가격은 {market[f_key]["현재가격"]:,} 원 입니다. ")
                         market[f_key]["현재가격"]= market[f_key]["원가"] - int((market[f_key]["원가"]*(discount_num*0.01)))
                         print(f"{market[f_key]["품명"]}의 할인 후 가격은 {market[f_key]["현재가격"]:,} 원 입니다. ")
                         market[f_key]["할인율"] = discount_num
                         discount +=1
                         input("\n계속하려면 엔터를 누르세요...")
                     else : 
                          print ("숫자 확인")
               else :
                    print("품목 확인")
                    input("\n계속하려면 엔터를 누르세요...")

          elif sel_num ==2 : #깜짝할인
               # print("chk")
               for i in range(5): # 최대 5개의 품목
                    dis_item = random.randint(1,100)
                    if dis_item in market  and market[dis_item]["할인율"] == 0 :
                         discount_ran = random.randint(1,4)*10
                         print(f"{market[dis_item]["품명"]}의 할인 전 가격은 {market[dis_item]["현재가격"]:,} 원 입니다. ")
                         market[dis_item]["현재가격"]= market[dis_item]["원가"] - int((market[dis_item]["원가"]*(discount_ran*0.01)))
                         print(f"{market[dis_item]["품명"]}의 할인 후 가격은 {market[dis_item]["현재가격"]:,} 원 입니다. ")
                         market[dis_item]["할인율"] = discount_ran
                         discount +=1

                    else :
                         continue
               input("\n계속하려면 엔터를 누르세요...")
          elif sel_num ==3 :
               break
          else :
               print("번호 확인")
     return discount

#main
market = market_dic(물품명)

discount=0
total_cash=0
while True :
     sel_num=show_main(discount)
     if sel_num ==1 :
          show_admin_menu(market,total_cash)
     elif sel_num ==2:
         total_cash= buy_page (total_cash)
     elif sel_num ==3:
          discount=discount_page (market,discount)
     elif sel_num ==4:
          break
     else :
          print("번호 확인")