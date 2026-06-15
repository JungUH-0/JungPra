import numpy as np
import cv2 as cv
import sys

def draw_OpticalFlow(img, flow, step=16):
    # frame.shape를 사용하기 위해 frame을 인자로 전달하거나, 함수 내에서 전역 변수를 참조해야 함
    # 여기서는 전역 변수 frame을 그대로 사용하는 구조 유지
    for y in range(step//2, frame.shape[0], step):
        for x in range(step//2, frame.shape[1], step):
            # 오류 수정: np.int 대신 int 사용
            dx, dy = flow[y, x].astype(int)
            if (dx*dx + dy*dy) > 1:
                cv.line(img, (x, y), (x+dx, y+dy), (0, 0, 255), 2) # 큰 모션은 빨간색
            else:
                cv.line(img, (x, y), (x+dx, y+dy), (0, 255, 0), 2) # 작은 모션은 초록색
    
cap = cv.VideoCapture(0, cv.CAP_DSHOW) # 카메라와 연결 시도
if not cap.isOpened(): sys.exit('카메라 연결 실패')
    
prev = None

while(1):
    ret, frame = cap.read()    # 비디오를 구성하는 프레임 획득
    # 오류 수정: sys()가 아닌 sys.exit() 사용
    if not ret: 
        print('프레임 획득에 실패하여 루프를 나갑니다.')
        break
    
    if prev is None:    # 첫 프레임이면 광류 계산 없이 prev만 설정
        prev = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        continue
    
    curr = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    flow = cv.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    draw_OpticalFlow(frame, flow)
    cv.imshow('Optical flow', frame)

    prev = curr

    key = cv.waitKey(1)   # 1밀리초 동안 키보드 입력 기다림
    if key == ord('q'):   # 'q' 키가 들어오면 루프를 빠져나감
        break 
    
cap.release()           # 카메라와 연결을 끊음
cv.destroyAllWindows()