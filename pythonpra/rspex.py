# import random
# def rsp_sel(str):
#     rsp = None
#     if str == 'user':
#         while True:
#             rsp = input("가위, 바위, 보 중에 하나를 입력해 주세요: ")
#             if rsp in ['가위', '바위', '보']:
#                 break
#             print("잘못 입력했어요")
#     else:
#         rsp = list_rsp[random.randint(0,2)]

#     return rsp

# def rsp_referee(user_rsp, com_rsp, winpoint):
#     winner = dic_rsp_referee[user_rsp][com_rsp]

#     if winner == 'user':
#         winpoint[winner] = winpoint[winner] + 1
#         print("{}가 승리({} / {}: {} / {})".format('user', 'user', winpoint['user'],'com',winpoint['com']))
#     elif winner == 'com':
#         winpoint[winner] = winpoint[winner] + 1
#         print("{}가 승리({} / {}: {} / {})".format('com', 'com', winpoint['com'], 'user', winpoint['user']))
#     else:
#         print("무승부")

#     return winpoint

# wincount = {'user': 0, 'com': 0}

# list_rsp = {0:'가위', 1:'바위', 2:'보'}
# dic_rsp_referee = {
#         '가위':{'가위': None, '바위': 'com', '보': 'user'},
#         '바위':{'가위': 'user', '바위': None, '보': 'com'},
#         '보':{'가위': 'com', '바위': 'user', '보': None}
#     }

# while True:
#     #사용자의 가위바위보 선택
#     user_rsp = rsp_sel('user')
#     com_rsp = rsp_sel('com')

#     #승부결정, 승 횟수 누적
#     wincount = rsp_referee(user_rsp, com_rsp, wincount)

#     if wincount['user'] >= 3 or wincount['com'] >= 3:
#         print(wincount)
#         break


 #-------------------------------------------------------------------------------------   
import flet as ft
import random


count=0

def main(page: ft.Page):
    page.padding = 0 # 여백 없애기 화면 꽉참
    # page.bgcolor = "pink"
    win_count={'user':0,'com':0}
    result_text = ft.Text(size=20, text_align=ft.TextAlign.CENTER)
    final_text=ft.Text("")
    play_cout_text=ft.Text(f"경기 횟수:{count}")
    wcount_text=ft.Text(f"com : {win_count['com']} : user : {win_count['user']}")
    
    
    
    results = {
        '가위': {'가위': '무승부', '바위': 'com', '보': 'user'},
        '바위': {'가위': 'user', '바위': '무승부', '보': 'com'},
        '보': {'가위': 'com', '바위': 'user', '보': '무승부'}
    }
    buttons = [
        ft.ElevatedButton("가위", data="가위",  on_click=lambda e: play(e)),
        ft.ElevatedButton("바위", data="바위",  on_click=lambda e: play(e)),
        ft.ElevatedButton("보", data="보",  on_click=lambda e: play(e)),
    ]
    def winchk(winner,win_c):
        if winner=='무승부':
            return win_c
        elif winner=='com':
            win_c[winner]=win_c[winner]+1
        else :
            win_c[winner]=win_c[winner]+1
        
        return win_c
        
    def finalwin(winner):
        text=f"최종 승리자는 {winner}"
        return text


    def play(e):
        global count
        nonlocal win_count
        user_choice = e.control.data 
        com_choice = random.choice(['가위', '바위', '보'])
        winner = results[user_choice][com_choice]
        # print(winner) 결과 (무승부,컴퓨터 승,사용자 승 3개중 1개)
        count +=1
        play_cout_text.value=f"경기횟수:{count}"
        win_count=winchk(winner,win_count)
        wcount_text.value = f"com : {win_count['com']} : user : {win_count['user']}"
        # 결과 출력
        if (winner=='무승부'):
            final_text.value = f"결과: {winner} \n(나: {user_choice} vs 컴퓨터: {com_choice})"
        else :
            final_text.value = f"결과: {winner}승리! \n(나: {user_choice} vs 컴퓨터: {com_choice})"
            # 3승시 종료
        if(win_count['user']==3 or win_count['com']==3) :
            for btn in buttons:
                btn.disabled = True
            result_text.value=finalwin(winner)

            # 5판 결과 안날시 리셋
        if(count >=5):
            count =0
            win_count['com']=0
            win_count['user']=0
        
        # if (winner=='무승부'):
        #     final_text.value = f"결과: {winner} \n(나: {user_choice} vs 컴퓨터: {com_choice})"
        # else :
        #     final_text.value = f"결과: {winner}승리! \n(나: {user_choice} vs 컴퓨터: {com_choice})"


        # win_count[winner]=win_count[winner]+1
        page.update()

    def reset(e):
        global count
        nonlocal win_count
    
        count = 0
        win_count = {'user': 0, 'com': 0}
        
        play_cout_text.value = f"경기 횟수:{count}"
        wcount_text.value = f"com : {win_count['com']} : user : {win_count['user']}"
        final_text.value = ""
        result_text.value = "게임 시작"
        for btn in buttons:
            btn.disabled = False
        
        page.update()
           
    
   
    page.add(
        ft.Column([play_cout_text,
            ft.Row(buttons, alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            wcount_text,
            result_text,
            final_text,
            ft.ElevatedButton("리셋",on_click=reset,color="red")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)