# import cv2 as cv
# import numpy as np

# # 1. 원본 이미지 로드
# img_color = cv.imread('apples.jpg') # 이미지 파일명을 확인하세요. (image_4.png -> apple.jpg)

# # 2. 전처리: Grayscale 변환 (에지 검출은 밝기 변화 기반이므로 컬러 정보가 불필요)
# img_gray = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)

# # 3. 전처리: 가우시안 블러 (노이즈 제거, 에지 검출 성능 향상)
# img_blur = cv.GaussianBlur(img_gray, (3, 3), 0)

# # ------------------------------------------------------------------
# # [Sobel 에지 검출기]
# # ------------------------------------------------------------------
# # x축 및 y축 방향의 밝기 변화량 계산 (1차 미분)
# sobel_x = cv.Sobel(img_blur, cv.CV_64F, 1, 0, ksize=3)
# sobel_y = cv.Sobel(img_blur, cv.CV_64F, 0, 1, ksize=3)

# # 두 방향의 변화량을 합쳐 최종 에지 강도 계산
# sobel_abs_x = cv.convertScaleAbs(sobel_x)
# sobel_abs_y = cv.convertScaleAbs(sobel_y)
# img_sobel = cv.addWeighted(sobel_abs_x, 0.5, sobel_abs_y, 0.5, 0)

# # ------------------------------------------------------------------
# # [Canny 에지 검출기]
# # ------------------------------------------------------------------
# # Canny(이미지, 하한 임계값, 상한 임계값)
# # 임계값 조절을 통해 에지의 세밀함을 제어할 수 있습니다.
# img_canny = cv.Canny(img_blur, 50, 150)

# # ------------------------------------------------------------------
# # [결과 시각화]
# # ------------------------------------------------------------------
# # 결과 이미지를 한 창에 나란히 배치하기 위해 크기 조절 및 병합
# res_sobel_resized = cv.resize(img_sobel, (img_color.shape[1]//2, img_color.shape[0]//2))
# res_canny_resized = cv.resize(img_canny, (img_color.shape[1]//2, img_color.shape[0]//2))

# res_combined = np.hstack((res_sobel_resized, res_canny_resized))

# # 결과 출력
# cv.imshow('Sobel (Left) vs Canny (Right) Edge Detection', res_combined)
# cv.waitKey(0)
# cv.destroyAllWindows()
import cv2 as cv
import numpy as np

# 1. 이미지 로드 (파일명이 apples.jpg인지 꼭 확인하세요!)
img = cv.imread('apples.jpg')

if img is None:
    print("파일을 찾을 수 없습니다. 경로와 파일명을 확인해주세요.")
else:
    # 2. 전처리 (그레이스케일 및 블러)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (3, 3), 0)

    # 3. Sobel 에지 검출
    grad_x = cv.Sobel(blur, cv.CV_64F, 1, 0, ksize=3)
    grad_y = cv.Sobel(blur, cv.CV_64F, 0, 1, ksize=3)
    abs_grad_x = cv.convertScaleAbs(grad_x)
    abs_grad_y = cv.convertScaleAbs(grad_y)
    sobel_res = cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    # 4. Canny 에지 검출
    canny_res = cv.Canny(blur, 50, 150)

    # 5. 경계선 영상 생성 (Canny 에지를 원본 위에 붉은색으로 덧씌움)
    boundary_res = img.copy()
    boundary_res[canny_res == 255] = [0, 0, 255] # BGR 순서 (빨간색)

    # 6. 화면 출력을 위해 크기 조절 (너무 클 수 있으므로)
    h, w = img.shape[:2]
    shrink = cv.resize(img, (w//2, h//2))
    sobel_shrink = cv.resize(sobel_res, (w//2, h//2))
    canny_shrink = cv.resize(canny_res, (w//2, h//2))
    boundary_shrink = cv.resize(boundary_res, (w//2, h//2))

    # 7. 결과 합치기 (원본, 소벨, 캐니, 경계선영상)
    # 소벨과 캐니는 1채널이므로 컬러(3채널)로 변환 후 합쳐야 합니다.
    sobel_color = cv.cvtColor(sobel_shrink, cv.COLOR_GRAY2BGR)
    canny_color = cv.cvtColor(canny_shrink, cv.COLOR_GRAY2BGR)
    
    top_row = np.hstack((shrink, sobel_color))
    bottom_row = np.hstack((canny_color, boundary_shrink))
    full_res = np.vstack((top_row, bottom_row))

    cv.imshow('Comparison: Original | Sobel | Canny | Boundary', full_res)
    cv.waitKey(0)
    cv.destroyAllWindows()