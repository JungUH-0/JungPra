from tensorflow import keras
import numpy as np
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras import layers
import os
import random
import cv2 as cv

# 1. 절대 경로 설정 및 기본 하이퍼파라미터 정의
input_dir = r'D:\JungPra\pythonpra\PRG_CV\ch9\datasets\oxford_pets\images\images'
target_dir = r'D:\JungPra\pythonpra\PRG_CV\ch9\datasets\oxford_pets\annotations\annotations\trimaps'
img_siz = (160, 160)   # 모델에 입력되는 영상 크기
n_class = 3           # 분할 레이블 (0:물체, 1:배경, 2:경계)
batch_siz = 32        # 미니 배치 크기

# 대소문자(.jpg/.JPG) 및 파일 유효성 예외 처리 포함하여 파일 로드
img_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.jpg')])
label_paths = sorted([os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith('.png') and not f.startswith('.')])

# 2. Keras 3 규격 데이터셋 구현 (PyDataset 상속으로 수정)
class OxfordPets(keras.utils.PyDataset):
    def __init__(self, batch_size, img_size, img_paths, label_paths, **kwargs):
        super().__init__(**kwargs)  # Keras 3 가이드라인 준수
        self.batch_size = batch_size
        self.img_size = img_size
        self.img_paths = img_paths
        self.label_paths = label_paths

    def __len__(self):
        import math
        return math.ceil(len(self.label_paths) / self.batch_size)

    def __getitem__(self, idx):
        i = idx * self.batch_size
        batch_img_paths = self.img_paths[i : i + self.batch_size]
        batch_label_paths = self.label_paths[i : i + self.batch_size]
        
        # 실제 가져온 데이터 크기에 맞게 동적으로 배치 크기 조절 (마지막 남는 배치 예외 방지)
        actual_batch_size = len(batch_img_paths)
        
        x = np.zeros((actual_batch_size,) + self.img_size + (3,), dtype="float32")
        for j, path in enumerate(batch_img_paths):
            img = load_img(path, target_size=self.img_size)
            x[j] = img
            
        y = np.zeros((actual_batch_size,) + self.img_size + (1,), dtype="uint8")
        for j, path in enumerate(batch_label_paths):
            img = load_img(path, target_size=self.img_size, color_mode="grayscale")
            y[j] = np.expand_dims(img, 2)
            y[j] -= 1     # 부류 번호를 1,2,3에서 0,1,2로 변환
            
        return x, y

# 3. U-Net 신경망 모델 설계 설계 함수
def make_model(img_size, num_classes):
    inputs = keras.Input(shape=img_size + (3,))

    # U-net의 다운 샘플링(축소 경로)
    x = layers.Conv2D(32, 3, strides=2, padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    previous_block_activation = x     # 지름길 연결을 위해

    for filters in [64, 128, 256]:
        x = layers.Activation('relu')(x)
        x = layers.SeparableConv2D(filters, 3, padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        x = layers.SeparableConv2D(filters, 3, padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D(3, strides=2, padding='same')(x)
        residual = layers.Conv2D(filters, 1, strides=2, padding='same')(previous_block_activation)
        x = layers.add([x, residual])  # 지름길 연결  
        previous_block_activation = x # 지름길 연결을 위해

    # U-net의 업 샘플링(확대 경로)
    for filters in [256, 128, 64, 32]:
        x = layers.Activation('relu')(x)
        x = layers.Conv2DTranspose(filters, 3, padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        x = layers.Conv2DTranspose(filters, 3, padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.UpSampling2D(2)(x)
        residual = layers.UpSampling2D(2)(previous_block_activation)
        residual = layers.Conv2D(filters, 1, padding='same')(residual)
        x = layers.add([x, residual])  # 지름길 연결
        previous_block_activation = x # 지름길 연결을 위해

    outputs = layers.Conv2D(num_classes, 3, activation='softmax', padding='same')(x)
    model = keras.Model(inputs, outputs)  # 모델 생성
    return model

# 모델 빌드
model = make_model(img_siz, n_class)

# 4. 데이터 셔플 및 트레이닝/테스트 셋 분할
# 시드가 고정되어 마스크와 쌍이 완벽히 맞도록 처리
random.Random(1).shuffle(img_paths)
random.Random(1).shuffle(label_paths)

test_samples = int(len(img_paths) * 0.1)    # 10%를 테스트 집합으로 사용
train_img_paths = img_paths[:-test_samples]
train_label_paths = label_paths[:-test_samples]
test_img_paths = img_paths[-test_samples:]
test_label_paths = label_paths[-test_samples:]

# 데이터셋 객체 선언
train_gen = OxfordPets(batch_siz, img_siz, train_img_paths, train_label_paths)
test_gen = OxfordPets(batch_siz, img_siz, test_img_paths, test_label_paths)

# 5. 모델 컴파일 및 학습 진행
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Keras 3 가이드라인에 따른 최적 포맷 파일명 지정 (.keras 권장)
cb = [keras.callbacks.ModelCheckpoint('oxford_seg.keras', save_best_only=True)] 

print("데이터가 성공적으로 준비되었습니다. 학습을 시작합니다...")
print("★ 탐색할 이미지 폴더 주소:", input_dir)
print("★ 탐색할 레이블 폴더 주소:", target_dir)
print("----------------------------------------")
print("★ 읽어온 원본 이미지(.jpg) 개수:", len(img_paths))
print("★ 읽어온 레이블 이미지(.png) 개수:", len(label_paths))
print("----------------------------------------")
model.fit(train_gen, epochs=30, validation_data=test_gen, callbacks=cb)

# 6. 예측 및 OpenCV 시각화 (타입 변환 에러 예방 코드 추가)
preds = model.predict(test_gen)

# 0번 예측 결과 채널 축 가작 큰 인덱스 추출 (Softmax 확률값 -> 0, 1, 2 클래스 정수 변환)
pred_mask = np.argmax(preds[0], axis=-1)
pred_mask = np.expand_dims(pred_mask, axis=-1)
pred_mask = pred_mask.astype("uint8") # OpenCV 출력을 위해 데이터타입 일치

# 원본 테스트 이미지와 정답 이미지 로드
disp_img = cv.imread(test_img_paths[0])
disp_img = cv.resize(disp_img, img_siz)

disp_label = cv.imread(test_label_paths[0], cv.IMREAD_GRAYSCALE)
disp_label = cv.resize(disp_label, img_siz)

# 화면에 표시하기 좋게 픽셀값 크기 키우기 (0,1,2 -> 0, 85, 170 등으로 가시성 확보)
cv.imshow('Sample image', disp_img)
cv.imshow('Segmentation label', disp_label * 64)
cv.imshow('Segmentation prediction', pred_mask * 64)

print("시각화 창이 열렸습니다. 터미널 창에서 창을 닫으려면 아무 키나 누르세요.")
cv.waitKey(0)
cv.destroyAllWindows()

