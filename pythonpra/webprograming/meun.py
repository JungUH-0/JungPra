import tkinter


window=tkinter.Tk()
window.title("JungUH")
window.geometry("800x700+200+200")
window.resizable(False,False)

def close():
     window.quit()
     window.destroy()

menubar = tkinter.Menu(window)
menubutton = tkinter.Menubutton(window,text="메뉴 버튼",relief="raised", direction="right")
menubutton.pack()

menu=tkinter.Menu(menubutton,tearoff=0)
menu.add_command(label="하위메뉴-1")
menu.add_separator()
menu.add_command(label="하위메뉴-2")
menu.add_command(label="하위메뉴-3")


menu_1=tkinter.Menu(menubar, tearoff=0)
menu_1.add_command(label="하위 메뉴 1-1")
menu_1.add_command(label="하위 메뉴 1-2")
menu_1.add_separator()
menu_1.add_command(label="하위 메뉴 1-3", command=close)
menubar.add_cascade(label="상위 메뉴 1", menu=menu_1)

menu_2=tkinter.Menu(menubar, tearoff=0, selectcolor="red")
menu_2.add_radiobutton(label="하위 메뉴 2-1", state="disable")
menu_2.add_radiobutton(label="하위 메뉴 2-2")
menu_2.add_radiobutton(label="하위 메뉴 2-3")
menubar.add_cascade(label="상위 메뉴 2", menu=menu_2)

menu_3=tkinter.Menu(menubar, tearoff=0)
menu_3.add_checkbutton(label="하위 메뉴 3-1")
menu_3.add_checkbutton(label="하위 메뉴 3-2")
menubar.add_cascade(label="상위 메뉴 3", menu=menu_3)


menubutton["menu"]=menu

window.config(menu=menubar)

window.mainloop()