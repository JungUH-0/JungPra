import flet as ft
import random
count = 10
def main(page: ft.Page):
     
     page.title = "숫자 맞추기 게임"
     num = ft.TextField(label="1~50 입력")
     page.add(ft.Text(value="랜덤 숫자 맞추기",size=50)) #변경이 힘듬
     txt=ft.Text(f"남은 목숨 : {count} ",size=20) # 변경이 쉬움
     ran = random.randint(1,50)
     print(ran)
     num = ft.TextField(label="1~50 입력")
     msg= ft.Text(" ")
     
     def num_chk(e):
          global count
          
          try:
           numchk = int(num.value) # 여기서 숫자가 아니면 바로 except로 이동해서 실행됨
           if numchk <0:
               msg.value = "음수는 입력하지마세요 (1~50)"
               page.update()
               return
          except ValueError:
               # 정수가 아닐 때 실행될 코드
               msg.value = "숫자만 입력해주세요 (1~50)"
               page.update()
               return
          
          if numchk == ran :
               msg.value = "정답"
          elif  numchk > ran:
               msg.value = "down"
               count -= 1
          else :
               msg.value = "up"
               count -= 1
          txt.value = f"남은 목숨 : {count}"

          if count<=0 :
               page.update()
               life_chk()
               return
          page.update()
            
     def life_chk(e=None) :
         page.window.close()
         

     # page.add(ft.Text(value="랜덤 숫자 맞추기",size=50)) #변경이 힘듬
     # txt=ft.Text(f"남은 목숨 : {count} ",size=20) # 변경이 쉬움
     # ran = random.randint(1,50)
     # print(ran)
     # num = ft.TextField(label="1~50 입력")
     # msg= ft.Text(" ")

     page.add(
          txt,
          num,
          ft.ElevatedButton("확인",on_click=num_chk),
          msg
          )
ft.app(target=main, view=ft.AppView.WEB_BROWSER)