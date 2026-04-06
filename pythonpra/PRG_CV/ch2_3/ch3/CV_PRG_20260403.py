import cv2
import numpy as np

# 1. 원본 이미지 불러오기
# 이미지 경로를 실제 파일 위치로 수정해주세요.
img = cv2.imread('ch2_3/ch3/rose.png')

if img is None:
    print("이미지를 불러올 수 없습니다. 경로를 확인해주세요.")
else:
     # 2. [기하학적 변환] 이미지 사이즈 50% 축소
     # dsize=(0,0)으로 설정하고 fx, fy 비율을 0.5로 주면 정확히 반으로 줄어듭니다.
     dst_resized = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

     # 3. [기하학적 변환 2] 시계방향으로 30도 회전
     h, w = dst_resized.shape[:2]
     center = (w // 2, h // 2)

     # getRotationMatrix2D(중심점, 각도, 배율)
     # OpenCV는 반시계방향이 (+), 시계방향이 (-)입니다. 따라서 -30을 입력합니다.
     matrix = cv2.getRotationMatrix2D(center, -30, 1.0)

     # warpAffine을 통해 실제 회전을 적용합니다.
     dst_rotated = cv2.warpAffine(dst_resized, matrix, (w, h))

     # 5. 결과 화면 출력
     cv2.imshow('Original', img)                      # 원본
     cv2.imshow('Resized 50%', dst_resized)           # 50% 축소
     cv2.imshow('Rotated 30', dst_rotated)            # 변환 결과

     print("화면의 창을 클릭하고 아무 키나 누르면 프로그램이 종료됩니다.")
     cv2.waitKey(0)
     cv2.destroyAllWindows()