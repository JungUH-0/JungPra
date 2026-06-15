# import flet as ft

# allpin=[0,1,2,3,4,5,6,7,8,9,10]


# def main(page : ft.page):
#   page.title = "볼링계산기"
#   page.window.width = 900
#   page.window.height = 750
#   page.theme_mode = ft.ThemeMode.LIGHT
#   btn_style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))

#   current_frame = {"idx": -1}
#   frames = []

#   def make_btn(text):
#       return ft.ElevatedButton(text, style=btn_style, width=120, height=30, on_click=lambda e :click(text))
  
#   def click(text):
#       pass
  
#   btn_values = [
#   ["1","2","3","-"],
#   ["4","5","6","/"],
#   ["7","8","9","X"]
#   ]
#   btnsys_values =[["새게임","리셋","종료"]]

#   btn_rows = [
#     [make_btn(v) for v in row]
#   for row in btn_values
#   ]
  

#   def make_frame(frame_num):
#       idx = len(frames)
      

#       box_count = 3 if frame_num == 10 else 2

#       inputs = [
#           ft.TextField(width=20, height=30, text_align=ft.TextAlign.CENTER)
#           for _ in range(box_count)
#       ]

#       score = ft.Text("0", size=15)
      

#       container = ft.Container(
#           content=ft.Column(
#               [
#                   ft.Row(inputs, spacing=2),
#                   score
#               ],
#               alignment=ft.MainAxisAlignment.CENTER,
#               horizontal_alignment=ft.CrossAxisAlignment.CENTER
#           ),
#           border=ft.border.all(2, "grey"),
#           bgcolor='red',
#           padding=12,
#           width=70 if frame_num != 10 else 90,
#       )

#       def on_click(e):
#           current_frame["idx"] = idx
          
#           update_highlight()

#       container.on_click = on_click
#       frames.append(container)

#       return container

#   def update_highlight():
#       for i, f in enumerate(frames):
#           if i == current_frame["idx"]:
#               f.border = ft.border.all(3, "blue")
#               f.bgcolor = "#e3f2fd"
#           else:
#               f.border = ft.border.all(2, "grey")
              
#       page.update()

#   frames = [make_frame(i) for i in range(1, 11)]

#   board = ft.Row(frames, spacing=5)

#   score_display = ft.Container(
#       content=ft.Column([
#           ft.Text("BOWLING SCOREBOARD", size=12, weight="bold", color='BLUE'),
#         board
#       ]),
#       width=800,
#       height=500,
#       padding=10,
#       border=ft.border.all(1,'grey'),
#       border_radius=15,
#       bgcolor='white'
#   )
  
  
#   page.add(score_display,
#             ft.Divider(),
#   *[ft.Row(row) for row in btn_rows]
# )
# ft.app(target=main)

import flet as ft

def remain_pin(ball):
    return [i for i in range(11 - ball)]

def get_score(game_dict):
    score_list = []
    n = len(game_dict)
    for i in range(1, n + 1):
        # 1. 이번 프레임에 공을 하나도 안 던졌다면 계산 중단
        if not game_dict[i]:
            break # 혹은 continue
            
        temp_score = 0
        f_sum = sum(game_dict[i])
        
        if i == n: # 10프레임
            temp_score += f_sum
        else:
            if game_dict[i][0] == 10: # 스트라이크인 경우
                temp_score += 10
                # [안전장치] 다음 프레임(i+1)의 첫 번째 공 데이터가 있는지 확인
                if i+1 in game_dict and len(game_dict[i+1]) >= 1:
                    next_val = game_dict[i+1][0]
                    temp_score += next_val
                    
                    # [안전장치] 또 그다음 공이 있는지 확인 (더블 스트라이크 혹은 2구)
                    if next_val == 10: # 더블인 경우
                        if i+2 in game_dict and len(game_dict[i+2]) >= 1:
                            temp_score += game_dict[i+2][0]
                        # 만약 10프레임이라서 i+2가 없다면 i+1의 두번째 공 확인
                        elif len(game_dict[i+1]) >= 2:
                            temp_score += game_dict[i+1][1]
                    else: # 스트라이크 후 다음 프레임이 오픈인 경우
                        if len(game_dict[i+1]) >= 2:
                            temp_score += game_dict[i+1][1]
                            
            elif f_sum == 10: # 스페어인 경우
                temp_score += 10
                # [안전장치] 다음 프레임의 첫 번째 공이 들어왔을 때만 합산
                if i+1 in game_dict and len(game_dict[i+1]) >= 1:
                    temp_score += game_dict[i+1][0]
            else: # 오픈
                temp_score += f_sum

        score_list.append(temp_score)
    return score_list

def resultboard(score):
    score_list = []
    sum_score = 0
    for i in score:
        sum_score += i
        score_list.append(sum_score)
    return score_list

# --- [UI 및 메인 로직] ---
def main(page: ft.Page):
    
    page.title = "볼링 계산기 Professional"
    page.window.width = 950
    page.window.height = 750
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30

    game_data = {i: [] for i in range(1, 11)}
    frame_ui_list = [] # UI 객체들 저장
    state = {"f_idx": 0, "b_idx": 0} # 현재 입력 중인 프레임 인덱스, 공 인덱스
    num_buttons = {}

    # --- 1. 버튼 클릭 시 실행될 함수 ---
    def on_btn_click(text):
        f_idx = state["f_idx"]
        b_idx = state["b_idx"]

        if f_idx >= 10: return # 게임 종료 시 무시

        # 1) UI의 빈칸(TextField)에 값 넣기
        # frame_ui_list[f_idx]["inputs"]는 해당 프레임의 [첫번째칸, 두번째칸] 리스트임
        target_input = frame_ui_list[f_idx]["inputs"][b_idx]
        target_input.value = text
        
        # 2) 점수 데이터로 변환하여 저장 (점수 계산용)
        val_map = {"-": 0, "X": 10, "/": 10 - (game_data[f_idx+1][0] if game_data[f_idx+1] else 0)}
        score = int(val_map.get(text, text))
        game_data[f_idx+1].append(score)

        # 3) 다음 칸으로 이동하는 로직
        if f_idx < 9: # 1~9프레임
            if text == "X" or b_idx == 1: # 스트라이크거나 두 번째 공이면 다음 프레임으로
                state["f_idx"] += 1
                state["b_idx"] = 0
            else: # 첫 번째 공 던졌으면 같은 프레임 두 번째 칸으로
                state["b_idx"] = 1
        else: # 10프레임 예외 처리
            shots = game_data[10]
            if len(shots) == 2 and sum(shots) < 10: # 오픈 종료
                state["f_idx"] += 1
            elif len(shots) == 3: # 보너스 종료
                state["f_idx"] += 1
            else: # 다음 보너스 칸으로
                state["b_idx"] += 1

        update_display() # 화면 갱신
        update_button_status()
        page.update()


    def update_button_status():
        f_idx = state["f_idx"]
        b_idx = state["b_idx"]
        last_frame_shots = game_data[10]
        # 현재 프레임에서 이미 던진 공들
        
        
        # 기본적으로 모든 숫자(0~10) 허용
        allowed_pins = list(range(11))
        is_game_over = False
        if f_idx >= 10:
            is_game_over = True
    
    # 2. 혹은 10프레임 안에서 투구가 끝났는지 세부 체크
        elif f_idx == 9:
            if len(last_frame_shots) == 2 and sum(last_frame_shots) < 10:
                is_game_over = True # 오픈으로 종료
            elif len(last_frame_shots) == 3:
                is_game_over = True # 스트라이크/스페어 후 보너스까지 종료

    # --- [버튼 처리] ---
        if is_game_over:
            
            # 모든 버튼(숫자, X, /, - 등)을 비활성화하고 흐리게 만듭니다.
            for btn in num_buttons.values():
                btn.disabled = True
                btn.opacity = 0.3
            page.update()
            return
        current_shots = game_data[f_idx + 1]

        if f_idx < 9:  # 1~9프레임
            if b_idx == 1:  # 두 번째 투구일 때
                first_ball = current_shots[0]
                # 사용자님의 remain_pin 함수를 사용하여 허용 범위 계산
                allowed_pins = remain_pin(first_ball)
        
        else:  # 10프레임 예외 처리
            if b_idx == 1: # 10프레임 두 번째 투구
                if current_shots[0] < 10: # 첫 공이 스트라이크가 아니면
                    allowed_pins = remain_pin(current_shots[0])
                else: # 첫 공이 스트라이크면 다시 10개 가능
                    allowed_pins = list(range(11))
            elif b_idx == 2: # 10프레임 보너스 투구
                if current_shots[1] == 10 or sum(current_shots[:2]) == 10:
                    allowed_pins = list(range(11))
                else:
                    allowed_pins = remain_pin(current_shots[1])

        # --- UI 버튼 비활성화 적용 ---
        # num_buttons는 {"1": btn_obj, "2": btn_obj...} 형태의 딕셔너리여야 함
        for val, btn in num_buttons.items():
            if val.isdigit(): # 숫자 버튼인 경우
                is_allowed = int(val) in allowed_pins
                btn.disabled = not is_allowed
                btn.opacity = 1.0 if is_allowed else 0.3 #투명도
            
            elif val == "/": # 스페어 버튼 제어
                # 첫 번째 투구에서만 비활성화, 두 번째 투구에서 활성화
                btn.disabled = (b_idx == 0)
                btn.opacity = 1.0 if b_idx == 1 else 0.3 
                
            elif val == "X": # 스트라이크 버튼 제어
                # 1~9프레임은 첫 투구에서만 가능, 10프레임은 상황에 따라
                can_strike = (b_idx == 0) or (f_idx == 9 and (current_shots[-1] == 10 or sum(current_shots) == 10))
                btn.disabled = not can_strike
                btn.opacity = 1.0 if can_strike else 0.3
        if f_idx>10 :
            btn.disabled=not is_allowed
        page.update()

    # --- 2. 화면 갱신 함수 (하이라이트 및 점수 계산) ---
    def update_display():
        # 실시간 점수 계산 (에러 방지용 체크 포함)
        # raw_scores = get_score(game_data) <- 여기에 안전장치 있는 get_score 연결
        # result = resultboard(raw_scores)
        
        try:
            raw_scores = get_score(game_data) # [10, 8, ...] 꼴
            accumulated_result = resultboard(raw_scores) # [10, 28, ...] 꼴
        except Exception as e:
            print(f"계산 중 오류 발생: {e}")
            accumulated_result = []

        for i, f_ui in enumerate(frame_ui_list):
            # 2. 누적 점수 반영 (계산 결과가 있는 프레임까지만)
            if i < len(accumulated_result):
                f_ui["score_text"].value = str(accumulated_result[i])
            else:
                # 아직 계산 결과가 없는 프레임은 이전 점수 유지 혹은 빈값
                pass

            # 3. 하이라이트 (현재 입력할 프레임 강조)
            if i == state["f_idx"]:
                f_ui["container"].border = ft.border.all(3, "blue")
                f_ui["container"].bgcolor = "#f0f7ff"
            else:
                f_ui["container"].border = ft.border.all(2, "grey300")
                f_ui["container"].bgcolor = "white"
        
        # 버튼 상태 업데이트 (이전에 만든 remain_pin 연동 함수가 있다면 여기서 호출)
        # update_button_status() 
        
        page.update()
    # --- 3. 프레임 UI 생성 함수 ---
    def make_frame(num):
        box_count = 3 if num == 10 else 2
        # 실시간으로 값을 넣을 TextField 리스트
        inputs = [
            ft.TextField(
                width=30, height=35, 
                text_align="center", 
                read_only=True, # 직접 타이핑 방지
                border_color="blue400",
                text_size=14,
                content_padding=0
            ) for _ in range(box_count)
        ]
        score_text = ft.Text("0", size=16, weight="bold")

        container = ft.Container(
            content=ft.Column([
                ft.Text(f"{num}F", size=10, weight="bold"),
                ft.Row(inputs, spacing=2, alignment="center"),
                score_text
            ], spacing=5, horizontal_alignment="center"),
            width=80 if num != 10 else 110,
            border=ft.border.all(2, "grey300"),
            border_radius=10,
            padding=10
        )
        
        # 나중에 접근하기 쉽게 딕셔너리로 저장
        frame_ui_list.append({
            "container": container,
            "inputs": inputs, # 이 리스트를 통해 나중에 value를 바꿈
            "score_text": score_text
        })
        return container

    # --- 4. 메인 레이아웃 구성 ---
    board = ft.Row([make_frame(i) for i in range(1, 11)], alignment="center", spacing=5)
    
    # 버튼 생성 
    def make_btn(v):
        btn = ft.ElevatedButton(
        v, width=80, height=50, 
        on_click=lambda e: on_btn_click(v)
        )
        # [핵심!] 만든 버튼을 나중에 조작할 수 있게 이름(v)표를 붙여 저장합니다.
        num_buttons[v] = btn 
    
        return btn

    btn_grid = ft.Column([
        ft.Row([make_btn(v) for v in ["1","2","3","-"]], alignment="center"),
        ft.Row([make_btn(v) for v in ["4","5","6","/"]], alignment="center"),
        ft.Row([make_btn(v) for v in ["7","8","9","X"]], alignment="center"),
    ], spacing=10)

    page.add(
        ft.Text("볼링 스코어 시스템", size=24, weight="bold"),
        ft.Container(board, padding=20),
        ft.Divider(height=40),
        btn_grid
    )
    
    update_display()

ft.run(main)