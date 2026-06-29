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
BASE_DIR      = r"D:\JungPra\pythonpra\signlan"
NUMBER_MODEL  = os.path.join(BASE_DIR, "newnumber_model_signbridge.pth")
KOR_MODEL     = os.path.join(BASE_DIR, "kor_model_signbridge.pth")
HAND_MODEL    = os.path.join(BASE_DIR, "hand_landmarker.task")

FONT_PATHS = [
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
]

MAX_FRAMES   = 30
FEATURE_DIM  = 55
CONF_THRESH  = 0.5
STABLE_COUNT = 5

CONSONANTS = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
VOWELS     = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅕ','ㅖ','ㅗ','ㅛ','ㅜ','ㅠ','ㅡ','ㅣ']

MODES      = ["숫자", "자음", "모음"]  # M키로 순환
MODE_COLOR = {
    "숫자": (0,200,255),
    "자음": (0,255,150),
    "모음": (255,150,50),
}

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


# ──────────────────────────────────────────────
# 폰트
# ──────────────────────────────────────────────
def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

FONT_LARGE  = load_font(100)
FONT_MEDIUM = load_font(32)
FONT_SMALL  = load_font(22)

def draw_korean(frame, text, pos, font, color=(255,255,255), shadow=True):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw    = ImageDraw.Draw(img_pil)
    x, y   = pos
    if shadow:
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ──────────────────────────────────────────────
# Vector+Angle 변환
# ──────────────────────────────────────────────
def extract_vector_angle(coords_42):
    points       = coords_42.reshape(21, 2)
    bone_vectors = np.array(
        [points[child] - points[parent] for parent, child in BONE_CONNECTIONS],
        dtype=np.float32,
    )
    lengths      = np.linalg.norm(bone_vectors, axis=1, keepdims=True)
    unit_vectors = bone_vectors / np.maximum(lengths, 1e-6)
    angles = []
    for fi, si in ANGLE_PAIRS:
        dot = np.clip(np.dot(unit_vectors[fi], unit_vectors[si]), -1.0, 1.0)
        angles.append(np.arccos(dot) / np.pi)
    return np.concatenate([unit_vectors.flatten(), np.array(angles, dtype=np.float32)])


# ──────────────────────────────────────────────
# 모델
# ──────────────────────────────────────────────
class SignLSTM(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.lstm1 = nn.LSTM(input_dim, 128, batch_first=True)
        self.drop1 = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(128, 64, batch_first=True)
        self.drop2 = nn.Dropout(0.3)
        self.fc1   = nn.Linear(64, 64)
        self.relu  = nn.ReLU()
        self.fc2   = nn.Linear(64, num_classes)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x     = self.drop1(x)
        x, _ = self.lstm2(x)
        x     = self.drop2(x[:, -1, :])
        x     = self.relu(self.fc1(x))
        return self.fc2(x)


def load_model(path):
    ckpt    = torch.load(path, map_location="cpu", weights_only=False)
    classes = ckpt["le_classes"]
    model   = SignLSTM(FEATURE_DIM, len(classes))
    model.load_state_dict(ckpt["model"])
    model.eval()
    print(f"✅ {os.path.basename(path)} | 클래스: {len(classes)}개 | Val: {ckpt.get('val_acc',0):.1f}%")
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
# 관절 추출
# ──────────────────────────────────────────────
def extract_landmarks(frame, detector):
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    coords_42 = np.zeros(42, dtype=np.float32)
    detected  = False

    if result.hand_landmarks and result.handedness:
        right_lm = left_lm = None
        for hand_lm, handedness in zip(result.hand_landmarks, result.handedness):
            if handedness[0].category_name == "Right":
                right_lm = hand_lm
            else:
                left_lm = hand_lm

        target = right_lm if right_lm is not None else left_lm
        if target is not None:
            coords_42 = np.array([[lm.x, lm.y] for lm in target], dtype=np.float32).flatten()
            detected  = True

        h, w = frame.shape[:2]
        for hand_lm in result.hand_landmarks:
            pts = [(int(lm.x*w), int(lm.y*h)) for lm in hand_lm]
            connections = [
                (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)
            ]
            for a, b in connections:
                cv2.line(frame, pts[a], pts[b], (0,255,100), 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 5, (0,200,255), -1, cv2.LINE_AA)

    return extract_vector_angle(coords_42), detected


def draw_progress_bar(frame, progress, x, y, w, h, color=(0,200,100)):
    cv2.rectangle(frame, (x,y), (x+w,y+h), (50,50,50), -1)
    fw = int(w * progress)
    if fw > 0:
        cv2.rectangle(frame, (x,y), (x+fw,y+h), color, -1)
    cv2.rectangle(frame, (x,y), (x+w,y+h), (100,100,100), 1)


def predict(model, classes, seq_tensor, filter_list=None):
    """예측 + 특정 클래스만 필터링"""
    with torch.no_grad():
        probs = torch.softmax(model(seq_tensor), dim=1)[0]

    if filter_list:
        # 해당 클래스만 추출 후 재정규화
        idxs      = [classes.index(c) for c in filter_list if c in classes]
        filtered  = probs[idxs]
        total     = filtered.sum()
        if total > 0:
            filtered = filtered / total
        return filtered, filter_list
    return probs, classes


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def run():
    print("🚀 SignBridge 통합 테스트")
    print("   M: 모드전환 (숫자→자음→모음→숫자)")
    print("   R: 초기화  Q: 종료\n")

    number_model, number_classes = load_model(NUMBER_MODEL)
    kor_model,    kor_classes    = load_model(KOR_MODEL)
    detector = load_detector()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame_seq    = deque(maxlen=MAX_FRAMES)
    result_buf   = deque(maxlen=STABLE_COUNT)
    current_sign = ""
    current_conf = 0.0
    mode_idx     = 0  # 0=숫자, 1=자음, 2=모음
    history      = []
    cur_probs    = {}

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1280, 720))
        h, w  = frame.shape[:2]
        mode  = MODES[mode_idx]

        features, hand_detected = extract_landmarks(frame, detector)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w,65), (20,20,20), -1)
        cv2.rectangle(overlay, (0,h-160), (w,h), (20,20,20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        if hand_detected:
            frame_seq.append(features)

            if len(frame_seq) >= 15:
                seq = torch.tensor(np.array(frame_seq)[np.newaxis], dtype=torch.float32)

                if mode == "숫자":
                    probs, classes = predict(number_model, number_classes, seq)
                elif mode == "자음":
                    probs, classes = predict(kor_model, kor_classes, seq, CONSONANTS)
                else:  # 모음
                    probs, classes = predict(kor_model, kor_classes, seq, VOWELS)

                idx  = probs.argmax().item()
                conf = float(probs[idx])
                cur_probs = {c: float(probs[i]) for i, c in enumerate(classes)}

                result_buf.append(classes[idx] if conf >= CONF_THRESH else "")
                counts   = Counter(result_buf)
                top, cnt = counts.most_common(1)[0]

                if top and cnt >= STABLE_COUNT // 2 + 1:
                    if top != current_sign:
                        current_sign = top
                        current_conf = conf
                        history.insert(0, f"[{mode[0]}]{top}")
                        history = history[:8]
                    else:
                        current_conf = conf

            progress = len(frame_seq) / MAX_FRAMES
            draw_progress_bar(frame, progress, 10, h-148, w//2, 14)
            frame = draw_korean(frame, f"수집: {len(frame_seq)}/{MAX_FRAMES}",
                                (10, h-155), FONT_SMALL, (150,150,150), shadow=False)
        else:
            frame_seq.clear()
            result_buf.clear()
            current_sign = ""
            current_conf = 0.0
            frame = draw_korean(frame, "손을 보여주세요",
                                (10, h-120), FONT_MEDIUM, (100,100,255))

        # ── 상단 모드 표시 ──
        mcolor = MODE_COLOR[mode]
        frame  = draw_korean(frame, f"◆ 모드: {mode}  (M: 전환)",
                             (10, 8), FONT_MEDIUM, mcolor)
        frame  = draw_korean(frame, "Q: 종료  R: 초기화",
                             (w-250, 8), FONT_SMALL, (100,100,100), shadow=False)

        # ── 인식 결과 ──
        if current_sign:
            frame = draw_korean(frame, current_sign,
                                (w//2 - 60, h//2 - 130), FONT_LARGE, (0,255,150))
            draw_progress_bar(frame, current_conf, 10, h-50, w//2, 20, color=mcolor)
            frame = draw_korean(frame, f"신뢰도: {current_conf*100:.1f}%",
                                (10, h-68), FONT_SMALL, (200,200,200), shadow=False)

        # ── 인식 기록 ──
        frame = draw_korean(frame, "최근:", (10, 65), FONT_SMALL, (150,150,150), shadow=False)
        for i, s in enumerate(history[:6]):
            alpha = max(80, 220-i*30)
            frame = draw_korean(frame, s, (75+i*90, 65),
                                FONT_SMALL, (alpha,alpha,alpha), shadow=False)

        # ── 확률 바 ──
        bar_x = w - 260
        frame = draw_korean(frame, f"{mode} 확률:", (bar_x, 65),
                            FONT_SMALL, (150,150,150), shadow=False)

        show_classes = sorted(cur_probs.keys()) if cur_probs else []
        for i, c in enumerate(show_classes[:14]):
            prob  = cur_probs.get(c, 0.0)
            bar_w = int(200 * prob)
            color = mcolor if c == current_sign else (80,80,160)
            cv2.rectangle(frame, (bar_x, 88+i*28), (bar_x+bar_w, 88+i*28+20), color, -1)
            cv2.rectangle(frame, (bar_x, 88+i*28), (bar_x+200, 88+i*28+20), (60,60,60), 1)
            frame = draw_korean(frame, f"{c}:{prob*100:.0f}%",
                                (bar_x+3, 88+i*28), FONT_SMALL, (255,255,255), shadow=False)

        cv2.imshow("SignBridge  |  M: 모드전환 (숫자→자음→모음)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            frame_seq.clear()
            result_buf.clear()
            current_sign = ""
            current_conf = 0.0
            history      = []
            cur_probs    = {}
            print("🔄 초기화!")
        elif key == ord('m'):
            mode_idx = (mode_idx + 1) % 3
            frame_seq.clear()
            result_buf.clear()
            current_sign = ""
            cur_probs    = {}
            print(f"🔄 모드 전환: {MODES[mode_idx]}")

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    print("👋 종료!")


if __name__ == "__main__":
    run()