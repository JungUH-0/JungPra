import random

# 1~50 숫자 맞추기
ran=random.randint(1,50)
print(ran)

while True :
     duo=input("10회 제한있는 게임 'Y' 없는 게임 'N' 게임종료: C :")
     count=10
     if duo=='c' or duo == 'C' :
          break
     if duo == 'y' or duo =='Y':
          while True :
               num = int(input("숫자 입력:"))
               if num == ran :
                    print("ok")
                    break
               elif num>ran :
                    print("down")
               else :
                    print("up")    
               
               count -=1
               if count == 0 :
                    print("목숨끝")
                    break
               print("남은목숨 :",count)

               
     elif duo=='N' or duo=='n' :
          while True :
               num = int(input("숫자 입력:"))
               if num == ran :
                    print("ok")
                    break
               elif num>ran :
                    print("down")
               else :
                    print("up")   
     else :
          print ("'y' 또는 'n' 입력")
     
     