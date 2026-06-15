import os
import cv2
import numpy as np
import mediapipe as mp

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR       = r"D:\JungPra\pythonpra\signlan"
SRC_VIDEO_DIR  = os.path.join(BASE_DIR, "downloaded_videos")
DIST_VIDEO_DIR = os.path.join(BASE_DIR, "preprocessed_videos")

os.makedirs(DIST_VIDEO_DIR, exist_ok=True)

FRAME_INTERVAL = 3    # 3프레임당 1장 추출
MAX_FRAMES     = 30   # 영상당 최대 프레임 수 (train_signlan.py와 반드시 동일하게)

# 손 관절 1개당 x,y,z = 3개 × 21개 관절 × 양손 2개 = 126
LANDMARK_DIM   = 21 * 3 * 2  # 126


def extract_landmarks(frame, hands_detector):
    """
    프레임 1장에서 양손 관절 좌표 126개를 추출합니다.
    손이 없으면 126개 전부 0으로 채웁니다.
    """
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands_detector.process(rgb)

    left_hand  = np.zeros(21 * 3, dtype=np.float32)  # 63개
    right_hand = np.zeros(21 * 3, dtype=np.float32)  # 63개

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, handedness in zip(
            result.multi_hand_landmarks, result.multi_handedness
        ):
            coords = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                dtype=np.float32
            ).flatten()  # (63,)

            label = handedness.classification[0].label  # 'Left' or 'Right'
            if label == "Left":
                left_hand = coords
            else:
                right_hand = coords

    return np.concatenate([left_hand, right_hand])  # (126,)


def preprocess_all_videos():
    video_files = [
        f for f in os.listdir(SRC_VIDEO_DIR)
        if f.lower().endswith(('.mp4', '.avi', '.mov'))
    ]

    if not video_files:
        print("❌ downloaded_videos 폴더에 영상 파일이 없습니다.")
        return

    print(f"🚀 총 {len(video_files)}개 영상 MediaPipe 관절 추출 시작")
    print(f"   손 관절 126개 (양손 21관절 × x,y,z) → .npy 저장\n{'='*55}")

    # MediaPipe Hands 초기화
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    total_ok   = 0
    total_fail = 0
    total_no_hand = 0

    for video_name in sorted(video_files):
        video_path = os.path.join(SRC_VIDEO_DIR, video_name)
        word_name  = os.path.splitext(video_name)[0]
        save_path  = os.path.join(DIST_VIDEO_DIR, f"{word_name}.npy")

        # 이미 추출된 파일이면 건너뜀
        if os.path.exists(save_path):
            print(f"  ⏭️  [{word_name}] 이미 존재, 건너뜀")
            total_ok += 1
            continue

        print(f"  🎬 [{word_name}] 추출 중...")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"    ❌ 영상을 열 수 없음: {video_name}")
            total_fail += 1
            continue

        frame_count    = 0
        landmark_seq   = []  # 프레임별 관절 좌표 누적
        no_hand_count  = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % FRAME_INTERVAL == 0:
                coords = extract_landmarks(frame, hands)
                landmark_seq.append(coords)

                if np.all(coords == 0):
                    no_hand_count += 1

            frame_count += 1

        cap.release()

        if not landmark_seq:
            print(f"    ❌ 프레임 추출 실패")
            total_fail += 1
            continue

        # ── 프레임 수를 MAX_FRAMES로 통일 ──────────
        seq = np.array(landmark_seq, dtype=np.float32)  # (N, 126)

        if len(seq) >= MAX_FRAMES:
            # 균등 샘플링
            indices = np.linspace(0, len(seq) - 1, MAX_FRAMES, dtype=int)
            seq     = seq[indices]
        else:
            # 제로 패딩
            pad = np.zeros((MAX_FRAMES - len(seq), LANDMARK_DIM), dtype=np.float32)
            seq = np.concatenate([seq, pad], axis=0)

        # (MAX_FRAMES, 126) 형태로 저장
        np.save(save_path, seq)

        hand_ratio = (len(landmark_seq) - no_hand_count) / len(landmark_seq) * 100
        print(f"    ✅ {len(landmark_seq)}프레임 추출 | 손 감지율: {hand_ratio:.0f}% → {word_name}.npy")

        if hand_ratio < 50:
            print(f"    ⚠️  손 감지율이 낮습니다. 영상 품질을 확인하세요.")
            total_no_hand += 1

        total_ok += 1

    hands.close()

    print(f"\n{'='*55}")
    print(f"📊 완료!")
    print(f"   성공: {total_ok}개 | 실패: {total_fail}개 | 손 감지율 낮음: {total_no_hand}개")
    print(f"📂 저장 폴더: {DIST_VIDEO_DIR}")


if __name__ == "__main__":
    preprocess_all_videos()