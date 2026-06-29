# import os
# import cv2
# import numpy as np
# import mediapipe as mp
# from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
# from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
# from mediapipe.tasks.python.core.base_options import BaseOptions

# # ──────────────────────────────────────────────
# # 설정값
# # ──────────────────────────────────────────────
# BASE_DIR       = r"D:\JungPra\pythonpra\signlan"
# CONS_SRC_DIR   = os.path.join(BASE_DIR, "myconsonant")   # 자음 원본 영상
# VOWEL_SRC_DIR  = os.path.join(BASE_DIR, "myvowel")       # 모음 원본 영상
# KOR_DIST_DIR   = os.path.join(BASE_DIR, "kor_preprocessed")  # npy 저장
# MODEL_PATH     = os.path.join(BASE_DIR, "hand_landmarker.task")

# os.makedirs(KOR_DIST_DIR, exist_ok=True)

# FRAME_INTERVAL = 1
# MAX_FRAMES     = 30
# LANDMARK_DIM   = 42  # x,y × 21관절 (SignBridge 형식)

# # Vector+Angle 상수
# BONE_CONNECTIONS = [
#     (0,1),(1,2),(2,3),(3,4),
#     (0,5),(5,6),(6,7),(7,8),
#     (0,9),(9,10),(10,11),(11,12),
#     (0,13),(13,14),(14,15),(15,16),
#     (0,17),(17,18),(18,19),(19,20),
# ]
# ANGLE_PAIRS = [
#     (0,1),(1,2),(2,3),
#     (4,5),(5,6),(6,7),
#     (8,9),(9,10),(10,11),
#     (12,13),(13,14),(14,15),
#     (16,17),(17,18),(18,19),
# ]


# def init_detector():
#     if not os.path.exists(MODEL_PATH):
#         raise FileNotFoundError(f"❌ 모델 파일 없음: {MODEL_PATH}")
#     options = HandLandmarkerOptions(
#         base_options=BaseOptions(model_asset_path=MODEL_PATH),
#         running_mode=VisionTaskRunningMode.IMAGE,
#         num_hands=2,
#         min_hand_detection_confidence=0.3,
#         min_hand_presence_confidence=0.3,
#     )
#     return HandLandmarker.create_from_options(options)


# def extract_landmarks(frame, detector):
#     """오른손 우선 x,y 42개 추출"""
#     rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
#     result   = detector.detect(mp_image)

#     coords   = np.zeros(42, dtype=np.float32)
#     detected = False

#     if result.hand_landmarks and result.handedness:
#         right_lm = None
#         left_lm  = None
#         for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
#             if handedness[0].category_name == "Right":
#                 right_lm = hand_lm
#             else:
#                 left_lm  = hand_lm

#         target = right_lm if right_lm is not None else left_lm
#         if target is not None:
#             coords   = np.array([[lm.x, lm.y] for lm in target], dtype=np.float32).flatten()
#             detected = True

#     return coords, detected


# def extract_vector_angle(coords_42):
#     """42차원 x,y → 55차원 방향벡터+각도 변환"""
#     points       = coords_42.reshape(21, 2)
#     bone_vectors = np.array(
#         [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
#         dtype=np.float32,
#     )
#     lengths      = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
#     unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)

#     angles = []
#     for first_idx, second_idx in ANGLE_PAIRS:
#         v1  = unit_vectors[first_idx]
#         v2  = unit_vectors[second_idx]
#         dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
#         angles.append(np.arccos(dot) / np.pi)

#     return np.concatenate([unit_vectors.flatten(), np.array(angles, dtype=np.float32)])


# def preprocess_folder(src_dir, detector, label):
#     """폴더 안의 영상들 전처리"""
#     video_files = [
#         f for f in os.listdir(src_dir)
#         if f.lower().endswith(('.mp4', '.avi', '.mov'))
#     ]

#     ok = fail = 0

#     for video_name in sorted(video_files):
#         video_path = os.path.join(src_dir, video_name)
#         word_name  = os.path.splitext(video_name)[0]
#         save_path  = os.path.join(KOR_DIST_DIR, f"{word_name}.npy")

#         if os.path.exists(save_path):
#             print(f"  ⏭️  [{word_name}] 이미 존재, 건너뜀")
#             ok += 1
#             continue

#         print(f"  🎬 [{word_name}] 추출 중...")

#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             print(f"    ❌ 영상 열기 실패")
#             fail += 1
#             continue

#         frame_count  = 0
#         landmark_seq = []

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break
#             if frame_count % FRAME_INTERVAL == 0:
#                 coords, detected = extract_landmarks(frame, detector)
#                 if detected:
#                     # Vector+Angle 변환
#                     features = extract_vector_angle(coords)
#                     landmark_seq.append(features)
#             frame_count += 1

#         cap.release()

#         if not landmark_seq:
#             print(f"    ❌ 손 감지 안됨")
#             fail += 1
#             continue

#         seq = np.array(landmark_seq, dtype=np.float32)

#         if len(seq) >= MAX_FRAMES:
#             idx = np.linspace(0, len(seq)-1, MAX_FRAMES, dtype=int)
#             seq = seq[idx]
#         else:
#             pad = np.zeros((MAX_FRAMES - len(seq), 55), dtype=np.float32)
#             seq = np.concatenate([seq, pad], axis=0)

#         np.save(save_path, seq)

#         hand_ratio = len(landmark_seq) / max(frame_count, 1) * 100
#         print(f"    ✅ 감지율: {hand_ratio:.0f}% → {word_name}.npy")
#         ok += 1

#     return ok, fail


# def preprocess_all():
#     print(f"🚀 자음/모음 전처리 시작 (Vector+Angle 55차원)")
#     detector = init_detector()
#     print(f"   ✅ 모델 로드 완료\n{'='*55}")

#     total_ok = total_fail = 0

#     # 자음 처리
#     if os.path.exists(CONS_SRC_DIR):
#         print(f"\n📂 자음 폴더 처리 중...")
#         ok, fail = preprocess_folder(CONS_SRC_DIR, detector, "자음")
#         total_ok += ok
#         total_fail += fail
#     else:
#         print(f"⚠️  자음 폴더 없음: {CONS_SRC_DIR}")

#     # 모음 처리
#     if os.path.exists(VOWEL_SRC_DIR):
#         print(f"\n📂 모음 폴더 처리 중...")
#         ok, fail = preprocess_folder(VOWEL_SRC_DIR, detector, "모음")
#         total_ok += ok
#         total_fail += fail
#     else:
#         print(f"⚠️  모음 폴더 없음: {VOWEL_SRC_DIR}")

#     detector.close()

#     print(f"\n{'='*55}")
#     print(f"📊 성공: {total_ok} | 실패: {total_fail}")
#     print(f"📂 저장 폴더: {KOR_DIST_DIR}")


# if __name__ == "__main__":
#     preprocess_all()


#---------------------------------------------------------
# 손바닥 손등 따로 인식을 위해 z축 추가
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.core.base_options import BaseOptions

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR       = r"D:\JungPra\pythonpra\signlan"
CONS_SRC_DIR   = os.path.join(BASE_DIR, "myconsonant")
VOWEL_SRC_DIR  = os.path.join(BASE_DIR, "myvowel")
KOR_DIST_DIR   = os.path.join(BASE_DIR, "kor_preprocessed")
MODEL_PATH     = os.path.join(BASE_DIR, "hand_landmarker.task")

os.makedirs(KOR_DIST_DIR, exist_ok=True)

FRAME_INTERVAL = 1
MAX_FRAMES     = 30
LANDMARK_DIM   = 63   # x,y,z × 21관절 (z축 추가!)

# Vector+Angle 상수 (63차원 기반)
BONE_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
]
ANGLE_PAIRS = [
    (0,1),(1,2),(2,3),
    (4,5),(5,6),(6,7),
    (8,9),(9,10),(10,11),
    (12,13),(13,14),(14,15),
    (16,17),(17,18),(18,19),
]


def init_detector():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"❌ 모델 파일 없음: {MODEL_PATH}")
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
    )
    return HandLandmarker.create_from_options(options)


def extract_landmarks(frame, detector):
    """
    오른손 우선, 없으면 왼손
    x,y,z × 21관절 = 63개 (z축 포함!)
    """
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    coords   = np.zeros(63, dtype=np.float32)
    detected = False

    if result.hand_landmarks and result.handedness:
        right_lm = None
        left_lm  = None
        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            if handedness[0].category_name == "Right":
                right_lm = hand_lm
            else:
                left_lm  = hand_lm

        target = right_lm if right_lm is not None else left_lm
        if target is not None:
            coords = np.array(
                [[lm.x, lm.y, lm.z] for lm in target],  # z축 추가
                dtype=np.float32
            ).flatten()  # 63개
            detected = True

    return coords, detected


def extract_vector_angle(coords_63):
    """
    63차원 x,y,z → 75차원 방향벡터+각도 변환
    방향벡터: 20개 × 3(x,y,z) = 60개
    각도:     15개
    총 75차원
    """
    points       = coords_63.reshape(21, 3)  # x,y,z
    bone_vectors = np.array(
        [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
        dtype=np.float32,
    )
    lengths      = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
    unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)

    angles = []
    for first_idx, second_idx in ANGLE_PAIRS:
        v1  = unit_vectors[first_idx]
        v2  = unit_vectors[second_idx]
        dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angles.append(np.arccos(dot) / np.pi)

    # 60개(방향벡터) + 15개(각도) = 75차원
    return np.concatenate([unit_vectors.flatten(), np.array(angles, dtype=np.float32)])


def preprocess_folder(src_dir, detector):
    video_files = [
        f for f in os.listdir(src_dir)
        if f.lower().endswith(('.mp4', '.avi', '.mov'))
    ]

    ok = fail = 0

    for video_name in sorted(video_files):
        video_path = os.path.join(src_dir, video_name)
        word_name  = os.path.splitext(video_name)[0]
        save_path  = os.path.join(KOR_DIST_DIR, f"{word_name}.npy")

        if os.path.exists(save_path):
            print(f"  ⏭️  [{word_name}] 이미 존재, 건너뜀")
            ok += 1
            continue

        print(f"  🎬 [{word_name}] 추출 중...")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"    ❌ 영상 열기 실패")
            fail += 1
            continue

        frame_count  = 0
        landmark_seq = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % FRAME_INTERVAL == 0:
                coords, detected = extract_landmarks(frame, detector)
                if detected:
                    features = extract_vector_angle(coords)
                    landmark_seq.append(features)
            frame_count += 1

        cap.release()

        if not landmark_seq:
            print(f"    ❌ 손 감지 안됨")
            fail += 1
            continue

        seq = np.array(landmark_seq, dtype=np.float32)

        if len(seq) >= MAX_FRAMES:
            idx = np.linspace(0, len(seq)-1, MAX_FRAMES, dtype=int)
            seq = seq[idx]
        else:
            pad = np.zeros((MAX_FRAMES - len(seq), 75), dtype=np.float32)
            seq = np.concatenate([seq, pad], axis=0)

        np.save(save_path, seq)

        hand_ratio = len(landmark_seq) / max(frame_count, 1) * 100
        print(f"    ✅ 감지율: {hand_ratio:.0f}% | shape: {seq.shape} → {word_name}.npy")
        ok += 1

    return ok, fail


def preprocess_all():
    print(f"🚀 자음/모음 전처리 시작 (z축 포함 Vector+Angle 75차원)")
    print(f"   x,y,z × 21관절 = 63차원 → Vector+Angle = 75차원")
    detector = init_detector()
    print(f"   ✅ 모델 로드 완료\n{'='*55}")

    total_ok = total_fail = 0

    if os.path.exists(CONS_SRC_DIR):
        print(f"\n📂 자음 폴더 처리 중...")
        ok, fail = preprocess_folder(CONS_SRC_DIR, detector)
        total_ok += ok
        total_fail += fail
    else:
        print(f"⚠️  자음 폴더 없음: {CONS_SRC_DIR}")

    if os.path.exists(VOWEL_SRC_DIR):
        print(f"\n📂 모음 폴더 처리 중...")
        ok, fail = preprocess_folder(VOWEL_SRC_DIR, detector)
        total_ok += ok
        total_fail += fail
    else:
        print(f"⚠️  모음 폴더 없음: {VOWEL_SRC_DIR}")

    detector.close()

    print(f"\n{'='*55}")
    print(f"📊 성공: {total_ok} | 실패: {total_fail}")
    print(f"📂 저장 폴더: {KOR_DIST_DIR}")


if __name__ == "__main__":
    preprocess_all()