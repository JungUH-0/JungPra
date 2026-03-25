#tkinter를 tk 명명
import tkinter as tk
from math import *
#count란 변수 선언
count=0
#def는 파이선에서 함수를 만들겠다 선언 자바로 따지면 function?
def countplus() :
    global count 
    count +=1
    label.config(text=str(count))

def countminus():
    global count
    count -=1
    label.config(text=str(count))

def calc(event):
    label.config(text="결과="+str(eval(entry.get())))

#window란 변수이다/ 창 선언? 예제니깐 window wd로도 가능
window = tk.Tk()

#wd=tk.Tk()

#mainloop() 전에 ui설정
window.title("티킨터공부")
#geometry윈도우창설정 000x000(너비x높이)은 창의 크기를 정함/ +00+00(x,y) 창의 왼쪽위 기준으로 어디서 창을 띄울건지 정함
window.geometry("800x500+500+100")
#resizeable 창의 크기 조절 (상하,좌우)/False=0,True=1
window.resizable(0,True)
#Label,Button,Entry...등 window라는 부모에 소속 5번째줄에서 window선언했기에 씀 만약 안쓰면 모든 window 창에 텍스트 출력
label=tk.Label(window,text="0")
label.pack()
lb=tk.Label(window,text="속성이 많다=명령어 개많음",width=1000,fg="red",relief="groove")
lb.pack()
#command 누를때 발생할 이벤트 선언
button1=tk.Button(window,width=10,text="더하기",overrelief="solid",command=countplus)
button1.pack()
button2=tk.Button(window,width=10,text="빼기",overrelief="solid",command=countminus)
button2.pack()
#Entry 흔히아는 텍스트박스?
entry=tk.Entry(window)
entry.bind("<Return>",calc)
entry.pack()
#Entry 텍스트 삽입을 위한/텍스트 앞에 숫자0은 다른뜻이 아닌 몇번째부터 채워라라는 뜻
entry.insert(0,"계산기")
#selectmode 매개변수 확인
listbox=tk.Listbox(window,selectmode="extended",height=5)

listbox.insert(0,"1")
listbox.insert(1,"2")
listbox.insert(2,"3")
listbox.insert(3,"4")
listbox.insert(4,"5")
listbox.insert(5,"6")
listbox.insert(6,"7")
listbox.insert(7,"8")
listbox.insert(8,"9")
listbox.insert(9,"10")
listbox.insert(10,"11")
listbox.insert(11,"12")
listbox.insert(12,"13")
listbox.insert(13,"14")
listbox.insert(14,"15")
listbox.insert(15,"16")
listbox.xview_scroll(5,"units")
#listbox.delete(1)



listbox.pack()


#mainloop() 창을 여는뜻?
window.mainloop()

#wd.mainloop()  