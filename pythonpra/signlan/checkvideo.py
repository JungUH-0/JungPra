import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from collections import deque
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.core.base_options import BaseOptions
from PIL import ImageFont, ImageDraw, Image

# ──────────────────────────────────────────────
# 설정값 25개 비디오 찢은거 학습 확인용
# ──────────────────────────────────────────────
BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
MODEL_PATH    = os.path.join(BASE_DIR, "selectsign_model.pth")
HAND_MODEL    = os.path.join(BASE_DIR, "hand_landmarker.task")
VIDEO_DIR     = os.path.join(BASE_DIR, "selected_videos")

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]

MAX_FRAMES     = 30
LANDMARK_DIM   = 126
MOTION_THRESH  = 0.01
MOTION_WAIT    = 3


# ──────────────────────────────────────────────
# 한글 폰트
# ──────────────────────────────────────────────
def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_LARGE  = load_font(50)
FONT_MEDIUM = load_font(28)
FONT_SMALL  = load_font(20)

def draw_korean(frame, text, pos, font, color=(255,255,255), shadow=True):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw    = ImageDraw.Draw(img_pil)
    x, y   = pos
    if shadow:
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ──────────────────────────────────────────────
# 모델
# ──────────────────────────────────────────────
class SignLanguageLSTM(nn.Module):
    def __init__(self, num_classes, input_dim=LANDMARK_DIM):
        super().__init__()
        self.input_norm = nn.LayerNorm(input_dim)
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=256,
            num_layers=3,
            batch_first=True,
            dropout=0.3,
            bidirectional=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256 * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x, _ = self.lstm(self.input_norm(x))
        x    = x[:, -1, :]
        return self.classifier(x)


def load_model():
    ckpt    = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    classes = ckpt["classes"]
    model   = SignLanguageLSTM(len(classes))
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"✅ 모델 로드 | {len(classes)}개 클래스 | Val Acc: {ckpt.get('val_acc',0):.1f}%")
    return model, classes


def load_detector():
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL),
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

        h, w = frame.shape[:2]
        for hand_lm in result.hand_landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]
            connections = [
                (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
            ]
            for a, b in connections:
                cv2.line(frame, pts[a], pts[b], (0,255,100), 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 4, (0,200,255), -1, cv2.LINE_AA)

    detected = result.hand_landmarks is not None and len(result.hand_landmarks) > 0
    return np.concatenate([left, right]), detected


# ──────────────────────────────────────────────
# 영상 평가
# ──────────────────────────────────────────────
def evaluate_video(video_path, word, model, classes, detector):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    landmark_seq = []
    prev_coords  = None
    motion_buf   = []
    collecting   = False
    pred_word    = "대기 중..."
    pred_conf    = 0.0
    is_correct   = None
    frame_count  = 0
    status_msg   = "손 움직임 감지 중..."

    while True:
        ret, frame = cap.read()
        if not ret:
            # 영상 끝 → 결과 3초 표시
            if frame is not None:
                for _ in range(int(fps * 3)):
                    display = show_result(frame.copy(), word, pred_word,
                                         pred_conf, is_correct, len(landmark_seq),
                                         status_msg, True)
                    cv2.imshow("Evaluation", display)
                    key = cv2.waitKey(int(1000/fps)) & 0xFF
                    if key == ord('q'): return "quit"
                    if key == ord('n'): return "next"
            break

        frame = cv2.resize(frame, (640, 480))
        coords, detected = extract_landmarks(frame, detector)

        if detected:
            if prev_coords is not None:
                diff = np.linalg.norm(coords - prev_coords)
                motion_buf.append(diff > MOTION_THRESH)

                # 동작 감지 시작
                if not collecting and len(motion_buf) >= MOTION_WAIT:
                    if sum(motion_buf[-MOTION_WAIT:]) >= MOTION_WAIT - 1:
                        collecting   = True
                        status_msg   = "🔴 수집 중..."
                        landmark_seq = []

            if collecting:
                landmark_seq.append(coords)

                # 30프레임 채우면 즉시 예측
                if len(landmark_seq) == MAX_FRAMES:
                    seq = torch.tensor(
                        np.array(landmark_seq)[np.newaxis], dtype=torch.float32)
                    with torch.no_grad():
                        probs     = torch.softmax(model(seq), dim=1)[0]
                        idx       = probs.argmax().item()
                        pred_conf = float(probs[idx])
                        pred_word = classes[idx]
                        is_correct = (pred_word == word)
                    status_msg  = "✅ 예측 완료"
                    collecting  = False

            prev_coords = coords.copy()

        else:
            if collecting and len(landmark_seq) > 5:
                # 손 사라지면 지금까지 모은 걸로 예측
                seq_arr = np.array(landmark_seq, dtype=np.float32)
                if len(seq_arr) >= MAX_FRAMES:
                    idx     = np.linspace(0, len(seq_arr)-1, MAX_FRAMES, dtype=int)
                    seq_arr = seq_arr[idx]
                else:
                    pad     = np.zeros((MAX_FRAMES-len(seq_arr), LANDMARK_DIM), np.float32)
                    seq_arr = np.concatenate([seq_arr, pad])

                seq = torch.tensor(seq_arr[np.newaxis], dtype=torch.float32)
                with torch.no_grad():
                    probs     = torch.softmax(model(seq), dim=1)[0]
                    idx       = probs.argmax().item()
                    pred_conf = float(probs[idx])
                    pred_word = classes[idx]
                    is_correct = (pred_word == word)
                status_msg = "✅ 예측 완료"
                collecting = False

        frame = show_result(frame, word, pred_word, pred_conf,
                            is_correct, len(landmark_seq), status_msg, False)
        cv2.imshow("Evaluation", frame)

        key = cv2.waitKey(int(1000/fps)) & 0xFF
        if key == ord('q'): return "quit"
        if key == ord('n'): return "next"
        if key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            landmark_seq = []
            prev_coords  = None
            motion_buf   = []
            collecting   = False
            pred_word    = "대기 중..."
            pred_conf    = 0.0
            is_correct   = None
            status_msg   = "손 움직임 감지 중..."

        frame_count += 1

    cap.release()
    return "next"


def show_result(frame, word, pred_word, pred_conf, is_correct,
                frame_cnt, status_msg, final):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w,70), (20,20,20), -1)
    cv2.rectangle(overlay, (0,h-160), (w,h), (20,20,20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # 정답
    frame = draw_korean(frame, f"정답: {word}", (10, 5), FONT_MEDIUM, (255,200,0))

    # 상태
    frame = draw_korean(frame, status_msg, (10, h-165), FONT_SMALL, (150,150,150), shadow=False)

    # 수집 진행바
    prog = min(frame_cnt / MAX_FRAMES, 1.0)
    cv2.rectangle(frame, (10, h-148), (w-10, h-135), (50,50,50), -1)
    cv2.rectangle(frame, (10, h-148), (10+int((w-20)*prog), h-135), (0,180,100), -1)

    # 예측 결과
    if is_correct is None:
        frame = draw_korean(frame, pred_word, (10, h-125), FONT_MEDIUM, (150,150,150))
    elif is_correct:
        frame = draw_korean(frame, f"예측: {pred_word}  ✓ 정답!", (10, h-125),
                            FONT_LARGE, (0,255,100))
    else:
        frame = draw_korean(frame, f"예측: {pred_word}  ✗ 오답", (10, h-125),
                            FONT_LARGE, (0,80,255))

    # 신뢰도 바
    if pred_conf > 0:
        cv2.rectangle(frame, (10, h-62), (w-10, h-45), (50,50,50), -1)
        color = (0,200,100) if is_correct else (0,80,255)
        cv2.rectangle(frame, (10, h-62), (10+int((w-20)*pred_conf), h-45), color, -1)
        frame = draw_korean(frame, f"신뢰도: {pred_conf*100:.1f}%",
                            (10, h-75), FONT_SMALL, (200,200,200), shadow=False)

    frame = draw_korean(frame, "N: 다음  R: 다시보기  Q: 종료",
                        (10, h-25), FONT_SMALL, (120,120,120), shadow=False)

    if final:
        frame = draw_korean(frame, "[ 영상 종료 ]",
                            (w//2-80, h//2-30), FONT_MEDIUM, (200,200,0))
    return frame


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def run():
    print("🎬 학습 영상 평가 시작!")
    model, classes = load_model()
    detector       = load_detector()

    video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')])
    if not video_files:
        print("❌ selected_videos 폴더에 영상이 없습니다.")
        return

    correct = 0
    total   = 0

    for i, video_file in enumerate(video_files):
        word       = os.path.splitext(video_file)[0]
        video_path = os.path.join(VIDEO_DIR, video_file)
        print(f"\n[{i+1}/{len(video_files)}] {word}")

        result = evaluate_video(video_path, word, model, classes, detector)
        if result == "quit":
            break

    cv2.destroyAllWindows()
    detector.close()
    print("\n👋 평가 종료!")


if __name__ == "__main__":
    run()