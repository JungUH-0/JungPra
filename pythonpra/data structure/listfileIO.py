from list import data_List 
import os


temp=0
temp_list=None
while True:
    try:
        if os.path.exists("listtest.txt"):
            with open("listtest.txt",'r',encoding = 'utf-8') as f :
                temp_list = data_List(len(f.readlines()))
                f.seek(0)
                for i in f.readlines() :
                    temp_list.append(i)
                    temp +=1
    except :
        pass
    
    try:
        memosize = int(input("메모장의 줄 수  : "))
        memosize += temp
        break
    
    except:
        print("숫자 입력")

my_memo = data_List(memosize)
if temp_list != None:
    for i in temp_list.data_list :
        my_memo.append(i.rstrip('\n')) # 끝에 \n 제거

while True :
    print ("\n--------------------------------------")
    print("""
    메뉴키
    i: 라인 삽입
    d: 한 라인 삭제
    r: 한 라인 변경
    p: 현재 내용 출력
    l: 파일 입력(라인출력)
    s: 파일 저장
    q: 편집기 종료
""")
    sel_menu = input("원하는 메뉴 선택 : ")
    print ("--------------------------------------")

    if sel_menu == "q" :
        break
    elif sel_menu =="i":
        while True :
            try :
                idx = int(input("삽입 행 번호 입력 : (0~" + str(my_memo.maxsize-1)+")"))
                if idx >= my_memo.maxsize :
                    print("줄 수 초과")
                    continue
                else:
                    break
            except :
                print("숫자입력")
        val = input("문자열 입력 : ")
        my_memo.insert(idx,val)

    elif sel_menu =="d":
        while True :
            try :
                idx = int(input("바꿀 행 번호 입력 : (0~" + str(my_memo.size()-1)+")"))
                if idx > my_memo.size() :
                    print("줄 수 초과")
                    continue
                else:
                    break
            except :
                print("숫자입력")

        my_memo.delete(idx)

    elif sel_menu =="r":
        while True :
            try :
                idx = int(input("바꿀 행 번호 입력 : (0~" + str(my_memo.size()-1)+")"))
                if idx > my_memo.size() :
                    print("줄 수 초과")
                    continue
                else:
                    break
            except :
                print("숫자입력")
        val = input("바꿀 문자열 입력 : ")
        my_memo.replace(idx,val)

    elif sel_menu =="p":
        cnt= 0
        for i in my_memo.data_list:
            cnt+=1
            print(cnt, end =" ")
            print("" if i is None else i )
    elif sel_menu =="l":
        try:
            if os.path.exists("listtest.txt"):
                with open("listtest.txt",'r',encoding = 'utf-8') as f :
                    for i in f.readlines() : print(i,end='')

        except :
            print("no file")
    elif sel_menu =="s":
            if os.path.exists("listtest.txt"): #있으면 True
                with open("listtest.txt",'w',encoding = 'utf-8') as f :
                    for i in my_memo.data_list:
                        f.write("\n" if i is None else i + "\n")
            else : #없으면 false
                with open("listtest.txt",'w',encoding = 'utf-8') as f :
                    for i in my_memo.data_list:
                        f.write("\n" if i is None else i + "\n")
            break

    else :
        print("select chk")
        continue