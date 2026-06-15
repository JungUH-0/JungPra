# import os
# import cv2
# import numpy as np

# # 경로 설정
# BASE_DIR = r"D:\JungPra\pythonpra\signlan"
# SRC_VIDEO_DIR = os.path.join(BASE_DIR, "downloaded_videos")
# DIST_VIDEO_DIR = os.path.join(BASE_DIR, "preprocessed_videos") # 프레임들이 저장될 곳

# os.makedirs(DIST_VIDEO_DIR, exist_ok=True)

# TARGET_SIZE = (224, 224)
# FRAME_INTERVAL = 3  # 모든 프레임을 다 저장하면 용량이 너무 크니, 3프레임당 1장씩 골라냅니다.

# def preprocess_all_videos():
#     video_files = [f for f in os.listdir(SRC_VIDEO_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    
#     if not video_files:
#         print("ℹ️ 원본 폴더(downloaded_videos)에 비디오 파일이 없습니다.")
#         return

#     print(f"🚀 총 {len(video_files)}개의 동영상 프레임 추출을 시작합니다...")

#     for video_name in video_files:
#         video_path = os.path.join(SRC_VIDEO_DIR, video_name)
#         word_name = os.path.splitext(video_name)[0] # 확장자 뗀 단어 이름 (예: 두려움)
        
#         # 단어별로 프레임들을 모아둘 개별 폴더 생성
#         word_output_dir = os.path.join(DIST_VIDEO_DIR, word_name)
#         os.makedirs(word_output_dir, exist_ok=True)

#         print(f"  🎬 '{video_name}' 영상 분석 중...")

#         # 🌟 한글 경로 동영상을 안전하게 읽기 위해 cv2.VideoCapture에 직접 경로를 전달하는 대신 
#         # 환경에 따라 발생할 수 있는 오류를 방지하기 위해 예외 처리를 강화합니다.
#         cap = cv2.VideoCapture(video_path)
        
#         if not cap.isOpened():
#             print(f"    ❌ 동영상을 열 수 없습니다: {video_name}")
#             continue

#         frame_count = 0
#         saved_count = 0

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break # 영상이 끝나면 탈출

#             # 지정한 인터벌(3프레임)마다 한 장씩 가공
#             if frame_count % FRAME_INTERVAL == 0:
#                 # 1. 크기 조절 (224x224)
#                 resized_frame = cv2.resize(frame, TARGET_SIZE, interpolation=cv2.INTER_AREA)

#                 # 2. 흑백 변환
#                 gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

#                 # 3. 이미지 파일로 저장할 이름 조립 (예: 두려움_frame_001.jpg)
#                 frame_filename = f"{word_name}_frame_{saved_count:03d}.jpg"
#                 frame_save_path = os.path.join(word_output_dir, frame_filename)

#                 # 4. 파이썬 엔진을 이용한 안전한 한글 경로 저장
#                 _, img_encoded = cv2.imencode('.jpg', gray_frame)
#                 with open(frame_save_path, 'wb') as f:
#                     f.write(img_encoded.tobytes())

#                 saved_count += 1

#             frame_count += 1

#         cap.release()
#         print(f"    ✅ 프레임 추출 완료! 총 {saved_count}장의 이미지 조각으로 쪼갰습니다.")

#     print("\n🎉 모든 비디오 전처리 파이프라인이 완료되었습니다!")
#     print(f"📂 결과 확인 폴더: {DIST_VIDEO_DIR}")

# if __name__ == "__main__":
#     preprocess_all_videos()

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
# SRC_VIDEO_DIR  = os.path.join(BASE_DIR, "selected_videos")
# DIST_VIDEO_DIR = os.path.join(BASE_DIR, "selectedpreprocessed_videos")
# MODEL_PATH     = os.path.join(BASE_DIR, "hand_landmarker.task")  # ← 여기에 모델 파일

# os.makedirs(DIST_VIDEO_DIR, exist_ok=True)

# FRAME_INTERVAL = 1
# MAX_FRAMES     = 30
# LANDMARK_DIM   = 126   # 양손 21관절 × x,y,z × 2


# def init_detector():
#     if not os.path.exists(MODEL_PATH):
#         raise FileNotFoundError(
#             f"❌ 모델 파일이 없습니다: {MODEL_PATH}\n"
#             f"   브라우저에서 아래 링크로 다운로드 후\n"
#             f"   D:\\JungPra\\pythonpra\\signlan\\ 폴더에 넣으세요:\n"
#             f"   https://storage.googleapis.com/mediapipe-models/"
#             f"hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
#         )

#     options = HandLandmarkerOptions(
#         base_options=BaseOptions(model_asset_path=MODEL_PATH),
#         running_mode=VisionTaskRunningMode.IMAGE,
#         num_hands=2,
#         min_hand_detection_confidence=0.5,
#         min_hand_presence_confidence=0.5,
#     )
#     return HandLandmarker.create_from_options(options)


# def extract_landmarks(frame, detector):
#     """프레임 1장에서 양손 관절 126개 좌표 추출"""
#     rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
#     result   = detector.detect(mp_image)

#     left  = np.zeros(21 * 3, dtype=np.float32)
#     right = np.zeros(21 * 3, dtype=np.float32)

#     if result.hand_landmarks and result.handedness:
#         for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
#             coords = np.array(
#                 [[lm.x, lm.y, lm.z] for lm in hand_lm],
#                 dtype=np.float32
#             ).flatten()
#             if handedness[0].category_name == "Left":
#                 left = coords
#             else:
#                 right = coords

#     return np.concatenate([left, right])  # (126,)


# def preprocess_all_videos():
#     video_files = [
#         f for f in os.listdir(SRC_VIDEO_DIR)
#         if f.lower().endswith(('.mp4', '.avi', '.mov'))
#     ]

#     if not video_files:
#         print("❌ downloaded_videos 폴더에 영상 파일이 없습니다.")
#         return

#     print(f"🚀 총 {len(video_files)}개 영상 MediaPipe 관절 추출 시작")
#     detector = init_detector()
#     print(f"   ✅ 모델 로드 완료: {MODEL_PATH}")
#     print(f"{'='*55}")

#     total_ok = total_fail = total_no_hand = 0

#     for video_name in sorted(video_files):
#         video_path = os.path.join(SRC_VIDEO_DIR, video_name)
#         word_name  = os.path.splitext(video_name)[0]
#         save_path  = os.path.join(DIST_VIDEO_DIR, f"{word_name}.npy")

#         if os.path.exists(save_path):
#             print(f"  ⏭️  [{word_name}] 이미 존재, 건너뜀")
#             total_ok += 1
#             continue

#         print(f"  🎬 [{word_name}] 추출 중...")

#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             print(f"    ❌ 영상 열기 실패: {video_name}")
#             total_fail += 1
#             continue

#         frame_count  = 0
#         landmark_seq = []
#         no_hand_cnt  = 0

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             if frame_count % FRAME_INTERVAL == 0:
#                 coords = extract_landmarks(frame, detector)
#                 landmark_seq.append(coords)
#                 if np.all(coords == 0):
#                     no_hand_cnt += 1

#             frame_count += 1

#         cap.release()

#         if not landmark_seq:
#             print(f"    ❌ 프레임 없음")
#             total_fail += 1
#             continue

#         seq = np.array(landmark_seq, dtype=np.float32)

#         # MAX_FRAMES로 통일
#         if len(seq) >= MAX_FRAMES:
#             idx = np.linspace(0, len(seq) - 1, MAX_FRAMES, dtype=int)
#             seq = seq[idx]
#         else:
#             pad = np.zeros((MAX_FRAMES - len(seq), LANDMARK_DIM), dtype=np.float32)
#             seq = np.concatenate([seq, pad], axis=0)

#         np.save(save_path, seq)

#         hand_ratio = (len(landmark_seq) - no_hand_cnt) / len(landmark_seq) * 100
#         print(f"    ✅ 손 감지율: {hand_ratio:.0f}% → {word_name}.npy")
#         if hand_ratio < 50:
#             print(f"    ⚠️  손 감지율 낮음! 영상 품질 확인 필요")
#             total_no_hand += 1

#         total_ok += 1

#     detector.close()

#     print(f"\n{'='*55}")
#     print(f"📊 성공: {total_ok} | 실패: {total_fail} | 감지율 낮음: {total_no_hand}")
#     print(f"📂 저장 폴더: {DIST_VIDEO_DIR}")


# if __name__ == "__main__":
#     preprocess_all_videos()

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.core.base_options import BaseOptions

# ──────────────────────────────────────────────
# 설정값 비디오 프레임단위로 찢기
# ──────────────────────────────────────────────
BASE_DIR       = r"D:\JungPra\pythonpra\signlan"
SRC_VIDEO_DIR  = os.path.join(BASE_DIR, "mynum")
DIST_VIDEO_DIR = os.path.join(BASE_DIR, "mynum_preprocessed")
MODEL_PATH     = os.path.join(BASE_DIR, "hand_landmarker.task")

os.makedirs(DIST_VIDEO_DIR, exist_ok=True)

FRAME_INTERVAL  = 1      # 모든 프레임 사용
MAX_FRAMES      = 30
LANDMARK_DIM    = 126
MOTION_THRESH   = 0.01   # 움직임 감지 임계값 (이 이상 움직여야 수집 시작)
MOTION_WAIT     = 3      # 연속 N프레임 움직임 감지 후 수집 시작


def init_detector():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"❌ 모델 파일 없음: {MODEL_PATH}")
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
    )
    return HandLandmarker.create_from_options(options)


def extract_landmarks(frame, detector):
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    left  = np.zeros(21 * 3, dtype=np.float32)
    right = np.zeros(21 * 3, dtype=np.float32)

    if result.hand_landmarks and result.handedness:
        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            coords = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_lm],
                dtype=np.float32
            ).flatten()
            if handedness[0].category_name == "Left":
                left = coords
            else:
                right = coords

    detected = result.hand_landmarks is not None and len(result.hand_landmarks) > 0
    return np.concatenate([left, right]), detected


def preprocess_all_videos():
    video_files = [
        f for f in os.listdir(SRC_VIDEO_DIR)
        if f.lower().endswith(('.mp4', '.avi', '.mov'))
    ]

    if not video_files:
        print("❌ selected_videos 폴더에 영상이 없습니다.")
        return

    print(f"🚀 총 {len(video_files)}개 영상 처리 시작")
    print(f"   동작 감지 모드 ON (임계값: {MOTION_THRESH})")
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

        frame_count    = 0
        all_coords     = []   # 전체 프레임 좌표
        prev_coords    = None
        motion_buf     = []   # 움직임 감지 버퍼
        collecting     = False
        landmark_seq   = []
        no_hand_cnt    = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % FRAME_INTERVAL == 0:
                coords, detected = extract_landmarks(frame, detector)

                if detected:
                    all_coords.append(coords)

                    if prev_coords is not None:
                        # 이전 프레임과 현재 프레임의 움직임 계산
                        diff = np.linalg.norm(coords - prev_coords)
                        motion_buf.append(diff > MOTION_THRESH)

                        # 연속 N프레임 움직임 감지되면 수집 시작
                        if not collecting and len(motion_buf) >= MOTION_WAIT:
                            if sum(motion_buf[-MOTION_WAIT:]) >= MOTION_WAIT - 1:
                                collecting = True
                                print(f"    🖐️  동작 감지! 수집 시작 (frame {frame_count})")

                    if collecting:
                        landmark_seq.append(coords)
                        if np.all(coords == 0):
                            no_hand_cnt += 1

                    prev_coords = coords.copy()
                else:
                    # 손 미감지 → 수집 중이면 종료
                    if collecting and len(landmark_seq) > 5:
                        print(f"    ✋ 손 사라짐 → 수집 종료 (frame {frame_count})")
                        break

            frame_count += 1

        cap.release()

        # 동작 감지로 수집된 게 없으면 전체 프레임 사용
        if len(landmark_seq) < 5:
            print(f"    ⚠️  동작 감지 실패 → 전체 프레임으로 대체")
            landmark_seq = all_coords

        if not landmark_seq:
            print(f"    ❌ 프레임 없음")
            total_fail += 1
            continue

        seq = np.array(landmark_seq, dtype=np.float32)

        # MAX_FRAMES로 통일
        if len(seq) >= MAX_FRAMES:
            idx = np.linspace(0, len(seq) - 1, MAX_FRAMES, dtype=int)
            seq = seq[idx]
        else:
            pad = np.zeros((MAX_FRAMES - len(seq), LANDMARK_DIM), dtype=np.float32)
            seq = np.concatenate([seq, pad], axis=0)

        np.save(save_path, seq)

        hand_ratio = (len(landmark_seq) - no_hand_cnt) / max(len(landmark_seq), 1) * 100
        print(f"    ✅ {len(landmark_seq)}프레임 수집 | 손 감지율: {hand_ratio:.0f}% → {word_name}.npy")
        if hand_ratio < 50:
            print(f"    ⚠️  손 감지율 낮음!")
            total_no_hand += 1

        total_ok += 1

    detector.close()
    print(f"\n{'='*55}")
    print(f"📊 성공: {total_ok} | 실패: {total_fail} | 감지율 낮음: {total_no_hand}")
    print(f"📂 저장 폴더: {DIST_VIDEO_DIR}")


if __name__ == "__main__":
    preprocess_all_videos()