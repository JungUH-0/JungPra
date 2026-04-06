import cv2
import numpy as np
import math

# 1. 이미지 로드
src = cv2.imread('ch2_3/ch3/rose.png')
if src is None:
    print("이미지를 찾을 수 없습니다.")
else:
    # 2. 50% 리사이즈
    dst_resized = cv2.resize(src, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    h, w = dst_resized.shape[:2]
    cx, cy = w / 2, h / 2  # 중심점

    # 3. 시계방향 30도를 라디안으로 변환
    angle = math.radians(-30) # 시계방향은 음수
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # 4. 동차 행렬(Homogeneous Matrix) 직접 구성 (3x3)
    # T1: 중심을 원점으로 이동 -> R: 회전 -> T2: 다시 원래 위치로 이동
    # 이 세 단계를 하나로 합친 최종 아핀 행렬 계산식입니다.
    
    # matrix = [ cos  sin  tx ]
    #          [ -sin cos  ty ]
    tx = (1 - cos_a) * cx - sin_a * cy
    ty = sin_a * cx + (1 - cos_a) * cy
    
    # OpenCV의 warpAffine은 2x3 행렬을 받으므로 마지막 행 [0, 0, 1]은 제외하고 정의합니다.
    homogeneous_matrix = np.array([
        [cos_a, sin_a, tx],
        [-sin_a, cos_a, ty]
    ], dtype=np.float32)

    # 5. 변환 적용
    dst_rotated = cv2.warpAffine(dst_resized, homogeneous_matrix, (w, h))

    # 6. 결과 출력
    cv2.imshow('1. Original', src)
    cv2.imshow('2. Resized 50%', dst_resized)
    cv2.imshow('3. Homogeneous Rotation', dst_rotated)

    cv2.waitKey(0)
    cv2.destroyAllWindows()