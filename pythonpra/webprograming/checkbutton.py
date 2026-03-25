import tkinter

window=tkinter.Tk()
window.title("JungUH")
window.geometry("800x700+200+200")
window.resizable(False,False)

def flash():
     chbutton1.flash()

def check():
     label.config(text="radioVariety_1= "+ str(radioVariety_1.get()) +
                   "\n" + "radioVariety_2= "+str(radioVariety_2.get())+
                   "\n\n" + "Total = "+str(radioVariety_1.get()+radioVariety_2.get()))
     
     


checkVariety_1=tkinter.IntVar()
checkVariety_2=tkinter.IntVar()
checkVariety_3=tkinter.IntVar()
radioVariety_1=tkinter.IntVar()
radioVariety_2=tkinter.IntVar()

chbutton1=tkinter.Checkbutton(window,text="O",variable=checkVariety_1,activebackground="blue")
chbutton2=tkinter.Checkbutton(window,text="X",variable=checkVariety_2)
chbutton3=tkinter.Checkbutton(window,text="W",variable=checkVariety_1,command=flash)

radio1=tkinter.Radiobutton(window,text="1번",value=3, variable=radioVariety_1, command=check)
# radio1.pack()
radio2=tkinter.Radiobutton(window,text="2번(1번)",value=3, variable=radioVariety_1, command=check)
# radio2.pack()
radio3=tkinter.Radiobutton(window,text="3번",value=9, variable=radioVariety_1, command=check)
# radio3.pack()
label=tkinter.Label(window, text="None", height=5)
# label.pack()
radio4=tkinter.Radiobutton(window,text="4번",value=12, variable=radioVariety_2, command=check)
# radio4.pack()
radio5=tkinter.Radiobutton(window,text="5번",value=15, variable=radioVariety_2, command=check)
# radio5.pack()
radio1.pack()
radio2.pack()
radio3.pack()
label.pack()
radio4.pack()
radio5.pack()

chbutton1.pack(side="left") #side 사용 혹은 grid(row=0, column=0, padx=20, pady=20)
chbutton2.pack(side="left")
chbutton3.pack(side="left")


window.mainloop()