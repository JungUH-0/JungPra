import os
import cv2
import numpy as np  # 🌟 한글 경로 처리를 위해 넘파이를 가져옵니다.

# 경로 설정
BASE_DIR = r"D:\JungPra\pythonpra\signlan"
SRC_IMG_DIR = os.path.join(BASE_DIR, "downloaded_images")
DIST_IMG_DIR = os.path.join(BASE_DIR, "preprocessed_images")

os.makedirs(DIST_IMG_DIR, exist_ok=True)

# AI 모델 표준 이미지 규격
TARGET_SIZE = (224, 224)

def preprocess_all_images():
    image_files = [f for f in os.listdir(SRC_IMG_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    if not image_files:
        print("ℹ️ 원본 폴더에 이미지 파일이 없습니다.")
        return

    print(f"🚀 총 {len(image_files)}개의 이미지 전처리를 시작합니다 (한글 경로 버그 수정판)...")

    for img_name in image_files:
        src_path = os.path.join(SRC_IMG_DIR, img_name)
        dist_path = os.path.join(DIST_IMG_DIR, img_name)

        # 🌟 1. [수정] 한글 경로용 imread 우회법
        # 파일을 바이너리 배열로 먼저 읽어온 후, OpenCV 행렬로 디코딩합니다.
        img_array = np.fromfile(src_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            print(f"  ❌ 이미지 로드 실패: {img_name}")
            continue

        # 2. 이미지 크기 조절 (Resize)
        resized_img = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)

        # 3. 흑백 변환 (GrayScale)
        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

        # 🌟 4. [수정] 한글 경로용 imwrite 우회법
        # OpenCV 이미지를 메모리 버퍼로 인코딩한 뒤, 파이썬 파일 쓰기로 안전하게 저장합니다.
        _, img_encoded = cv2.imencode('.jpg', gray_img)
        img_encoded.tofile(dist_path)
        
        print(f"  ✅ 전처리 완료: {img_name} ({TARGET_SIZE[0]}x{TARGET_SIZE[1]} 흑백)")

    print("\n🎉 모든 이미지 가공이 완료되었습니다!")
    print(f"📂 결과 확인 폴더: {DIST_IMG_DIR}")

if __name__ == "__main__":
    preprocess_all_images()