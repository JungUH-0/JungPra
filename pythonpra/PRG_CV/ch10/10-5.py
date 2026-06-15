import cv2 as cv
import mediapipe as mp
import time

fps = 0
prev_time = time.time()

mp_face_detection=mp.solutions.face_detection
mp_drawing=mp.solutions.drawing_utils

face_detection=mp_face_detection.FaceDetection(model_selection=1,min_detection_confidence=0.5)

cap=cv.VideoCapture(0,cv.CAP_DSHOW)

while True:
    ret,frame=cap.read()
    if not ret:
        print('프레임 획득에 실패하여 루프를 나갑니다.')
        break

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    res=face_detection.process(cv.cvtColor(frame,cv.COLOR_BGR2RGB))
    
    if res.detections:
        for detection in res.detections:
            mp_drawing.draw_detection(frame,detection)
    
    cv.putText(frame, f'FPS: {fps:.1f}', (10, 30),
               cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
    cv.imshow('MediaPipe Face Detection from video',cv.flip(frame,1))
    if cv.waitKey(5)==ord('q'):
        break



cap.release()
cv.destroyAllWindows()