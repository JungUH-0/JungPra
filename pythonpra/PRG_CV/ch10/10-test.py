import cv2
import mediapipe as mp
import numpy as np
 
# ----------------------------
# MediaPipe 손 인식
# ----------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
 
mp_draw = mp.solutions.drawing_utils
 
# ----------------------------
# 카메라 실행
# ----------------------------
cap = cv2.VideoCapture(0)
 
# 그림판 캔버스
canvas = None
 
# 이전 점 저장
prev_x, prev_y = 0, 0
 
# 현재 색상
draw_color = (0, 0, 255)  # 빨강
 
while True:
    success, frame = cap.read()
 
    if not success:
        break
 
    frame = cv2.flip(frame, 1)
 
    h, w, c = frame.shape
 
    if canvas is None:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
 
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
 
    results = hands.process(rgb)
 
    if results.multi_hand_landmarks:
 
        for hand_landmarks in results.multi_hand_landmarks:
 
            # 검지 끝
            index_tip = hand_landmarks.landmark[8]
 
            # 검지 관절
            index_pip = hand_landmarks.landmark[6]
 
            # 중지 끝
            middle_tip = hand_landmarks.landmark[12]
 
            # 중지 관절
            middle_pip = hand_landmarks.landmark[10]
 
            ix = int(index_tip.x * w)
            iy = int(index_tip.y * h)
 
            # 손가락 펴짐 여부
            index_up = index_tip.y < index_pip.y
            middle_up = middle_tip.y < middle_pip.y
 
            # --------------------
            # 그리기 모드
            # 검지만 펴짐
            # --------------------
            if index_up and not middle_up:
 
                cv2.circle(frame, (ix, iy), 10, draw_color, -1)
 
                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = ix, iy
 
                cv2.line(
                    canvas,
                    (prev_x, prev_y),
                    (ix, iy),
                    draw_color,
                    5
                )
 
                prev_x, prev_y = ix, iy
 
            # --------------------
            # 선택 모드
            # 검지+중지
            # --------------------
            elif index_up and middle_up:
 
                prev_x, prev_y = 0, 0
 
                cv2.rectangle(frame, (0, 0), (120, 60), (0, 0, 255), -1)
                cv2.rectangle(frame, (130, 0), (250, 60), (0, 255, 0), -1)
                cv2.rectangle(frame, (260, 0), (380, 60), (255, 0, 0), -1)
                cv2.rectangle(frame, (390, 0), (520, 60), (255, 255, 255), -1)
 
                if iy < 60:
 
                    if ix < 120:
                        draw_color = (0, 0, 255)
 
                    elif ix < 250:
                        draw_color = (0, 255, 0)
 
                    elif ix < 380:
                        draw_color = (255, 0, 0)
 
                    elif ix < 520:
                        canvas[:] = 0
 
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
 
    # ----------------------------
    # 캔버스 합성
    # ----------------------------
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
 
    _, inv = cv2.threshold(
        gray,
        20,
        255,
        cv2.THRESH_BINARY_INV
    )
 
    inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
 
    frame = cv2.bitwise_and(frame, inv)
    frame = cv2.bitwise_or(frame, canvas)
 
    cv2.putText(
        frame,
        "INDEX = DRAW",
        (10, h - 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
 
    cv2.putText(
        frame,
        "INDEX + MIDDLE = SELECT",
        (10, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
 
    cv2.imshow("Air Drawing", frame)
 
    key = cv2.waitKey(1)
 
    if key == 27:  # ESC
        break
 
cap.release()
cv2.destroyAllWindows()