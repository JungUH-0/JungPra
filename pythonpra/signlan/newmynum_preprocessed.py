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
SRC_VIDEO_DIR  = os.path.join(BASE_DIR, "mynum")
DIST_VIDEO_DIR = os.path.join(BASE_DIR, "newmynum_preprocessed")
MODEL_PATH     = os.path.join(BASE_DIR, "hand_landmarker.task")

os.makedirs(DIST_VIDEO_DIR, exist_ok=True)

FRAME_INTERVAL = 1
MAX_FRAMES     = 30
LANDMARK_DIM   = 42   # x,y × 21관절


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
    오른손 우선, 없으면 왼손 사용
    x,y × 21관절 = 42개
    """
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    coords   = np.zeros(21 * 2, dtype=np.float32)
    detected = False

    if result.hand_landmarks and result.handedness:
        right_lm = None
        left_lm  = None

        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            if handedness[0].category_name == "Right":
                right_lm = hand_lm
            else:
                left_lm = hand_lm

        # 오른손 우선, 없으면 왼손
        target = right_lm if right_lm is not None else left_lm

        if target is not None:
            coords = np.array(
                [[lm.x, lm.y] for lm in target],
                dtype=np.float32
            ).flatten()
            detected = True

    return coords, detected


def preprocess_all_videos():
    video_files = [
        f for f in os.listdir(SRC_VIDEO_DIR)
        if f.lower().endswith(('.mp4', '.avi', '.mov'))
    ]

    if not video_files:
        print("❌ mynum 폴더에 영상 파일이 없습니다.")
        return

    print(f"🚀 총 {len(video_files)}개 영상 처리 시작")
    print(f"   오른손 우선, 없으면 왼손 | x,y 42차원 | 동작감지 OFF")
    detector = init_detector()
    print(f"   ✅ 모델 로드 완료\n{'='*55}")

    total_ok = total_fail = total_no_hand = 0

    for video_name in sorted(video_files):
        video_path = os.path.join(SRC_VIDEO_DIR, video_name)
        word_name  = os.path.splitext(video_name)[0]
        save_path  = os.path.join(DIST_VIDEO_DIR, f"{word_name}.npy")

        if os.path.exists(save_path):
            print(f"  ⏭️  [{word_name}] 이미 존재, 건너뜀")
            total_ok += 1
            continue

        print(f"  🎬 [{word_name}] 추출 중...")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"    ❌ 영상 열기 실패")
            total_fail += 1
            continue

        frame_count  = 0
        landmark_seq = []
        no_hand_cnt  = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % FRAME_INTERVAL == 0:
                coords, detected = extract_landmarks(frame, detector)
                if detected:
                    landmark_seq.append(coords)
                else:
                    no_hand_cnt += 1

            frame_count += 1

        cap.release()

        if not landmark_seq:
            print(f"    ❌ 손이 한 번도 감지되지 않음")
            total_fail += 1
            continue

        seq = np.array(landmark_seq, dtype=np.float32)

        if len(seq) >= MAX_FRAMES:
            idx = np.linspace(0, len(seq)-1, MAX_FRAMES, dtype=int)
            seq = seq[idx]
        else:
            pad = np.zeros((MAX_FRAMES - len(seq), LANDMARK_DIM), dtype=np.float32)
            seq = np.concatenate([seq, pad], axis=0)

        np.save(save_path, seq)

        hand_ratio = len(landmark_seq) / max(frame_count, 1) * 100
        print(f"    ✅ {len(landmark_seq)}프레임 / 전체 {frame_count}프레임 | 감지율: {hand_ratio:.0f}% → {word_name}.npy")
        if hand_ratio < 50:
            print(f"    ⚠️  감지율 낮음! 조명이나 손 위치 확인 필요")
            total_no_hand += 1

        total_ok += 1

    detector.close()

    print(f"\n{'='*55}")
    print(f"📊 성공: {total_ok} | 실패: {total_fail} | 감지율 낮음: {total_no_hand}")
    print(f"📂 저장 폴더: {DIST_VIDEO_DIR}")


if __name__ == "__main__":
    preprocess_all_videos() 