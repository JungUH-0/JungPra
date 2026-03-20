import flet as ft
import random
count = 10
def main(page: ft.Page):
     num = ft.TextField(label="1~50 입력")
     
     def num_chk(e):
          global count
          numchk = int(num.value)
          if numchk == ran :
               msg.value = "정답"
          else :
               msg.value = "틀림"
               count -= 1
          txt.value = f"남은 목숨 : {count}"

          if count<=0 :
               page.update()
               life_chk()
               return
          page.update()
            
     def life_chk(e=None) :
         page.window.close()
         

     page.add(ft.Text(value="랜던 숫자 맞추기",size=50)) #변경이 힘듬
     txt=ft.Text(f"남은 목숨 : {count} ",size=20) # 변경이 쉬움
     ran = random.randint(1,50)
     print(ran)
     num = ft.TextField(label="1~50 입력")
     msg= ft.Text(" ")

     page.add(
          txt,
          num,
          ft.ElevatedButton("확인",on_click=num_chk),
          msg
          )
ft.app(target=main)