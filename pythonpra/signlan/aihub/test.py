import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from collections import deque, Counter
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.core.base_options import BaseOptions
from PIL import ImageFont, ImageDraw, Image

# ──────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────
BASE_DIR     = r"D:\JungPra\pythonpra\signlan"
MODEL_PATH   = os.path.join(BASE_DIR, "aihub_model.pth")
HAND_MODEL   = os.path.join(BASE_DIR, "hand_landmarker.task")

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]

MAX_FRAMES   = 30
LANDMARK_DIM = 84    # x,y × 21관절 × 2손
CONF_THRESH  = 0.5
STABLE_COUNT = 5


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
# 모델 구조 (trainhandle_torch.py 와 동일)
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
            nn.Linear(256 * 2, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x, _ = self.lstm(self.input_norm(x))
        x    = x[:, -1, :]
        return self.classifier(x)


# ──────────────────────────────────────────────
# 모델 + MediaPipe 로드
# ──────────────────────────────────────────────
def load_model():
    ckpt        = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    classes     = ckpt["classes"]
    num_classes = len(classes)
    model       = SignLanguageLSTM(num_classes)
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"✅ 모델 로드 완료 | {num_classes}개 클래스 | Val Acc: {ckpt.get('val_acc',0):.1f}%")
    print(f"   단어 목록: {classes}")
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


# ──────────────────────────────────────────────
# 관절 좌표 추출 (x,y만 사용 → 84개)
# ──────────────────────────────────────────────
def extract_landmarks(frame, detector):
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    left  = np.zeros(21 * 2, dtype=np.float32)  # x,y × 21 = 42
    right = np.zeros(21 * 2, dtype=np.float32)  # x,y × 21 = 42

    if result.hand_landmarks and result.handedness:
        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            # x,y만 추출 (z 제외)
            coords = np.array(
                [[lm.x, lm.y] for lm in hand_lm],
                dtype=np.float32
            ).flatten()  # 42개

            if handedness[0].category_name == "Left":
                left = coords
            else:
                right = coords

        # 관절 화면에 그리기
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
    return np.concatenate([left, right]), detected  # 84개


# ──────────────────────────────────────────────
# 진행바
# ──────────────────────────────────────────────
def draw_progress_bar(frame, progress, x, y, w, h):
    cv2.rectangle(frame, (x, y), (x+w, y+h), (50,50,50), -1)
    fill_w = int(w * progress)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x+fill_w, y+h), (0,200,100), -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (100,100,100), 1)


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def run():
    print("🚀 실시간 수어 인식 시작!")
    print("   종료: Q | 초기화: R\n")

    model, classes = load_model()
    detector       = load_detector()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame_seq    = deque(maxlen=MAX_FRAMES)
    result_buf   = deque(maxlen=STABLE_COUNT)
    current_word = ""
    current_conf = 0.0
    history      = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1280, 720))
        h, w  = frame.shape[:2]

        coords, hand_detected = extract_landmarks(frame, detector)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w,70), (20,20,20), -1)
        cv2.rectangle(overlay, (0,h-140), (w,h), (20,20,20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        if hand_detected:
            frame_seq.append(coords)

            if len(frame_seq) == MAX_FRAMES:
                seq = torch.tensor(np.array(frame_seq)[np.newaxis], dtype=torch.float32)
                with torch.no_grad():
                    probs     = torch.softmax(model(seq), dim=1)[0]
                    idx       = probs.argmax().item()
                    conf      = float(probs[idx])

                result_buf.append(classes[idx] if conf >= CONF_THRESH else "")
                counts   = Counter(result_buf)
                top, cnt = counts.most_common(1)[0]

                if top and cnt >= STABLE_COUNT // 2 + 1:
                    if top != current_word:
                        current_word = top
                        current_conf = conf
                        history.insert(0, top)
                        history = history[:5]
                    else:
                        current_conf = conf

            progress = len(frame_seq) / MAX_FRAMES
            draw_progress_bar(frame, progress, 10, h-128, w-20, 14)
            frame = draw_korean(frame, f"수집 중: {len(frame_seq)}/{MAX_FRAMES}",
                                (10, h-135), FONT_SMALL, (150,150,150), shadow=False)
        else:
            frame_seq.clear()
            frame = draw_korean(frame, "손을 카메라에 보여주세요",
                                (10, h-110), FONT_MEDIUM, (100,100,255))

        frame = draw_korean(frame, "수어 인식", (10, 10), FONT_MEDIUM, (255,200,0))

        if current_word:
            text_w = FONT_LARGE.getbbox(current_word)[2]
            text_x = max(10, (w - text_w) // 2)
            frame  = draw_korean(frame, current_word, (text_x, h-100), FONT_LARGE, (0,255,150))
            draw_progress_bar(frame, current_conf, 10, h-30, w-20, 18)
            frame  = draw_korean(frame, f"신뢰도: {current_conf*100:.1f}%",
                                 (10, h-52), FONT_SMALL, (200,200,200), shadow=False)

        if history:
            frame = draw_korean(frame, "최근 인식:", (w-220, 10), FONT_SMALL, (150,150,150), shadow=False)
        for i, word in enumerate(history[:5]):
            alpha = max(80, 220 - i*35)
            frame = draw_korean(frame, word, (w-220, 38+i*32),
                                FONT_SMALL, (alpha,alpha,alpha), shadow=False)

        cv2.imshow("Sign Language  |  Q: 종료  R: 초기화", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            frame_seq.clear()
            result_buf.clear()
            current_word = ""
            current_conf = 0.0
            print("🔄 초기화!")

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    print("👋 종료!")


if __name__ == "__main__":
    run()