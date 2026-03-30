import random

#  1= 가위 2= 바위 3= 보 1<2<3<1
def vic3 (a,b,c,d,e) :
    a+=1
    print("{}번째 판".format(a))
    if(b==c):
        print("무승부")
        return a,d,e
    if(c==1):
        if(b==2):
            print("me 승리!!!!")
            d+=1
        else:
            print("com 승리!?!?!")
            e+=1
    elif(c==2):
        if(b==3):
            print("me 승리!!!!")
            d+=1

        else:
            print("com 승리!?!?!")
            e+=1
    elif(c==3):
        if(b==1):
            print("me 승리!!!!")
            d+=1
        else:
            print("com 승리!?!?!")
            e+=1
    return a,d,e


# main
g=0
p=0
co=0

while True :
    while g !=5 :
        com = random.randint(1,3)
        print(com)
        while True:
            me = int(input("숫자 입력 (1~3) : "))
            if(me>3 or me<1) :
                print("1~3의 숫자 입력")
            else :
                break

        g,p,co= vic3(g,me,com,p,co)
        print("com 승수 : {}".format(co))

        print("me 승수 : {}".format(p))
        if(p==3) :
            print("me 최종승리!!!!!!!!!!!!!!!!!")
            break
        if(co==3) :
            print("com 최종승리@@@@@@@@@@@@@@")
            break


    if(p==3 or co==3):
        break

    if(g>=5):
        print("{}판 결과 안남 다시+@!@!@!@!@!@+!@!)@!@#@$)(!$!)".format(g))
        g=0
        p=0
        co=0
