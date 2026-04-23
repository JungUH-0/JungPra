
scoreboard=[0,1,2,3,4,5,6,7,8,9,10]

def sel_game (play) :
     if play == 'a':
          return 5
     else :
          return 10
     
# def set_game (frame) :
#      game = {}
#      for i in range(frame):
#           game[i+1] = 0
#      return game 

def app_secondball(chk_l,people,i): # 두 번째 투구
     secondball = -1
     while secondball not in chk_l :
          try:
               secondball= int(input(f"{people}의 {i+1}프레임 두번째 점수 : "))
          except ValueError:
               continue
     return secondball

def app_bonusball(chk_l,people,i): # 보너스 투구
     bonusball = -1
    
     while bonusball not in chk_l:
          try:
               bonusball= int(input(f"{people}의 {i+1}프레임 보너스 점수 : "))
          except ValueError:
               continue
     return bonusball

def remain_pin (ball) : #잔여핀 
     
     chk_list = []
     for i in range(11-ball):
          chk_list.append(i)
     
     return chk_list

def input_score (people,frame) :
     global scoreboard
     game = {}
     for i in range(frame):
          firstball = -1
          while firstball not in scoreboard :
               try:
                    firstball= int(input(f"{people}의 {i+1}프레임 첫번째 점수 : "))
               except ValueError:
                    continue
          game[i+1]=[firstball]

          if firstball != 10: # 스트라이크 X
          #      chk_list = []
          #      for j in range(11-firstball):
          #           chk_list.append(j)
               chk_list=remain_pin(firstball)
               secondball= app_secondball(chk_list,people,i)
               game[i+1].append(secondball)
          
          else:# 스트라이크 O
               if i+1 != frame: # 마지막 프레임전까지
                         secondball =0
               else : #마지막 프레임 
                    chk_list= scoreboard
                    secondball = app_secondball(chk_list,people,i)

               game[i+1].append(secondball)
          print(f"game{i+1}은 {game[i+1]}")

     if i+1 ==frame and (sum(game[i+1]) >=10)  :
          if secondball !=10:
               chk_list=remain_pin(secondball)
          else :chk_list=scoreboard
          bonusball = app_bonusball(chk_list,people,i)

          game[i+1].append(bonusball)
     return game

def get_score (frame):
     score_list = []
     n= len(frame)
     for i in range(1,n+1):
          temp_score = 0
          f_sum = sum(frame[i])
          if i == n:
               temp_score+=f_sum
          else :
               if frame[i][0] == 10 : # 스트라이크
                    temp_score+= frame[i][0]

                    if frame[i+1][0] ==10 and i+2 <= n:
                         temp_score+=frame[i+1][0]+frame[i+2][0]
                    else:
                         temp_score+=frame[i+1][0]+frame[i+1][1]
               elif frame[i][0] !=10 and f_sum ==10 : # 스페어
                    temp_score+= f_sum + frame[i+1][0]
               else: # 오픈
                    temp_score+=f_sum

          score_list.append(temp_score)
     return score_list

def resultboard (score):
     score_list= []
     sum_score = 0
     for i in score :
          sum_score += i
          score_list.append(sum_score)
     return score_list

game = input_score(1,10)

print (game)
score = get_score(game)
print(score)
resultscore = resultboard(score)
print(resultscore)
# while True :
