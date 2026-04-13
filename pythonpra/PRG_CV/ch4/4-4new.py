# import cv2 as cv
# import numpy as np

# # 1. 이미지 로드
# img = cv.imread('ch4/apples.jpg')

# if img is None:
#     print("이미지를 찾을 수 없습니다. 경로를 다시 확인하세요.")
# else:
#     # 2. 전처리: 노이즈 제거를 위한 블러링 (매우 중요!)
#     # 사과 표면의 질감이나 잎사귀 때문에 원이 잘못 잡히는 것을 방지합니다.
#     blurred = cv.medianBlur(img, 5) 
#     gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)

#     # 3. 허프 원 변환 파라미터 조정
#     # minDist(200): 원 중심 사이의 최소 거리. 사과들이 모여있으므로 조금 줄여보세요.
#     # param2: 원 검출 임계값. 너무 낮으면 가짜 원이 많이 생기고, 높으면 못 찾습니다.
#     apples = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, minDist=150,
#                               param1=100, param2=35, minRadius=50, maxRadius=150)

#     if apples is not None:
#         apples = np.uint16(np.around(apples))
#         for i in apples[0, :]:
#             # 중심 그리기
#             cv.circle(img, (i[0], i[1]), 2, (0, 255, 0), 3)
#             # 원 둘레 그리기 (파란색)
#             cv.circle(img, (i[0], i[1]), i[2], (255, 0, 0), 3)

#     cv.imshow('Apple detection', img)
#     cv.waitKey(0)
#     cv.destroyAllWindows()

# import cv2 as cv
# import numpy as np

# img = cv.imread('ch4/apples.jpg')
# if img is None: exit()

# # 1. HSV 색 공간으로 변환
# hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

# # 2. 빨간색 범위 설정 (빨간색은 HSV에서 양 끝단에 걸쳐 있어 두 범위를 합칩니다)
# lower_red1 = np.array([0, 100, 100])
# upper_red1 = np.array([10, 255, 255])
# lower_red2 = np.array([160, 100, 100])
# upper_red2 = np.array([180, 255, 255])

# mask1 = cv.inRange(hsv, lower_red1, upper_red1)
# mask2 = cv.inRange(hsv, lower_red2, upper_red2)
# red_mask = mask1 + mask2

# # 3. 노이즈 제거 (모폴로지 연산)
# kernel = np.ones((5,5), np.uint8)
# red_mask = cv.morphologyEx(red_mask, cv.MORPH_OPEN, kernel)
# red_mask = cv.dilate(red_mask, kernel, iterations=1)

# # 4. 빨간색 영역만 남긴 이미지 생성 및 그레이스케일 변환
# res = cv.bitwise_and(img, img, mask=red_mask)
# gray = cv.cvtColor(res, cv.COLOR_BGR2GRAY)
# gray = cv.GaussianBlur(gray, (9, 9), 2)

# # 5. 허프 원 변환 (파라미터 미세 조정)
# # param2를 조금 낮춰도 이미 빨간색만 남겼기 때문에 정확도가 높습니다.
# apples = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, minDist=100,
#                           param1=50, param2=25, minRadius=40, maxRadius=150)

# if apples is not None:
#     apples = np.uint16(np.around(apples))
#     for i in apples[0, :]:
#         # 빨간색 마스크 안의 픽셀인지 한 번 더 확인 (선택 사항)
#         if red_mask[i[1], i[0]] > 0:
#             cv.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 3) # 검출된 사과는 녹색 원으로 표시

# cv.imshow('Red Mask', red_mask) # 사과 영역만 하얗게 보임
# cv.imshow('Advanced Apple Detection', img)
# cv.waitKey(0)
# cv.destroyAllWindows()

# import cv2 as cv
# import numpy as np

# img = cv.imread('ch4/apples.jpg')
# if img is None: exit()

# # 1. 가우시안 블러로 이미지 결을 부드럽게 (원 인식률 상승)
# blurred = cv.GaussianBlur(img, (5, 5), 0)

# # 2. HSV 색상 추출 (범위를 더 넓게 잡았습니다)
# hsv = cv.cvtColor(blurred, cv.COLOR_BGR2HSV)

# # 빨간색의 두 영역을 합침 (채도와 명도의 하한선을 50으로 낮춰서 더 많은 영역 포함)
# lower_red1 = np.array([0, 50, 50])
# upper_red1 = np.array([15, 255, 255])
# lower_red2 = np.array([160, 50, 50])
# upper_red2 = np.array([180, 255, 255])

# mask = cv.inRange(hsv, lower_red1, upper_red1) | cv.inRange(hsv, lower_red2, upper_red2)

# # 3. 모폴로지 '닫기(Close)' 연산: 사과 안의 빈틈(구멍)을 채워줌
# kernel = np.ones((7, 7), np.uint8)
# mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

# # 4. 원 검출은 그레이스케일이 아닌 '마스크 이미지' 자체에서 수행
# # 흰색(사과)과 검은색(배경)이 극명해서 원을 훨씬 잘 찾습니다.
# circles = cv.HoughCircles(mask, cv.HOUGH_GRADIENT, 1, minDist=80,
#                            param1=100, param2=15, minRadius=40, maxRadius=150)

# if circles is not None:
#     circles = np.uint16(np.around(circles))
#     for i in circles[0, :]:
#         # 원본 이미지에 표시
#         cv.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 3)
#         cv.circle(img, (i[0], i[1]), 2, (255, 0, 0), 3)

# cv.imshow('Mask used for Detection', mask) # 이 화면에서 사과가 꽉 찬 흰색 원으로 보여야 합니다.
# cv.imshow('Final Result', img)
# cv.waitKey(0)
# cv.destroyAllWindows()

# import cv2 as cv
# import numpy as np

# img = cv.imread('ch4/apples.jpg')
# if img is None: exit()

# # 1. 전처리 (허프 변환의 성능은 블러가 결정합니다)
# # 가우시안 블러로 잎사귀의 날카로운 엣지를 지워야 나뭇잎 오인식을 막습니다.
# blurred = cv.GaussianBlur(img, (9, 9), 2)
# gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)

# # 2. 허프 원 변환 (파라미터 끝장 튜닝)
# # minDist=60: 사과들이 겹쳐 있으므로 최소 거리를 대폭 줄임
# # param1=150: 엣지 검출 임계값 (기본값 수준)
# # param2=25: 가장 중요한 값! 20은 너무 많고 35는 너무 적으니 25로 타협
# # minRadius/maxRadius: 사진 속 사과 크기에 맞게 범위 확장
# # 이 라인을 아래 수치로 바꿔보세요!
# apples = cv.HoughCircles(
#     gray, 
#     cv.HOUGH_GRADIENT, 
#     1, 
#     minDist=100,    # 1. 원 사이의 최소 거리 증가 (겹침 방지)
#     param1=150, 
#     param2=31,     # 2. 원 인식 기준 상향 (나뭇잎 오인식 방지)
#     minRadius=40,  # 3. 너무 작은 원 무시
#     maxRadius=150
# )

# if apples is not None:
#     apples = np.uint16(np.around(apples))
#     for i in apples[0, :]:
#         # 원 그리기
#         cv.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 3)
#         # 중심점 그리기
#         cv.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)

# # 인식된 개수 출력
# count = 0 if apples is None else len(apples[0])
# print(f"검출된 사과 개수: {count}")

# cv.imshow('Hough Circles Only', img)
# cv.waitKey(0)
# cv.destroyAllWindows()

# import cv2 as cv
# import numpy as np

# img = cv.imread('ch4/apples.jpg')

# # 1. 블러를 더 강하게! (나뭇잎의 날카로운 선을 아예 뭉개버립니다)
# # 나뭇잎의 엣지가 사과보다 선명해서 생기는 문제이므로, 더 많이 뭉개야 합니다.
# blurred = cv.GaussianBlur(img, (21, 21), 0) 
# gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)

# # 2. 허프 변환 파라미터 재설정
# apples = cv.HoughCircles(
#     gray, 
#     cv.HOUGH_GRADIENT, 
#     1, 
#     minDist=120,    # 1. 거리를 더 늘려서 사과 하나당 '딱 하나'만 잡히게 함
#     param1=100,     # Canny 엣지 임계값
#     param2=21,      # 2. 기준을 아주 살짝만 높여서 나뭇잎 탈락 유도
#     minRadius=60,   # 3. 최소 반지름을 키워서 사과 내부의 작은 원들 제거
#     maxRadius=150
# )

# if apples is not None:
#     apples = np.uint16(np.around(apples))
#     for i in apples[0, :]:
#         cv.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 3)
#         cv.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)

#  # 인식된 개수 출력
# count = 0 if apples is None else len(apples[0])
# print(f"검출된 사과 개수: {count}")


# cv.imshow('Final Tuning', img)
# cv.waitKey(0)
# cv.destroyAllWindows()

import cv2 as cv
import numpy as np

img = cv.imread('ch4/apples.jpg')

# 1. [강력 필터] Bilateral Filter
# 가우시안 블러와 달리 엣지(테두리)를 파괴하지 않으면서 면의 노이즈만 밀어버립니다.
# 나뭇잎의 결을 지우는 데 탁월합니다.
dst = cv.bilateralFilter(img, d=15, sigmaColor=75, sigmaSpace=75)

# 2. 그레이스케일 변환 및 모폴로지 연산
gray = cv.cvtColor(dst, cv.COLOR_BGR2GRAY)

# [추가 필터] 닫기(Close) 연산으로 사과 내부의 어두운 점이나 반사광 노이즈를 메웁니다.
kernel = np.ones((5,5), np.uint8)
gray = cv.morphologyEx(gray, cv.MORPH_CLOSE, kernel)

# 3. 허프 변환 파라미터 최적화 (이 수치가 핵심입니다)
apples = cv.HoughCircles(
    gray, 
    cv.HOUGH_GRADIENT, 
    dp=1.2,          # 해상도 비율을 살짝 높여 더 정밀하게 찾음
    minDist=160,     # 중복 방지를 위해 거리를 더 확보
    param1=78,       # 엣지 검출 강도를 낮춰 흐릿한 사과도 포함
    param2=28,       # 필터링이 강력하므로 문턱값을 28 정도로 높여 오탐지 제거
    minRadius=65,    # 나뭇잎 조각들이 잡히지 않도록 최소 크기 상향
    maxRadius=145
)

if apples is not None:
    apples = np.uint16(np.around(apples))
    for i in apples[0, :]:
        # 초록색 원으로 검출 표시
        cv.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 3)
        # 중심점 표시
        cv.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)

#  # 인식된 개수 출력
count = 0 if apples is None else len(apples[0])
print(f"검출된 사과 개수: {count}")

cv.imshow('Powerful Filter Result', img)
cv.waitKey(0)
cv.destroyAllWindows()